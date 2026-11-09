"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { M } from "@/constants/messages";
import { CART_KEY } from "@/hooks/useCart";
import { SESSION_KEY } from "@/hooks/useSession";
import { isApiError } from "@/lib/api/errors";
import { authApi, cartApi, meApi } from "@/lib/api/shop";
import { USE_MOCKS } from "@/lib/env";
import { formatCountdown, toFaDigits } from "@/lib/format";
import { otpCodeSchema, phoneSchema } from "@/lib/validation";
import { useGuestCart } from "@/store/cartStore";
import { toast } from "@/store/uiStore";

type Step = "phone" | "code" | "profile";

/** Only allow redirects to internal paths. */
function safeNext(value: string | null): string {
  return value && value.startsWith("/") && !value.startsWith("//") ? value : "/account";
}

export function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const queryClient = useQueryClient();
  const next = safeNext(params.get("next"));

  const [step, setStep] = useState<Step>("phone");
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [resendAt, setResendAt] = useState(0);
  const [now, setNow] = useState(() => Date.now());
  const [names, setNames] = useState({ first_name: "", last_name: "" });

  useEffect(() => {
    if (step !== "code") return;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [step]);
  const secondsLeft = Math.max(0, Math.ceil((resendAt - now) / 1000));

  async function sendCode(event?: FormEvent) {
    event?.preventDefault();
    const parsed = phoneSchema.safeParse(phone);
    if (!parsed.success) {
      setError(parsed.error.issues[0].message);
      return;
    }
    setError(undefined);
    setLoading(true);
    try {
      const res = await authApi.requestOtp(parsed.data);
      setPhone(parsed.data);
      setResendAt(Date.now() + res.resend_in * 1000);
      setNow(Date.now());
      setStep("code");
      toast.info(res.detail);
    } catch (e) {
      setError(isApiError(e) ? e.allMessages()[0] : M.errors.generic);
    } finally {
      setLoading(false);
    }
  }

  async function verify(event: FormEvent) {
    event.preventDefault();
    const parsed = otpCodeSchema.safeParse(code);
    if (!parsed.success) {
      setError(parsed.error.issues[0].message);
      return;
    }
    setError(undefined);
    setLoading(true);
    try {
      const { user, is_new } = await authApi.verifyOtp(phone, parsed.data);
      queryClient.setQueryData(SESSION_KEY, user);

      // Merge the guest cart (localStorage) into the server cart.
      const guestLines = useGuestCart.getState().lines;
      if (guestLines.length) {
        try {
          const cart = await cartApi.merge(guestLines.map((l) => ({ variant_id: l.variant.id, quantity: l.quantity })));
          queryClient.setQueryData(CART_KEY, cart);
          (cart.warnings ?? []).forEach((w) => toast.info(w));
        } finally {
          useGuestCart.getState().clear();
        }
      }
      await queryClient.invalidateQueries({ queryKey: CART_KEY });

      toast.success(M.auth.welcome);
      if (is_new || !user.first_name) setStep("profile");
      else router.replace(next);
    } catch (e) {
      setError(isApiError(e) ? e.allMessages()[0] : M.errors.generic);
    } finally {
      setLoading(false);
    }
  }

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    try {
      const user = await meApi.update(names);
      queryClient.setQueryData(SESSION_KEY, user);
    } catch {
      // optional step: ignore errors and continue
    } finally {
      setLoading(false);
      router.replace(next);
    }
  }

  if (step === "phone") {
    return (
      <form onSubmit={sendCode} className="flex flex-col gap-4" noValidate>
        <Input
          label={M.auth.phoneLabel}
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          placeholder={M.auth.phonePlaceholder}
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          error={error}
          hint={M.auth.phoneHint}
          ltr
          autoFocus
        />
        <Button type="submit" size="lg" loading={loading}>
          {M.auth.sendCode}
        </Button>
      </form>
    );
  }

  if (step === "code") {
    return (
      <form onSubmit={verify} className="flex flex-col gap-4" noValidate>
        <p className="text-muted text-sm">{M.auth.codeSentTo(toFaDigits(phone))}</p>
        {USE_MOCKS && <p className="bg-brand-soft text-brand rounded-lg p-2 text-xs">{M.auth.mockHint}</p>}
        <Input
          label={M.auth.codeLabel}
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={5}
          value={code}
          onChange={(e) => setCode(e.target.value)}
          error={error}
          ltr
          autoFocus
          className="text-center text-lg tracking-[0.5em]"
        />
        <Button type="submit" size="lg" loading={loading}>
          {M.auth.verify}
        </Button>
        <div className="flex items-center justify-between text-sm">
          <button
            type="button"
            className="text-brand hover:underline"
            onClick={() => {
              setStep("phone");
              setCode("");
              setError(undefined);
            }}
          >
            {M.auth.editPhone}
          </button>
          {secondsLeft > 0 ? (
            <span className="text-muted">{M.auth.resendIn(formatCountdown(secondsLeft))}</span>
          ) : (
            <button type="button" className="text-brand hover:underline" onClick={() => sendCode()} disabled={loading}>
              {M.auth.resend}
            </button>
          )}
        </div>
      </form>
    );
  }

  return (
    <form onSubmit={saveProfile} className="flex flex-col gap-4">
      <p className="text-muted text-sm">{M.auth.completeProfile}</p>
      <Input
        label={M.account.firstName}
        value={names.first_name}
        onChange={(e) => setNames({ ...names, first_name: e.target.value })}
        autoFocus
      />
      <Input label={M.account.lastName} value={names.last_name} onChange={(e) => setNames({ ...names, last_name: e.target.value })} />
      <Button type="submit" size="lg" loading={loading}>
        {M.account.save}
      </Button>
    </form>
  );
}
