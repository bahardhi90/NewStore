"use client";

/** Last-resort error boundary (when the root layout itself fails). */
export default function GlobalError({ reset }: { error: Error; reset: () => void }) {
  return (
    <html lang="fa" dir="rtl">
      <body style={{ fontFamily: "system-ui, sans-serif", textAlign: "center", padding: "6rem 1rem" }}>
        <h1>خطایی رخ داد.</h1>
        <p>لطفاً صفحه را دوباره بارگذاری کنید.</p>
        <button type="button" onClick={reset} style={{ padding: "0.75rem 1.5rem", marginTop: "1rem" }}>
          تلاش مجدد
        </button>
      </body>
    </html>
  );
}
