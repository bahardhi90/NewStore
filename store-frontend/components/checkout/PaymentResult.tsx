"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";

import { Button, ButtonLink } from "@/components/ui/Button";
import { AlertIcon, CheckIcon } from "@/components/ui/icons";
import { Spinner } from "@/components/ui/Spinner";
import { M } from "@/constants/messages";
import { errorMessage } from "@/lib/api/errors";
import { checkoutApi } from "@/lib/api/shop";
import { formatPrice, toFaDigits } from "@/lib/format";
import { toast } from "@/store/uiStore";

/** Gateway redirects here with ?Authority=...&Status=...; we verify server-side (idempotent). */
export function PaymentResult() {
  const params = useSearchParams();
  const authority = params.get("Authority");
  const status = params.get("Status");
  const trackingCode = params.get("TrackingCode");
  const type = params.get("Type");

  const verify = useQuery({
    queryKey: ["payment-verify", authority, status, trackingCode, type],
    queryFn: () => checkoutApi.verifyPayment(authority!, status!, trackingCode, type),
    enabled: Boolean(authority && status),
    retry: 2,
    staleTime: Infinity,
  });

  const retry = useMutation({
    mutationFn: (orderId: number) => checkoutApi.startPayment(orderId),
    onSuccess: ({ redirect_url }) => window.location.assign(redirect_url),
    onError: (error) => toast.error(errorMessage(error)),
  });

  const card = "flex w-full max-w-lg flex-col items-center gap-4 rounded-card bg-surface p-8 text-center ring-1 ring-line";

  if (!authority || !status) {
    return (
      <div className={card}>
        <AlertIcon className="text-warning size-12" />
        <p>{M.payment.invalid}</p>
        <ButtonLink href="/">{M.payment.backHome}</ButtonLink>
      </div>
    );
  }

  if (verify.isLoading) {
    return (
      <div className={card} aria-live="polite">
        <Spinner className="size-10" />
        <p>{M.payment.verifying}</p>
      </div>
    );
  }

  if (verify.isError || !verify.data) {
    return (
      <div className={card}>
        <AlertIcon className="text-sale size-12" />
        <p>{errorMessage(verify.error)}</p>
        <Button onClick={() => verify.refetch()}>{M.errors.tryAgain}</Button>
      </div>
    );
  }

  const result = verify.data;
  const success = result.status === "success";
  const title = success ? M.payment.success : result.status === "cancelled" ? M.payment.cancelled : M.payment.failed;

  return (
    <div className={card} aria-live="polite">
      <span
        className={`flex size-16 items-center justify-center rounded-full ${success ? "bg-success-soft text-success" : "bg-sale-soft text-sale"}`}
      >
        {success ? <CheckIcon className="size-8" /> : <AlertIcon className="size-8" />}
      </span>
      <h1 className="text-xl font-black">{title}</h1>
      <p className="text-muted text-sm leading-7">{result.detail}</p>
      <dl className="divide-line bg-sand w-full divide-y rounded-lg px-4 text-sm">
        {result.order_number && (
          <div className="flex justify-between py-3">
            <dt className="text-muted">{M.payment.orderNumber}</dt>
            <dd className="ltr-nums font-bold">{toFaDigits(result.order_number)}</dd>
          </div>
        )}
        {success && result.ref_id && (
          <div className="flex justify-between py-3">
            <dt className="text-muted">{M.payment.refId}</dt>
            <dd className="ltr-nums font-bold">{toFaDigits(result.ref_id)}</dd>
          </div>
        )}
        {result.amount != null && (
          <div className="flex justify-between py-3">
            <dt className="text-muted">{M.payment.amount}</dt>
            <dd>{formatPrice(result.amount)}</dd>
          </div>
        )}
      </dl>
      <div className="flex flex-wrap justify-center gap-2">
        {result.order_id && (
          <ButtonLink href={`/account/orders/${result.order_id}`} variant={success ? "primary" : "outline"}>
            {M.payment.viewOrder}
          </ButtonLink>
        )}
        {!success && result.order_id && (
          <Button onClick={() => retry.mutate(result.order_id!)} loading={retry.isPending}>
            {M.payment.retry}
          </Button>
        )}
        <ButtonLink href="/" variant="ghost">
          {M.payment.backHome}
        </ButtonLink>
      </div>
    </div>
  );
}
