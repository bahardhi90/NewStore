/**
 * A tiny in-memory implementation of the backend API (contract/openapi.yaml).
 * Runs on the Next.js server only. State lives in memory and resets on restart.
 * OTP code in mock mode is always 12345.
 */
import "server-only";

import type { Address, Cart, CartItem, Order, OrderItem, ProductListItem, User, Variant } from "@/types/api";

import {
  banners,
  calcFinalPrice,
  categories,
  collections,
  paymentMethods,
  products,
  shippingMethods,
  siteSettings,
  stores,
  type MockProduct,
} from "./data";
import { pages } from "./pages";

export type MockResponse = { status: number; data: unknown };

type CartLine = { id: number; variant_id: number; quantity: number };
type MockPayment = { authority: string; order_id: number; status: "initiated" | "success" | "failed" | "cancelled"; ref_id: string | null };

type MockDb = {
  users: User[];
  carts: Map<number, CartLine[]>;
  addresses: Address[];
  orders: (Order & { user_id: number })[];
  payments: MockPayment[];
  stock: Map<number, number>;
  seq: number;
};

const g = globalThis as unknown as { __storeMockDb?: MockDb };
const db: MockDb =
  g.__storeMockDb ??
  (g.__storeMockDb = {
    users: [],
    carts: new Map(),
    addresses: [],
    orders: [],
    payments: [],
    stock: new Map(products.flatMap((p) => p.variants.map((v) => [v.id, v.stock] as const))),
    seq: 1000,
  });

const MOCK_CODE = "12345";
const PAGE_SIZE = 12;
const MAX_QTY = 10;
const fa = (n: number | string) => String(n).replace(/\d/g, (d) => "۰۱۲۳۴۵۶۷۸۹"[Number(d)]);

const ok = (data: unknown, status = 200): MockResponse => ({ status, data });
const err = (status: number, code: string, detail: string, errors: Record<string, string[]> = {}): MockResponse => ({
  status,
  data: { detail, code, errors },
});
const notFound = () => err(404, "not_found", "یافت نشد.");
const unauthorized = () => err(401, "not_authenticated", "لطفاً وارد حساب کاربری شوید.");

function nextId(): number {
  db.seq += 1;
  return db.seq;
}

function variantWithStock(v: Variant): Variant {
  return { ...v, stock: db.stock.get(v.id) ?? 0 };
}

function findVariant(variantId: number): { product: MockProduct; variant: Variant } | null {
  for (const product of products) {
    const variant = product.variants.find((v) => v.id === variantId);
    if (variant) return { product, variant: variantWithStock(variant) };
  }
  return null;
}

function toListItem(p: MockProduct): ProductListItem {
  return {
    id: p.id,
    title: p.title,
    slug: p.slug,
    image: p.image,
    hover_image: p.hover_image,
    base_price: p.base_price,
    discount_percent: p.discount_percent,
    final_price: p.final_price,
  };
}

function csv(value: string | null): string[] {
  return (value ?? "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function filterProducts(q: URLSearchParams, { scopeOnly = false } = {}): MockProduct[] {
  let list = products.filter((p) => p.is_active);
  const category = q.get("category");
  if (category) list = list.filter((p) => p.category.slug === category);
  const collection = q.get("collection");
  if (collection) list = list.filter((p) => p.collections.some((c) => c.slug === collection));
  if (q.get("on_sale") === "true") list = list.filter((p) => p.discount_percent > 0);
  const search = q.get("search")?.trim();
  if (search) list = list.filter((p) => p.title.includes(search) || p.description.includes(search));
  if (scopeOnly) return list;
  const sizes = csv(q.get("size"));
  if (sizes.length) list = list.filter((p) => p.variants.some((v) => sizes.includes(v.size) && (db.stock.get(v.id) ?? 0) > 0));
  const colors = csv(q.get("color"));
  if (colors.length) list = list.filter((p) => p.variants.some((v) => colors.includes(v.color) && (db.stock.get(v.id) ?? 0) > 0));
  const min = Number(q.get("min_price"));
  if (q.get("min_price") && !Number.isNaN(min)) list = list.filter((p) => p.final_price >= min);
  const max = Number(q.get("max_price"));
  if (q.get("max_price") && !Number.isNaN(max)) list = list.filter((p) => p.final_price <= max);
  return list;
}

function sortProducts(list: MockProduct[], ordering: string | null): MockProduct[] {
  const sorted = [...list];
  switch (ordering) {
    case "price":
      return sorted.sort((a, b) => a.final_price - b.final_price || b.id - a.id);
    case "-price":
      return sorted.sort((a, b) => b.final_price - a.final_price || b.id - a.id);
    case "-discount_percent":
      return sorted.sort((a, b) => b.discount_percent - a.discount_percent || b.created_at.localeCompare(a.created_at));
    case "popular":
      return sorted.sort((a, b) => b.sales_count - a.sales_count);
    default:
      return sorted.sort((a, b) => b.created_at.localeCompare(a.created_at) || b.id - a.id);
  }
}

function paginate<T>(items: T[], q: URLSearchParams, path: string) {
  const pageSize = Math.min(Number(q.get("page_size")) || PAGE_SIZE, 48);
  const page = Math.max(Number(q.get("page")) || 1, 1);
  const pages = Math.max(Math.ceil(items.length / pageSize), 1);
  if (page > pages) return null;
  const link = (n: number) => {
    const next = new URLSearchParams(q);
    next.set("page", String(n));
    return `${path}?${next.toString()}`;
  };
  return {
    count: items.length,
    next: page < pages ? link(page + 1) : null,
    previous: page > 1 ? link(page - 1) : null,
    results: items.slice((page - 1) * pageSize, page * pageSize),
  };
}

function userFromToken(token: string | null): User | null {
  const match = token?.match(/^mock-access-(\d+)$/);
  if (!match) return null;
  return db.users.find((u) => u.id === Number(match[1])) ?? null;
}

function buildCart(userId: number, warnings: string[] = []): Cart {
  const lines = db.carts.get(userId) ?? [];
  const items: CartItem[] = [];
  let subtotal = 0;
  let total = 0;
  let count = 0;
  for (const line of lines) {
    const found = findVariant(line.variant_id);
    if (!found) continue;
    const { product, variant } = found;
    const final = calcFinalPrice(product.base_price, product.discount_percent);
    let warning: string | null = null;
    if (variant.stock === 0) warning = "این مدل ناموجود است.";
    else if (line.quantity > variant.stock) warning = `از این مدل فقط ${fa(variant.stock)} عدد موجود است.`;
    items.push({
      id: line.id,
      product: { id: product.id, title: product.title, slug: product.slug, image: product.image },
      variant,
      quantity: line.quantity,
      unit_price: product.base_price,
      discount_percent: product.discount_percent,
      final_unit_price: final,
      line_total: final * line.quantity,
      warning,
    });
    subtotal += product.base_price * line.quantity;
    total += final * line.quantity;
    count += line.quantity;
  }
  return { id: userId, items, item_count: count, subtotal, discount_total: subtotal - total, total, warnings };
}

function checkQuantity(variant: Variant, quantity: number): MockResponse | null {
  if (quantity > MAX_QTY) {
    const text = `حداکثر ${fa(MAX_QTY)} عدد از هر مدل قابل سفارش است.`;
    return err(400, "validation_error", text, { quantity: [text] });
  }
  if (quantity > variant.stock) {
    const text = variant.stock === 0 ? "این مدل ناموجود است." : `از این مدل فقط ${fa(variant.stock)} عدد موجود است.`;
    return err(409, "out_of_stock", "موجودی کافی نیست.", { variant_id: [text] });
  }
  return null;
}

function validateAddress(body: Record<string, unknown>): Record<string, string[]> {
  const errors: Record<string, string[]> = {};
  const required = ["title", "receiver_name", "receiver_phone", "province", "city", "postal_code", "address_line"];
  for (const field of required) if (!String(body[field] ?? "").trim()) errors[field] = ["این فیلد الزامی است."];
  if (body.receiver_phone && !/^09\d{9}$/.test(String(body.receiver_phone)))
    errors.receiver_phone = ["شماره موبایل باید با ۰۹ شروع شود و ۱۱ رقم باشد."];
  if (body.postal_code && !/^\d{10}$/.test(String(body.postal_code))) errors.postal_code = ["کد پستی باید ۱۰ رقم باشد."];
  return errors;
}

function jalaliYear(): number {
  const year = new Intl.DateTimeFormat("en-US-u-ca-persian", { year: "numeric" }).format(new Date());
  return Number(year.replace(/\D/g, "")) || 1405;
}

type Body = Record<string, unknown>;

/** Route a request to the in-memory API. `path` is relative to /api (e.g. "/products/"). */
export function handleMock(method: string, rawPath: string, query: URLSearchParams, body: Body | null, token: string | null): MockResponse {
  const path = rawPath.endsWith("/") ? rawPath : `${rawPath}/`;
  const parts = path.split("/").filter(Boolean);
  const user = userFromToken(token);
  const m = method.toUpperCase();
  const b: Body = body ?? {};

  // ---------- catalog
  if (m === "GET" && path === "/categories/") return ok(categories);
  if (m === "GET" && path === "/collections/") return ok(collections);
  if (m === "GET" && parts[0] === "collections" && parts.length === 2) {
    const collection = collections.find((c) => c.slug === decodeURIComponent(parts[1]));
    return collection ? ok(collection) : notFound();
  }
  if (m === "GET" && path === "/products/") {
    const list = sortProducts(filterProducts(query), query.get("ordering")).map(toListItem);
    const page = paginate(list, query, "/products/");
    return page ? ok(page) : notFound();
  }
  if (m === "GET" && path === "/products/filters/") {
    const scope = filterProducts(query, { scopeOnly: true });
    const sizes = new Set<string>();
    const colors = new Map<string, string | null>();
    for (const p of scope)
      for (const v of p.variants)
        if ((db.stock.get(v.id) ?? 0) > 0) {
          sizes.add(v.size);
          if (!colors.has(v.color)) colors.set(v.color, v.color_hex ?? null);
        }
    const order = ["XS", "S", "M", "L", "XL", "XXL"];
    const sortedSizes = [...sizes].sort((a, c) => {
      const ia = order.indexOf(a);
      const ic = order.indexOf(c);
      if (ia >= 0 && ic >= 0) return ia - ic;
      return Number(a) - Number(c);
    });
    const prices = scope.map((p) => p.final_price);
    return ok({
      sizes: sortedSizes,
      colors: [...colors.entries()].map(([name, hex]) => ({ name, hex })),
      min_price: prices.length ? Math.min(...prices) : null,
      max_price: prices.length ? Math.max(...prices) : null,
    });
  }
  if (m === "GET" && parts[0] === "products" && parts.length === 2) {
    const product = products.find((p) => p.slug === decodeURIComponent(parts[1]) && p.is_active);
    if (!product) return notFound();
    const { created_at: _c, sales_count: _s, is_active: _a, ...detail } = product;
    return ok({ ...detail, variants: detail.variants.map(variantWithStock) });
  }
  if (m === "GET" && path === "/home/") {
    const active = products.filter((p) => p.is_active);
    const collection = collections[0];
    return ok({
      banners,
      categories,
      on_sale: sortProducts(
        active.filter((p) => p.discount_percent > 0),
        "-discount_percent",
      )
        .slice(0, 8)
        .map(toListItem),
      collection_highlight: {
        collection,
        products: sortProducts(
          active.filter((p) => p.collections.some((c) => c.id === collection.id)),
          "newest",
        )
          .slice(0, 8)
          .map(toListItem),
      },
      newest: sortProducts(active, "newest").slice(0, 8).map(toListItem),
    });
  }
  if (m === "GET" && path === "/site-settings/") return ok(siteSettings);
  if (m === "GET" && parts[0] === "pages" && parts.length === 2) {
    const page = pages[parts[1] as keyof typeof pages];
    return page ? ok(page) : notFound();
  }
  if (m === "GET" && path === "/payments/methods/") return ok(paymentMethods);
  if (m === "GET" && path === "/stores/") return ok(stores);
  if (m === "GET" && path === "/shipping-methods/") return ok(shippingMethods);

  // ---------- auth
  if (m === "POST" && path === "/auth/otp/request/") {
    const phone = String(b.phone ?? "");
    if (!/^09\d{9}$/.test(phone))
      return err(400, "validation_error", "اطلاعات ارسالی معتبر نیست.", { phone: ["شماره موبایل باید با ۰۹ شروع شود و ۱۱ رقم باشد."] });
    return ok({ detail: "کد تأیید ارسال شد. (کد آزمایشی: ۱۲۳۴۵)", expires_in: 120, resend_in: 60 });
  }
  if (m === "POST" && path === "/auth/otp/verify/") {
    const phone = String(b.phone ?? "");
    if (String(b.code ?? "") !== MOCK_CODE) return err(400, "otp_invalid", "کد تأیید اشتباه است.", { code: ["کد تأیید اشتباه است."] });
    let found = db.users.find((u) => u.phone === phone);
    const isNew = !found;
    if (!found) {
      found = { id: db.users.length + 1, phone, first_name: "", last_name: "", email: null, date_joined: new Date().toISOString() };
      db.users.push(found);
    }
    return ok({ access: `mock-access-${found.id}`, refresh: `mock-refresh-${found.id}`, user: found, is_new: isNew });
  }
  if (m === "POST" && path === "/auth/token/refresh/") {
    const match = String(b.refresh ?? "").match(/^mock-refresh-(\d+)$/);
    if (!match || !db.users.some((u) => u.id === Number(match[1]))) return unauthorized();
    return ok({ access: `mock-access-${match[1]}`, refresh: `mock-refresh-${match[1]}` });
  }
  if (m === "POST" && path === "/auth/logout/") return ok(null, 204);

  // ---------- everything below needs a user (except payment verify)
  if (m === "GET" && path === "/payments/verify/") {
    const payment = db.payments.find((p) => p.authority === query.get("Authority"));
    if (!payment) return notFound();
    const order = db.orders.find((o) => o.id === payment.order_id)!;
    if (payment.status === "initiated") {
      if ((query.get("Status") ?? "").toUpperCase() === "OK") {
        payment.status = "success";
        payment.ref_id = String(Math.floor(Math.random() * 1e10)).padStart(10, "0");
        order.status = "paid";
        order.status_display = "پرداخت‌شده";
        order.paid_at = new Date().toISOString();
        order.expires_at = null;
      } else payment.status = "cancelled";
    }
    const detail =
      payment.status === "success"
        ? "پرداخت با موفقیت انجام شد."
        : payment.status === "cancelled"
          ? "پرداخت لغو شد."
          : "پرداخت ناموفق بود.";
    return ok({
      status: payment.status === "success" ? "success" : payment.status === "cancelled" ? "cancelled" : "failed",
      detail,
      order_id: order.id,
      order_number: order.number,
      ref_id: payment.ref_id,
      amount: order.total,
    });
  }

  if (!user) return unauthorized();

  if (path === "/me/") {
    if (m === "GET") return ok(user);
    if (m === "PATCH") {
      for (const key of ["first_name", "last_name", "email"] as const) if (key in b) (user as Record<string, unknown>)[key] = b[key];
      return ok(user);
    }
  }

  // cart
  if (path === "/cart/" && m === "GET") return ok(buildCart(user.id));
  if (path === "/cart/items/" && m === "POST") {
    const found = findVariant(Number(b.variant_id));
    if (!found) return err(404, "not_found", "این محصول یافت نشد یا دیگر فروخته نمی‌شود.");
    const lines = db.carts.get(user.id) ?? [];
    const existing = lines.find((l) => l.variant_id === found.variant.id);
    const quantity = (existing?.quantity ?? 0) + Number(b.quantity || 1);
    const problem = checkQuantity(found.variant, quantity);
    if (problem) return problem;
    if (existing) existing.quantity = quantity;
    else lines.push({ id: nextId(), variant_id: found.variant.id, quantity });
    db.carts.set(user.id, lines);
    return ok(buildCart(user.id), 201);
  }
  if (parts[0] === "cart" && parts[1] === "items" && parts.length === 3) {
    const lines = db.carts.get(user.id) ?? [];
    const line = lines.find((l) => l.id === Number(parts[2]));
    if (!line) return notFound();
    if (m === "DELETE") {
      db.carts.set(
        user.id,
        lines.filter((l) => l !== line),
      );
      return ok(buildCart(user.id));
    }
    if (m === "PATCH") {
      const found = findVariant(line.variant_id)!;
      const problem = checkQuantity(found.variant, Number(b.quantity));
      if (problem) return problem;
      line.quantity = Number(b.quantity);
      return ok(buildCart(user.id));
    }
  }
  if (path === "/cart/merge/" && m === "POST") {
    const lines = db.carts.get(user.id) ?? [];
    const warnings: string[] = [];
    for (const entry of (b.items as { variant_id: number; quantity: number }[]) ?? []) {
      const found = findVariant(Number(entry.variant_id));
      if (!found) {
        warnings.push("یک محصول دیگر موجود نیست و به سبد اضافه نشد.");
        continue;
      }
      const existing = lines.find((l) => l.variant_id === found.variant.id);
      const desired = (existing?.quantity ?? 0) + Number(entry.quantity);
      const allowed = Math.min(desired, found.variant.stock, MAX_QTY);
      if (allowed <= 0) {
        warnings.push(`«${found.product.title}» ناموجود است و اضافه نشد.`);
        continue;
      }
      if (allowed < desired) warnings.push(`تعداد «${found.product.title}» به ${fa(allowed)} عدد کاهش یافت.`);
      if (existing) existing.quantity = allowed;
      else lines.push({ id: nextId(), variant_id: found.variant.id, quantity: allowed });
    }
    db.carts.set(user.id, lines);
    return ok(buildCart(user.id, warnings));
  }

  // addresses
  if (path === "/me/addresses/") {
    const mine = db.addresses.filter((a) => (a as Address & { user_id?: number }).user_id === user.id);
    if (m === "GET") return ok(mine.map(({ user_id: _u, ...a }: Address & { user_id?: number }) => a));
    if (m === "POST") {
      const errors = validateAddress(b);
      if (Object.keys(errors).length) return err(400, "validation_error", "اطلاعات ارسالی معتبر نیست.", errors);
      const isDefault = mine.length === 0 || Boolean(b.is_default);
      if (isDefault) mine.forEach((a) => (a.is_default = false));
      const address = { ...(b as unknown as Address), id: nextId(), is_default: isDefault, user_id: user.id };
      db.addresses.push(address);
      const { user_id: _u, ...out } = address;
      return ok(out, 201);
    }
  }
  if (parts[0] === "me" && parts[1] === "addresses" && parts.length === 3) {
    const address = db.addresses.find((a) => a.id === Number(parts[2]) && (a as Address & { user_id?: number }).user_id === user.id) as
      (Address & { user_id?: number }) | undefined;
    if (!address) return notFound();
    if (m === "DELETE") {
      db.addresses = db.addresses.filter((a) => a !== address);
      if (address.is_default) {
        const next = db.addresses.find((a) => (a as Address & { user_id?: number }).user_id === user.id);
        if (next) next.is_default = true;
      }
      return ok(null, 204);
    }
    if (m === "PATCH") {
      const merged = { ...address, ...b };
      const errors = validateAddress(merged);
      if (Object.keys(errors).length) return err(400, "validation_error", "اطلاعات ارسالی معتبر نیست.", errors);
      if (b.is_default)
        db.addresses.forEach((a) => {
          if ((a as Address & { user_id?: number }).user_id === user.id) a.is_default = false;
        });
      Object.assign(address, b);
      const { user_id: _u, ...out } = address;
      return ok(out);
    }
  }

  // orders
  if (path === "/orders/" && m === "POST") {
    const address = db.addresses.find((a) => a.id === Number(b.address_id) && (a as Address & { user_id?: number }).user_id === user.id);
    if (!address) return err(400, "validation_error", "آدرس انتخاب‌شده یافت نشد.", { address_id: ["آدرس انتخاب‌شده یافت نشد."] });
    const method = shippingMethods.find((s) => s.id === Number(b.shipping_method_id));
    if (!method) return err(400, "validation_error", "روش ارسال انتخاب‌شده معتبر نیست.", { shipping_method_id: ["روش ارسال معتبر نیست."] });
    const cart = buildCart(user.id);
    if (!cart.items.length) return err(400, "cart_empty", "سبد خرید شما خالی است.");
    const problems = cart.items.filter((i) => i.warning).map((i) => `«${i.product.title}»: ${i.warning}`);
    if (problems.length) return err(409, "out_of_stock", "موجودی کافی نیست.", { items: problems });
    const shippingCost = method.free_over !== null && method.free_over !== undefined && cart.total >= method.free_over ? 0 : method.cost;
    const items: OrderItem[] = cart.items.map((i) => ({
      id: nextId(),
      product_slug: i.product.slug,
      title: i.product.title,
      image: i.product.image,
      size: i.variant.size,
      color: i.variant.color,
      quantity: i.quantity,
      unit_price: i.unit_price,
      discount_percent: i.discount_percent,
      final_unit_price: i.final_unit_price,
      line_total: i.line_total,
    }));
    for (const i of cart.items) db.stock.set(i.variant.id, (db.stock.get(i.variant.id) ?? 0) - i.quantity);
    const { user_id: _u, id: _id, ...addressSnapshot } = address as Address & { user_id?: number };
    const order: Order & { user_id: number } = {
      id: nextId(),
      number: `${jalaliYear()}-${String(db.orders.length + 1).padStart(6, "0")}`,
      status: "pending",
      status_display: "در انتظار پرداخت",
      items,
      subtotal: cart.subtotal,
      discount_total: cart.discount_total,
      shipping_cost: shippingCost,
      total: cart.total + shippingCost,
      shipping_method: { ...method, cost: shippingCost },
      address: addressSnapshot,
      note: String(b.note ?? ""),
      tracking_code: null,
      expires_at: new Date(Date.now() + 30 * 60_000).toISOString(),
      created_at: new Date().toISOString(),
      paid_at: null,
      user_id: user.id,
    };
    db.orders.unshift(order);
    db.carts.set(user.id, []);
    const { user_id: _uid, ...out } = order;
    return ok(out, 201);
  }
  if (path === "/me/orders/" && m === "GET") {
    let mine = db.orders.filter((o) => o.user_id === user.id);
    const status = query.get("status");
    if (status) mine = mine.filter((o) => o.status === status);
    const page = paginate(
      mine.map(({ user_id: _u, ...o }) => o),
      query,
      "/me/orders/",
    );
    return page ? ok(page) : notFound();
  }
  if (parts[0] === "me" && parts[1] === "orders" && parts.length === 3 && m === "GET") {
    const order = db.orders.find((o) => o.id === Number(parts[2]) && o.user_id === user.id);
    if (!order) return notFound();
    const { user_id: _u, ...out } = order;
    return ok(out);
  }

  // payments
  if (path === "/payments/start/" && m === "POST") {
    const order = db.orders.find((o) => o.id === Number(b.order_id) && o.user_id === user.id);
    if (!order) return notFound();
    if (order.status !== "pending") return err(400, "order_not_payable", "این سفارش قابل پرداخت نیست.");
    const authority = `MOCK${Date.now()}${Math.floor(Math.random() * 1000)}`;
    db.payments.push({ authority, order_id: order.id, status: "initiated", ref_id: null });
    return ok({ redirect_url: `/payment/result?Authority=${authority}&Status=OK`, payment_id: db.payments.length });
  }

  return notFound();
}
