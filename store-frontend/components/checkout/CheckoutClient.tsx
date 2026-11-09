"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { AddressForm } from "@/components/account/AddressForm";
import { CartLines } from "@/components/cart/CartLines";
import { CartSummary } from "@/components/cart/CartSummary";
import { Button, ButtonLink } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Textarea } from "@/components/ui/Input";
import { Skeleton } from "@/components/ui/Skeleton";
import { SmartImage } from "@/components/ui/SmartImage";
import { M } from "@/constants/messages";
import { CART_KEY, useCart } from "@/hooks/useCart";
import { errorMessage, isApiError } from "@/lib/api/errors";
import { checkoutApi, meApi } from "@/lib/api/shop";
import { formatPrice, toFaDigits } from "@/lib/format";
import { cn } from "@/lib/utils";
import { toast } from "@/store/uiStore";
import type { PaymentMethod, ShippingMethod } from "@/types/api";

const ADDRESSES_KEY = ["addresses"] as const;

function supportsAmount(method: PaymentMethod, amount: number): boolean {
  if (method.min_amount != null && amount < method.min_amount) return false;
  return method.max_amount == null || amount <= method.max_amount;
}

function shippingCostFor(method: ShippingMethod | undefined, itemsTotal: number): number | null {
  if (!method) return null;
  if (method.free_over != null && itemsTotal >= method.free_over) return 0;
  return method.cost;
}

export function CheckoutClient() {
  const queryClient = useQueryClient();
  const { cart, isLoading: cartLoading, setQuantity, remove, isMutating } = useCart();
  const addresses = useQuery({ queryKey: ADDRESSES_KEY, queryFn: meApi.addresses });
  const methods = useQuery({ queryKey: ["shipping-methods"], queryFn: checkoutApi.shippingMethods, staleTime: 10 * 60_000 });
  const paymentMethods = useQuery({ queryKey: ["payment-methods"], queryFn: checkoutApi.paymentMethods });

  const [step, setStep] = useState(0);
  const [addressId, setAddressId] = useState<number | null>(null);
  const [methodId, setMethodId] = useState<number | null>(null);
  const [paymentCode, setPaymentCode] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [showAddressForm, setShowAddressForm] = useState(false);

  const selectedAddressId = addressId ?? addresses.data?.find((a) => a.is_default)?.id ?? addresses.data?.[0]?.id ?? null;
  const selectedMethodId = methodId ?? methods.data?.[0]?.id ?? null;
  const method = methods.data?.find((m) => m.id === selectedMethodId);
  const shippingCost = shippingCostFor(method, cart.total);

  const payable = cart.total + (shippingCost ?? 0);
  const usablePayments = paymentMethods.data?.filter((p) => supportsAmount(p, payable)) ?? [];
  const selectedPayment = usablePayments.find((p) => p.code === paymentCode)?.code ?? usablePayments[0]?.code ?? null;

  const pay = useMutation({
    mutationFn: async () => {
      // Server recalculates everything; client totals are display only.
      const order = await checkoutApi.createOrder({ address_id: selectedAddressId!, shipping_method_id: selectedMethodId!, note });
      queryClient.invalidateQueries({ queryKey: CART_KEY });
      const { redirect_url } = await checkoutApi.startPayment(order.id, selectedPayment!);
      return redirect_url;
    },
    onSuccess: (url) => {
      toast.info(M.checkout.redirecting);
      window.location.assign(url);
    },
    onError: (error) => {
      if (isApiError(error)) error.allMessages().forEach((m) => toast.error(m));
      else toast.error(errorMessage(error));
      queryClient.invalidateQueries({ queryKey: CART_KEY });
    },
  });

  if (cartLoading || addresses.isLoading) return <Skeleton className="h-96" />;
  if (cart.items.length === 0 && !pay.isPending && !pay.isSuccess) {
    return <EmptyState title={M.checkout.emptyCart} action={<ButtonLink href="/">{M.cart.continue}</ButtonLink>} />;
  }

  const canNext = [selectedAddressId !== null, selectedMethodId !== null, !cart.items.some((i) => i.warning)][step] ?? true;

  return (
    <div className="grid items-start gap-8 lg:grid-cols-[1fr_22rem]">
      <div className="flex flex-col gap-6">
        <ol className="flex gap-2 text-xs sm:text-sm" aria-label="مراحل خرید">
          {M.checkout.steps.map((label, i) => (
            <li
              key={label}
              aria-current={i === step ? "step" : undefined}
              className={cn(
                "flex flex-1 items-center gap-2 rounded-lg px-3 py-2",
                i === step ? "bg-ink text-white" : i < step ? "bg-sand" : "bg-surface ring-line text-muted ring-1",
              )}
            >
              <span className="font-bold">{toFaDigits(i + 1)}</span>
              {label}
            </li>
          ))}
        </ol>

        <section className="rounded-card bg-surface ring-line p-5 ring-1">
          {step === 0 && (
            <div className="flex flex-col gap-4">
              <h2 className="font-bold">{M.checkout.selectAddress}</h2>
              {addresses.data?.length === 0 && !showAddressForm && <p className="text-muted text-sm">{M.checkout.noAddress}</p>}
              <div className="flex flex-col gap-3" role="radiogroup" aria-label={M.checkout.selectAddress}>
                {addresses.data?.map((a) => (
                  <label
                    key={a.id}
                    className={cn(
                      "flex cursor-pointer gap-3 rounded-lg border p-4 text-sm",
                      selectedAddressId === a.id ? "border-ink" : "border-line",
                    )}
                  >
                    <input
                      type="radio"
                      name="address"
                      className="accent-ink mt-1"
                      checked={selectedAddressId === a.id}
                      onChange={() => setAddressId(a.id)}
                    />
                    <span className="flex flex-col gap-1">
                      <span className="font-bold">{a.title}</span>
                      <span className="text-ink-soft">
                        {a.province}، {a.city}، {a.address_line}
                      </span>
                      <span className="text-muted">
                        {a.receiver_name} — <span className="ltr-nums">{toFaDigits(a.receiver_phone)}</span>
                      </span>
                    </span>
                  </label>
                ))}
              </div>
              {showAddressForm || addresses.data?.length === 0 ? (
                <AddressForm
                  onCancel={addresses.data?.length ? () => setShowAddressForm(false) : undefined}
                  onSubmit={async (values) => {
                    const created = await meApi.createAddress(values);
                    await queryClient.invalidateQueries({ queryKey: ADDRESSES_KEY });
                    setAddressId(created.id);
                    setShowAddressForm(false);
                    toast.success(M.account.addressSaved);
                  }}
                />
              ) : (
                <Button variant="outline" size="sm" className="w-fit" onClick={() => setShowAddressForm(true)}>
                  {M.checkout.addAddress}
                </Button>
              )}
            </div>
          )}

          {step === 1 && (
            <div className="flex flex-col gap-4">
              <h2 className="font-bold">{M.checkout.selectShipping}</h2>
              {methods.isLoading && <Skeleton className="h-32" />}
              <div className="flex flex-col gap-3" role="radiogroup" aria-label={M.checkout.selectShipping}>
                {methods.data?.map((m) => {
                  const cost = shippingCostFor(m, cart.total);
                  return (
                    <label
                      key={m.id}
                      className={cn(
                        "flex cursor-pointer items-center gap-3 rounded-lg border p-4 text-sm",
                        selectedMethodId === m.id ? "border-ink" : "border-line",
                      )}
                    >
                      <input
                        type="radio"
                        name="shipping"
                        className="accent-ink"
                        checked={selectedMethodId === m.id}
                        onChange={() => setMethodId(m.id)}
                      />
                      <span className="flex flex-1 flex-col gap-1">
                        <span className="font-bold">{m.title}</span>
                        {m.description && <span className="text-muted">{m.description}</span>}
                        {m.free_over != null && (
                          <span className="text-success text-xs">{M.checkout.freeOver(formatPrice(m.free_over))}</span>
                        )}
                      </span>
                      <span className="font-medium">{cost === 0 ? M.checkout.free : formatPrice(cost ?? m.cost)}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="flex flex-col gap-4">
              <h2 className="font-bold">{M.checkout.review}</h2>
              <CartLines items={cart.items} onQuantity={setQuantity} onRemove={remove} disabled={isMutating} />
              <Textarea label={M.checkout.note} value={note} maxLength={500} onChange={(e) => setNote(e.target.value)} />
            </div>
          )}

          {step === 3 && (
            <div className="flex flex-col items-start gap-4">
              <h2 className="font-bold">{M.checkout.pay}</h2>
              {paymentMethods.isLoading && <Skeleton className="h-32 w-full" />}
              {paymentMethods.isSuccess && usablePayments.length === 0 && <p className="text-sale text-sm">{M.checkout.noPaymentMethod}</p>}
              {usablePayments.length > 0 && <p className="text-sm">{M.checkout.selectPayment}</p>}
              <div className="flex w-full flex-col gap-3" role="radiogroup" aria-label={M.checkout.selectPayment}>
                {paymentMethods.data?.map((p) => {
                  const usable = supportsAmount(p, payable);
                  return (
                    <label
                      key={p.code}
                      className={cn(
                        "flex items-center gap-3 rounded-lg border p-4 text-sm",
                        usable ? "cursor-pointer" : "cursor-not-allowed opacity-60",
                        selectedPayment === p.code ? "border-ink" : "border-line",
                      )}
                    >
                      <input
                        type="radio"
                        name="payment"
                        className="accent-ink"
                        disabled={!usable}
                        checked={selectedPayment === p.code}
                        onChange={() => setPaymentCode(p.code)}
                      />
                      {p.logo && (
                        <span className="relative size-8 shrink-0">
                          <SmartImage src={p.logo} alt="" fill sizes="32px" className="object-contain" />
                        </span>
                      )}
                      <span className="flex flex-1 flex-col gap-1">
                        <span className="font-bold">{p.title}</span>
                        <span className="text-muted">{usable ? p.description : M.checkout.amountNotSupported}</span>
                      </span>
                    </label>
                  );
                })}
              </div>
              <p className="text-muted text-sm">{M.checkout.totalsNote}</p>
              <Button size="lg" loading={pay.isPending || pay.isSuccess} disabled={!selectedPayment} onClick={() => pay.mutate()}>
                {M.checkout.placeOrder}
              </Button>
            </div>
          )}
        </section>

        <div className="flex justify-between">
          <Button variant="ghost" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0 || pay.isPending}>
            {M.checkout.back}
          </Button>
          {step < 3 && (
            <Button onClick={() => setStep((s) => s + 1)} disabled={!canNext}>
              {M.checkout.next}
            </Button>
          )}
        </div>
      </div>

      <div className="lg:sticky lg:top-32">
        <CartSummary
          subtotal={cart.subtotal}
          discountTotal={cart.discount_total}
          total={cart.total}
          shippingCost={shippingCost}
          note={M.checkout.totalsNote}
        />
      </div>
    </div>
  );
}
