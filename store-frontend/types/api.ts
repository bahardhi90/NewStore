/**
 * Friendly aliases over the types generated from contract/openapi.yaml.
 * Regenerate with `npm run gen:api` whenever the contract changes.
 */
import type { components } from "./api.generated";

type S = components["schemas"];

export type ApiErrorBody = S["Error"];
export type Category = S["Category"];
export type Collection = S["Collection"];
export type ProductListItem = S["ProductListItem"];
export type ProductDetail = S["ProductDetail"];
export type ProductImage = S["ProductImage"];
export type Variant = S["Variant"];
export type ProductFilterOptions = S["ProductFilterOptions"];
export type Paginated<T> = { count: number; next: string | null; previous: string | null; results: T[] };
export type PaginatedProducts = S["PaginatedProductList"];
export type Banner = S["Banner"];
export type Home = S["Home"];
export type Cart = S["Cart"];
export type CartItem = S["CartItem"];
export type CartItemCreate = S["CartItemCreate"];
export type ShippingMethod = S["ShippingMethod"];
export type OrderStatus = S["OrderStatus"];
export type Order = S["Order"];
export type OrderItem = S["OrderItem"];
export type OrderCreate = S["OrderCreate"];
export type PaginatedOrders = S["PaginatedOrderList"];
export type PaymentMethod = S["PaymentMethod"];
export type PaymentStartResponse = S["PaymentStartResponse"];
export type PaymentVerifyResponse = S["PaymentVerifyResponse"];
export type OtpRequestResponse = S["OtpRequestResponse"];
export type AuthTokens = S["AuthTokens"];
export type User = S["User"];
export type UserUpdate = S["UserUpdate"];
export type Address = S["Address"];
export type AddressInput = S["AddressInput"];
export type Store = S["Store"];
export type SiteSettings = S["SiteSettings"];
export type TrustBadge = S["TrustBadge"];
export type SizeChart = S["SizeChart"];
export type Page = S["Page"];

export type ProductQuery = {
  category?: string;
  collection?: string;
  on_sale?: boolean;
  search?: string;
  size?: string;
  color?: string;
  min_price?: number;
  max_price?: number;
  ordering?: "newest" | "price" | "-price" | "-discount_percent" | "popular";
  page?: number;
  page_size?: number;
};
