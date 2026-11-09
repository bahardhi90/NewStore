"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Input";
import { M } from "@/constants/messages";
import { isApiError } from "@/lib/api/errors";
import { addressSchema, type AddressFormInput, type AddressFormValues } from "@/lib/validation";
import type { Address } from "@/types/api";

const PROVINCES = [
  "تهران",
  "اصفهان",
  "فارس",
  "خراسان رضوی",
  "آذربایجان شرقی",
  "آذربایجان غربی",
  "البرز",
  "گیلان",
  "مازندران",
  "خوزستان",
  "کرمان",
  "یزد",
  "قم",
  "قزوین",
  "همدان",
  "کرمانشاه",
  "لرستان",
  "مرکزی",
  "زنجان",
  "سمنان",
  "گلستان",
  "اردبیل",
  "کردستان",
  "هرمزگان",
  "بوشهر",
  "سیستان و بلوچستان",
  "چهارمحال و بختیاری",
  "کهگیلویه و بویراحمد",
  "ایلام",
  "خراسان شمالی",
  "خراسان جنوبی",
];

type Props = {
  initial?: Address | null;
  onSubmit: (values: AddressFormValues) => Promise<unknown>;
  onCancel?: () => void;
  submitLabel?: string;
};

export function AddressForm({ initial, onSubmit, onCancel, submitLabel = M.account.save }: Props) {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<AddressFormInput, unknown, AddressFormValues>({
    resolver: zodResolver(addressSchema),
    defaultValues: {
      title: initial?.title ?? "",
      receiver_name: initial?.receiver_name ?? "",
      receiver_phone: initial?.receiver_phone ?? "",
      province: initial?.province ?? "تهران",
      city: initial?.city ?? "",
      postal_code: initial?.postal_code ?? "",
      address_line: initial?.address_line ?? "",
      is_default: initial?.is_default ?? false,
    },
  });

  const submit = handleSubmit(async (values) => {
    try {
      await onSubmit(values);
    } catch (error) {
      // Map backend field errors ({errors: {field: [...]}}) onto the form
      if (isApiError(error)) {
        for (const [field, messages] of Object.entries(error.errors)) {
          if (field in values) setError(field as keyof AddressFormInput, { message: messages[0] });
        }
      }
    }
  });

  return (
    <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2" noValidate>
      <Input label={M.address.title} {...register("title")} error={errors.title?.message} />
      <Input label={M.address.receiverName} autoComplete="name" {...register("receiver_name")} error={errors.receiver_name?.message} />
      <Input
        label={M.address.receiverPhone}
        inputMode="tel"
        autoComplete="tel"
        ltr
        {...register("receiver_phone")}
        error={errors.receiver_phone?.message}
      />
      <div className="flex flex-col gap-1.5">
        <label htmlFor="province" className="text-ink-soft text-sm font-medium">
          {M.address.province}
        </label>
        <select
          id="province"
          {...register("province")}
          className="border-line bg-surface focus:border-ink h-11 rounded-lg border px-3 text-sm focus:outline-none"
        >
          {PROVINCES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>
      <Input label={M.address.city} {...register("city")} error={errors.city?.message} />
      <Input label={M.address.postalCode} inputMode="numeric" ltr {...register("postal_code")} error={errors.postal_code?.message} />
      <div className="sm:col-span-2">
        <Textarea
          label={M.address.addressLine}
          autoComplete="street-address"
          {...register("address_line")}
          error={errors.address_line?.message}
        />
      </div>
      <label className="flex items-center gap-2 text-sm sm:col-span-2">
        <input type="checkbox" className="accent-ink size-4" {...register("is_default")} />
        {M.account.setDefault}
      </label>
      <div className="flex gap-2 sm:col-span-2">
        <Button type="submit" loading={isSubmitting}>
          {submitLabel}
        </Button>
        {onCancel && (
          <Button variant="ghost" onClick={onCancel}>
            {M.account.cancel}
          </Button>
        )}
      </div>
    </form>
  );
}
