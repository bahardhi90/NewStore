import type { Metadata } from "next";
import { Suspense } from "react";

import { LoginForm } from "@/components/account/LoginForm";
import { M } from "@/constants/messages";

export const metadata: Metadata = { title: M.auth.title, robots: { index: false } };

export default function LoginPage() {
  return (
    <div className="container-page flex justify-center py-12">
      <div className="rounded-card bg-surface ring-line w-full max-w-md p-6 ring-1 sm:p-8">
        <h1 className="mb-6 text-xl font-black">{M.auth.title}</h1>
        <Suspense>
          <LoginForm />
        </Suspense>
      </div>
    </div>
  );
}
