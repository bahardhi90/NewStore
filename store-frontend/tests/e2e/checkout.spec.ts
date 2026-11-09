import { expect, test } from "@playwright/test";

/** Main flow in mock mode: browse -> add to cart -> login (OTP 12345) -> checkout -> fake gateway -> result. */
test("browse, add to cart, login, checkout and pay", async ({ page }) => {
  await page.goto("/category/jackets");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("کاپشن و جلیقه");

  await page.locator("article a").first().click();
  await expect(page).toHaveURL(/\/product\//);

  // pick the first available size
  const sizeButtons = page.locator("fieldset").nth(1).getByRole("button", { disabled: false });
  await sizeButtons.first().click();
  await page.getByRole("button", { name: "افزودن به سبد خرید" }).click();
  await expect(page.getByText("به سبد خرید اضافه شد.")).toBeVisible();

  await page.goto("/cart");
  await page.getByRole("button", { name: "ادامه فرایند خرید" }).click();

  // login
  await expect(page).toHaveURL(/\/login/);
  await page.getByLabel("شماره موبایل").fill("09121234567");
  await page.getByRole("button", { name: "دریافت کد تأیید" }).click();
  await page.getByLabel("کد تأیید").fill("12345");
  await page.getByRole("button", { name: "ورود", exact: true }).click();

  // new user -> profile step
  await page.getByLabel("نام", { exact: true }).fill("علی");
  await page.getByRole("button", { name: "ذخیره تغییرات" }).click();
  await expect(page).toHaveURL(/\/checkout/);

  // address
  await page.getByLabel("عنوان آدرس (مثلاً خانه)").fill("خانه");
  await page.getByLabel("نام و نام خانوادگی گیرنده").fill("علی رضایی");
  await page.getByLabel("موبایل گیرنده").fill("09121234567");
  await page.getByLabel("شهر").fill("تهران");
  await page.getByLabel("کد پستی (۱۰ رقم)").fill("1234567890");
  await page.getByLabel("نشانی کامل").fill("خیابان ولیعصر، پلاک ۱");
  await page.getByRole("button", { name: "ذخیره تغییرات" }).click();

  await page.getByRole("button", { name: "مرحله بعد" }).click(); // -> shipping
  await page.getByRole("button", { name: "مرحله بعد" }).click(); // -> review
  await page.getByRole("button", { name: "مرحله بعد" }).click(); // -> pay
  await page.getByRole("button", { name: "ثبت سفارش و پرداخت" }).click();

  await expect(page).toHaveURL(/\/payment\/result/);
  await expect(page.getByRole("heading", { name: "پرداخت موفق" })).toBeVisible();
});
