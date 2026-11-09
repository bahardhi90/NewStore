/**
 * Static demo data used when NEXT_PUBLIC_USE_MOCKS=true.
 * Shapes follow contract/openapi.yaml exactly.
 */
import type { Banner, Category, Collection, PaymentMethod, ProductDetail, ShippingMethod, SiteSettings, Store, Variant } from "@/types/api";

const COLORS = [
  { key: "black", name: "مشکی", hex: "#1f1f1f" },
  { key: "navy", name: "سرمه‌ای", hex: "#1e2a4a" },
  { key: "gray", name: "طوسی", hex: "#8a8d91" },
  { key: "cream", name: "کرم", hex: "#d8c7a8" },
  { key: "olive", name: "زیتونی", hex: "#5b6236" },
  { key: "brown", name: "قهوه‌ای", hex: "#6b4630" },
  { key: "white", name: "سفید", hex: "#e9e6df" },
  { key: "sky", name: "آبی روشن", hex: "#9cb8d6" },
] as const;

const TOP_SIZES = ["S", "M", "L", "XL", "XXL"];
const PANT_SIZES = ["30", "32", "34", "36", "38"];

export const categories: Category[] = [
  { id: 1, name: "کاپشن و جلیقه", slug: "jackets", parent: null, image: "/mock/category-jackets.svg" },
  { id: 2, name: "شلوار", slug: "pants", parent: null, image: "/mock/category-pants.svg" },
  { id: 3, name: "پیراهن", slug: "shirts", parent: null, image: "/mock/category-shirts.svg" },
];

export const collections: Collection[] = [
  {
    id: 1,
    title: "کالکشن بهاره",
    slug: "spring-collection",
    description: "رنگ‌های روشن و پارچه‌های سبک برای روزهای بهاری",
    banner: "/mock/banner-spring.svg",
    banner_mobile: null,
  },
  {
    id: 2,
    title: "کالکشن زمستانه",
    slug: "winter-collection",
    description: "گرم و شیک برای روزهای سرد",
    banner: "/mock/banner-winter.svg",
    banner_mobile: null,
  },
];

const CATALOG: Record<string, { shape: string; sizes: string[]; items: [string, number][] }> = {
  jackets: {
    shape: "jacket",
    sizes: TOP_SIZES,
    items: [
      ["کاپشن پافر کلاه‌دار", 4_890_000],
      ["جلیقه پفی سبک", 2_350_000],
      ["کت پشمی کلاسیک", 6_200_000],
      ["کاپشن چرم مصنوعی", 5_450_000],
      ["بارانی بلند", 5_900_000],
      ["کاپشن جین", 3_150_000],
      ["جلیقه کتان", 1_890_000],
      ["کت تک اسپرت", 4_700_000],
    ],
  },
  pants: {
    shape: "pants",
    sizes: PANT_SIZES,
    items: [
      ["شلوار جین اسلیم", 1_950_000],
      ["شلوار کتان راسته", 1_690_000],
      ["شلوار پارچه‌ای رسمی", 2_250_000],
      ["شلوار کارگو", 2_050_000],
      ["شلوار اسلش", 1_350_000],
      ["شلوار جین مام‌فیت", 2_100_000],
      ["شلوارک کتان", 990_000],
      ["شلوار مخمل کبریتی", 2_390_000],
    ],
  },
  shirts: {
    shape: "shirt",
    sizes: TOP_SIZES,
    items: [
      ["پیراهن آکسفورد", 1_490_000],
      ["پیراهن کتان آستین کوتاه", 1_190_000],
      ["پیراهن چهارخانه فلانل", 1_650_000],
      ["پیراهن رسمی یقه کلاسیک", 1_790_000],
      ["پیراهن لینن", 1_890_000],
      ["پیراهن جین", 1_550_000],
      ["پیراهن یقه دیپلمات", 1_590_000],
      ["پیراهن راه‌راه", 1_420_000],
    ],
  },
};

/** Same formula as the backend: rounded down to 1,000 Toman. */
export function calcFinalPrice(base: number, discount: number): number {
  if (discount <= 0) return base;
  return Math.floor((base * (100 - discount)) / 100 / 1000) * 1000;
}

// Deterministic pseudo-random so mock data is stable between reloads.
function seeded(seed: number) {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
}

export type MockProduct = ProductDetail & { created_at: string; sales_count: number; is_active: boolean };

function buildProducts(): MockProduct[] {
  const rand = seeded(42);
  const discounts = [0, 0, 0, 10, 15, 20, 25, 30];
  const stocks = [0, 2, 5, 8, 12, 20];
  const products: MockProduct[] = [];
  let id = 0;
  let variantId = 100;
  const base = Date.UTC(2026, 9, 1);

  for (const [catIndex, [slug, def]] of Object.entries(CATALOG).entries()) {
    const category = categories.find((c) => c.slug === slug)!;
    def.items.forEach(([title, price], index) => {
      id += 1;
      const discount = discounts[Math.floor(rand() * discounts.length)];
      const start = Math.floor(rand() * COLORS.length);
      const colorCount = rand() > 0.5 ? 3 : 2;
      const colors = Array.from({ length: colorCount }, (_, i) => COLORS[(start + i * 3) % COLORS.length]);
      const variants: Variant[] = [];
      for (const color of colors) {
        for (const size of def.sizes) {
          variantId += 1;
          variants.push({
            id: variantId,
            size,
            color: color.name,
            color_hex: color.hex,
            stock: stocks[Math.floor(rand() * stocks.length)],
          });
        }
      }
      const images = colors
        .slice(0, 2)
        .map((c) => ({ image: `/mock/${def.shape}-${c.key}.svg`, alt: `${title} ${c.name}`, color: c.name }));
      products.push({
        id,
        title,
        slug: `${slug}-${index + 1}`,
        image: images[0].image,
        hover_image: images[1]?.image ?? null,
        base_price: price,
        discount_percent: discount,
        final_price: calcFinalPrice(price, discount),
        description:
          `${title} با دوخت باکیفیت و پارچه مرغوب. مناسب استفاده روزمره و مجلسی.\n` +
          "جنس: ترکیب پنبه و پلی‌استر | شستشو: با آب سرد | ساخت ایران",
        category,
        collections: [collections[index % 2]],
        images,
        variants,
        created_at: new Date(base + (catIndex * 8 + index) * 86_400_000).toISOString(),
        sales_count: Math.floor(rand() * 200),
        is_active: true,
      });
    });
  }
  return products;
}

export const products: MockProduct[] = buildProducts();

export const banners: Banner[] = [
  {
    id: 1,
    title: "کالکشن بهاره رسید",
    subtitle: "تا ۳۰٪ تخفیف روی محصولات منتخب",
    image: "/mock/banner-spring.svg",
    image_mobile: null,
    link: "/collection/spring-collection",
  },
  {
    id: 2,
    title: "کاپشن‌های زمستانه",
    subtitle: "گرم، سبک و شیک",
    image: "/mock/banner-winter.svg",
    image_mobile: null,
    link: "/category/jackets",
  },
  {
    id: 3,
    title: "حراج پیراهن",
    subtitle: "فقط تا پایان هفته",
    image: "/mock/banner-sale.svg",
    image_mobile: null,
    link: "/category/shirts?on_sale=true",
  },
];

export const stores: Store[] = [
  {
    id: 1,
    name: "شعبه مرکزی",
    city: "تهران",
    address: "تهران، خیابان ولیعصر، بالاتر از پارک ملت، مجتمع تجاری نگین، طبقه اول",
    phone: "021-22000000",
    hours: "شنبه تا پنجشنبه ۱۰ تا ۲۲",
    latitude: 35.7766,
    longitude: 51.4142,
    image: null,
  },
  {
    id: 2,
    name: "شعبه شمال تهران",
    city: "تهران",
    address: "تهران، تجریش، مرکز خرید ارگ، طبقه دوم",
    phone: "021-22700000",
    hours: "همه‌روزه ۱۰ تا ۲۳",
    latitude: 35.8044,
    longitude: 51.4269,
    image: null,
  },
  {
    id: 3,
    name: "شعبه اصفهان",
    city: "اصفهان",
    address: "اصفهان، خیابان چهارباغ بالا، مجتمع پارک",
    phone: "031-36000000",
    hours: "شنبه تا پنجشنبه ۱۰ تا ۲۲",
    latitude: 32.6366,
    longitude: 51.6608,
    image: null,
  },
  {
    id: 4,
    name: "شعبه شیراز",
    city: "شیراز",
    address: "شیراز، بلوار چمران، مجتمع خلیج فارس",
    phone: "071-36200000",
    hours: "شنبه تا پنجشنبه ۱۰ تا ۲۲",
    latitude: 29.6402,
    longitude: 52.4855,
    image: null,
  },
];

export const shippingMethods: ShippingMethod[] = [
  { id: 1, title: "پست پیشتاز", description: "۳ تا ۵ روز کاری", cost: 60_000, free_over: 3_000_000 },
  { id: 2, title: "تیپاکس", description: "۱ تا ۳ روز کاری", cost: 95_000, free_over: 5_000_000 },
  { id: 3, title: "پیک (فقط تهران)", description: "همان روز / روز بعد", cost: 120_000, free_over: null },
];

export const siteSettings: SiteSettings = {
  brand_name: "کرامت",
  tagline: "پوشاک مردانه با کیفیت و قیمت منصفانه",
  logo: null,
  announcement_text: "ارسال رایگان برای خریدهای بالای ۳ میلیون تومان",
  instagram_url: "https://instagram.com",
  telegram_url: "https://t.me",
  trust_badges: [
    { icon: "return", title: "۷ روز ضمانت بازگشت", subtitle: "بدون پرسش، کامل" },
    { icon: "truck", title: "ارسال سریع", subtitle: "به سراسر ایران" },
    { icon: "shield", title: "پرداخت امن", subtitle: "درگاه معتبر بانکی" },
    { icon: "badge", title: "ضمانت اصالت", subtitle: "تولید و دوخت باکیفیت" },
  ],
  shipping_points: [
    "ارسال به سراسر کشور با پست پیشتاز و تیپاکس؛ ارسال رایگان برای خریدهای بالای ۳ میلیون تومان.",
    "تا ۷ روز پس از تحویل می‌توانید کالا را بدون استفاده و با برچسب سالم مرجوع کنید.",
    "تعویض سایز رایگان است.",
  ],
  size_guide_note: "اندازه‌ها به سانتی‌متر است. اگر بین دو سایز هستید، سایز بزرگ‌تر را انتخاب کنید.",
  size_charts: [
    {
      title: "کاپشن، کت و پیراهن",
      columns: ["سایز", "دور سینه", "قد", "سرشانه تا سرآستین"],
      rows: [
        ["S", "۹۶–۱۰۰", "۷۰", "۶۲"],
        ["M", "۱۰۰–۱۰۴", "۷۲", "۶۳"],
        ["L", "۱۰۴–۱۱۰", "۷۴", "۶۴"],
        ["XL", "۱۱۰–۱۱۶", "۷۶", "۶۵"],
        ["XXL", "۱۱۶–۱۲۲", "۷۸", "۶۶"],
      ],
    },
    {
      title: "شلوار",
      columns: ["سایز", "دور کمر", "قد"],
      rows: [
        ["۳۰", "۷۶", "۱۰۲"],
        ["۳۲", "۸۱", "۱۰۳"],
        ["۳۴", "۸۶", "۱۰۴"],
        ["۳۶", "۹۱", "۱۰۵"],
        ["۳۸", "۹۶", "۱۰۶"],
      ],
    },
  ],
  footer_columns: [
    {
      title: "راهنمای خرید",
      links: [
        { title: "سوالات متداول", url: "/faq" },
        { title: "شرایط مرجوعی", url: "/returns" },
        { title: "پیگیری سفارش", url: "/account/orders" },
      ],
    },
    {
      title: "فروشگاه",
      links: [
        { title: "درباره ما", url: "/about" },
        { title: "تماس با ما", url: "/contact" },
        { title: "شعب", url: "/stores" },
      ],
    },
  ],
};

export const paymentMethods: PaymentMethod[] = [
  {
    code: "zarinpal",
    title: "پرداخت اینترنتی",
    description: "پرداخت با تمام کارت‌های بانکی عضو شتاب",
    logo: null,
    min_amount: null,
    max_amount: null,
  },
  { code: "digipay", title: "دیجی‌پی", description: "خرید اعتباری و اقساطی با دیجی‌پی", logo: null, min_amount: null, max_amount: null },
  { code: "snapppay", title: "اسنپ‌پی", description: "خرید اقساطی با اسنپ‌پی", logo: null, min_amount: null, max_amount: null },
];
