# Store Frontend (Next.js)

Persian (RTL) men's fashion store. Next.js 16 (App Router) + TypeScript + Tailwind CSS 4 + TanStack Query + Zustand.
API contract: [`contract/openapi.yaml`](contract/openapi.yaml) (shared with the Django backend).

## Quick start (no backend needed)

```bash
npm install
cp .env.example .env.local        # NEXT_PUBLIC_USE_MOCKS=true by default
npm run dev                       # http://localhost:3000
```

In mock mode everything works with in-memory demo data: browsing, filters, cart, login (**OTP code is always `12345`**), checkout and a fake payment gateway.

## Use the real backend

1. Start the backend (see the backend README) on `http://localhost:8000`.
2. In `.env.local` set:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   NEXT_PUBLIC_USE_MOCKS=false
   ```
3. Restart `npm run dev`. The OTP code is printed in the backend/celery logs in development.

## Scripts

| Command                              | What it does                                                          |
| ------------------------------------ | --------------------------------------------------------------------- |
| `npm run dev`                        | Dev server                                                            |
| `npm run build` / `npm start`        | Production build / server                                             |
| `npm run lint` / `npm run typecheck` | ESLint / TypeScript                                                   |
| `npm run format`                     | Prettier (with Tailwind class sorting)                                |
| `npm run gen:api`                    | Regenerate `types/api.generated.ts` from `contract/openapi.yaml`      |
| `npm run gen:api:live`               | Regenerate types from the running backend's `/api/schema/`            |
| `npm test`                           | Unit tests (Vitest + Testing Library)                                 |
| `npm run e2e`                        | Playwright end-to-end (first time: `npx playwright install chromium`) |

## How it is built

- **Auth (httpOnly cookies / BFF):** the browser never sees JWTs. `app/api/auth/*` route handlers call the backend and store
  `access_token`/`refresh_token` as httpOnly cookies. All authenticated calls go to `app/api/bff/[...path]`, which adds
  `Authorization: Bearer …`, refreshes the token on 401 (rotation) and retries once. `proxy.ts` (Next 16's middleware)
  redirects `/account/*` and `/checkout` to `/login` when there is no session.
- **Data:** public catalog data is fetched in Server Components (`lib/api/catalog.ts`) with ISR (`revalidate`).
  Cart/account/checkout use React Query on the client (`lib/api/shop.ts`).
- **Mocks:** `lib/mocks/router.ts` implements the same API in memory. `NEXT_PUBLIC_USE_MOCKS` switches between mock and real —
  no other code changes.
- **Cart:** guests use a Zustand store persisted in `localStorage` (`store/cartStore.ts`). After login the guest cart is sent to
  `POST /cart/merge/`, then the server cart is the source of truth. Prices on the client are display-only.
- **Payment:** `POST /orders/` → `POST /payments/start/` → redirect to gateway → gateway returns to `/payment/result?Authority=&Status=`
  → the page calls `GET /payments/verify/` (idempotent).
- **Installment gateways:** Digipay and SnappPay POST back to `app/api/payments/callback`, which redirects to `/payment/result`.
  The payment methods at checkout come from `GET /payments/methods/`.
- **Home page:** vertical full-height sections (Swiper, `components/home/HomeSwiper.tsx`). If the header height changes,
  update the height in that file.
- **Texts:** all UI strings are in `constants/messages.ts`; static page copy in `constants/content.ts`.
  The site name, tagline and logo come from Django admin (`GET /site-settings/`); `M.brand` / `M.tagline` are only fallbacks.
- **Font:** Vazirmatn (OFL) is bundled in `app/fonts/` via `next/font/local` (works without access to Google Fonts).

## Folder structure

```
app/(shop)/…        home, category, collection, product, search, cart, checkout, payment/result, stores, static pages
app/(account)/…     login, account (profile, orders, addresses)
app/api/…           auth + BFF route handlers
components/         ui/, layout/, home/, product/, cart/, checkout/, account/
lib/                api/, mocks/, server/, format.ts, validation.ts, env.ts
store/              cartStore.ts, uiStore.ts
hooks/              useSession.ts, useCart.ts
types/              api.generated.ts (generated), api.ts (aliases)
contract/           openapi.yaml
```

## Docker

```bash
docker build -t store-frontend \
  --build-arg NEXT_PUBLIC_API_URL=https://api.example.com/api \
  --build-arg NEXT_PUBLIC_SITE_URL=https://example.com .
docker run -p 3000:3000 -e API_URL=http://backend:8000/api store-frontend
```

## Contract changes

1. Update `contract/openapi.yaml` (same file as the backend's `contract/openapi.yaml`).
2. `npm run gen:api` — TypeScript errors show every place to update.
3. CI fails if the generated types are out of date.
