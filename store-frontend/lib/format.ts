const FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹";
const AR_DIGITS = "٠١٢٣٤٥٦٧٨٩";

const numberFormatter = new Intl.NumberFormat("fa-IR");

/** 1250000 -> "۱٬۲۵۰٬۰۰۰ تومان" */
export function formatPrice(amount: number, withUnit = true): string {
  const value = numberFormatter.format(Math.round(amount));
  return withUnit ? `${value} تومان` : value;
}

export function formatNumber(value: number): string {
  return numberFormatter.format(value);
}

/** Convert English digits inside any string to Persian digits. */
export function toFaDigits(value: string | number): string {
  return String(value).replace(/\d/g, (d) => FA_DIGITS[Number(d)]);
}

/** Convert Persian/Arabic digits to English (use before sending input to the API). */
export function toEnDigits(value: string): string {
  return value.replace(/[۰-۹]/g, (d) => String(FA_DIGITS.indexOf(d))).replace(/[٠-٩]/g, (d) => String(AR_DIGITS.indexOf(d)));
}

/** "09121234567" with Persian digits accepted; returns English digits or the cleaned input. */
export function normalizePhone(value: string): string {
  let phone = toEnDigits(value).replace(/[\s\-()]/g, "");
  if (phone.startsWith("+98")) phone = `0${phone.slice(3)}`;
  else if (phone.startsWith("0098")) phone = `0${phone.slice(4)}`;
  else if (/^9\d{9}$/.test(phone)) phone = `0${phone}`;
  return phone;
}

const dateFormatter = new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
  year: "numeric",
  month: "long",
  day: "numeric",
  timeZone: "Asia/Tehran",
});
const dateTimeFormatter = new Intl.DateTimeFormat("fa-IR-u-ca-persian", {
  year: "numeric",
  month: "long",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "Asia/Tehran",
});

/** ISO date -> "۸ آبان ۱۴۰۵" */
export function formatJalaliDate(iso: string | null | undefined, withTime = false): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return (withTime ? dateTimeFormatter : dateFormatter).format(date);
}

export function formatPercent(value: number): string {
  return `${toFaDigits(value)}٪`;
}

/** mm:ss in Persian digits for countdowns */
export function formatCountdown(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  const mm = String(Math.floor(s / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  return toFaDigits(`${mm}:${ss}`);
}
