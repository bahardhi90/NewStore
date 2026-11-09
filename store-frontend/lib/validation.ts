import { z } from "zod";

import { M } from "@/constants/messages";

import { normalizePhone, toEnDigits } from "./format";

export const phoneSchema = z
  .string()
  .transform((v) => normalizePhone(v))
  .pipe(z.string().regex(/^09\d{9}$/, M.auth.invalidPhone));

export const otpCodeSchema = z
  .string()
  .transform((v) => toEnDigits(v).trim())
  .pipe(z.string().regex(/^\d{5}$/, M.auth.invalidCode));

const required = z.string().trim().min(1, M.address.required);

export const addressSchema = z.object({
  title: required.max(50),
  receiver_name: required.max(100),
  receiver_phone: phoneSchema,
  province: required.max(50),
  city: required.max(50),
  postal_code: z
    .string()
    .transform((v) => toEnDigits(v).replace(/\D/g, ""))
    .pipe(z.string().regex(/^\d{10}$/, M.address.postalInvalid)),
  address_line: required.max(500),
  is_default: z.boolean(),
});

export type AddressFormInput = z.input<typeof addressSchema>;
export type AddressFormValues = z.output<typeof addressSchema>;

export const profileSchema = z.object({
  first_name: z.string().trim().max(50),
  last_name: z.string().trim().max(50),
  email: z.union([z.literal(""), z.email("ایمیل معتبر نیست.")]),
});

export type ProfileFormValues = z.infer<typeof profileSchema>;
