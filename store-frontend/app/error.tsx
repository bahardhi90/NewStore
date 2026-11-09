"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/Button";
import { M } from "@/constants/messages";

/** Error boundary for all routes under the root layout. */
export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="container-page flex flex-col items-center gap-4 py-24 text-center">
      <h1 className="text-2xl font-bold">{M.errors.generic}</h1>
      <p className="text-muted text-sm">{M.errors.network}</p>
      <Button onClick={reset}>{M.errors.tryAgain}</Button>
    </div>
  );
}
