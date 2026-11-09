/** Client-side API calls (cart, orders, payments, account). */
import type {
  Address,
  AddressInput,
  Cart,
  CartItemCreate,
  Order,
  OrderCreate,
  OrderStatus,
  OtpRequestResponse,
  PaginatedOrders,
  PaginatedProducts,
  PaymentMethod,
  PaymentStartResponse,
  PaymentVerifyResponse,
  ShippingMethod,
  User,
  UserUpdate,
} from "@/types/api";

import { bff, http } from "./client";

export const authApi = {
  requestOtp: async (phone: string) => (await http.post<OtpRequestResponse>("/auth/otp/request", { phone })).data,
  verifyOtp: async (phone: string, code: string) =>
    (await http.post<{ user: User; is_new: boolean }>("/auth/otp/verify", { phone, code })).data,
  logout: async () => {
    await http.post("/auth/logout");
  },
};

export const meApi = {
  get: () => bff.get<User>("/me/"),
  update: (data: UserUpdate) => bff.patch<User>("/me/", data),
  addresses: () => bff.get<Address[]>("/me/addresses/"),
  createAddress: (data: AddressInput) => bff.post<Address>("/me/addresses/", data),
  updateAddress: (id: number, data: Partial<AddressInput>) => bff.patch<Address>(`/me/addresses/${id}/`, data),
  deleteAddress: (id: number) => bff.delete<null>(`/me/addresses/${id}/`),
  orders: (params: { page?: number; status?: OrderStatus } = {}) => bff.get<PaginatedOrders>("/me/orders/", params),
  order: (id: number) => bff.get<Order>(`/me/orders/${id}/`),
};

export const searchApi = {
  suggest: (query: string, limit: number) => bff.get<PaginatedProducts>("/products/", { search: query, page_size: limit }),
};

export const cartApi = {
  get: () => bff.get<Cart>("/cart/"),
  add: (data: CartItemCreate) => bff.post<Cart>("/cart/items/", data),
  update: (itemId: number, quantity: number) => bff.patch<Cart>(`/cart/items/${itemId}/`, { quantity }),
  remove: (itemId: number) => bff.delete<Cart>(`/cart/items/${itemId}/`),
  merge: (items: CartItemCreate[]) => bff.post<Cart>("/cart/merge/", { items }),
};

export const checkoutApi = {
  shippingMethods: () => bff.get<ShippingMethod[]>("/shipping-methods/"),
  createOrder: (data: OrderCreate) => bff.post<Order>("/orders/", data),
  paymentMethods: () => bff.get<PaymentMethod[]>("/payments/methods/"),
  startPayment: (orderId: number, method?: string) => bff.post<PaymentStartResponse>("/payments/start/", { order_id: orderId, method }),
  verifyPayment: (authority: string, status: string, trackingCode?: string | null, type?: string | null) =>
    bff.get<PaymentVerifyResponse>("/payments/verify/", {
      Authority: authority,
      Status: status,
      ...(trackingCode ? { TrackingCode: trackingCode } : {}),
      ...(type ? { Type: type } : {}),
    }),
};
