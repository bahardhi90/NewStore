import { forwardRef, useId, type ComponentProps, type ReactNode } from "react";

import { cn } from "@/lib/utils";

type InputProps = ComponentProps<"input"> & {
  label?: string;
  error?: string;
  hint?: ReactNode;
  ltr?: boolean;
};

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input({ label, error, hint, ltr, className, id, ...rest }, ref) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const describedBy = error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined;
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-ink-soft text-sm font-medium">
          {label}
        </label>
      )}
      <input
        ref={ref}
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={cn(
          "bg-surface text-ink placeholder:text-muted/70 h-11 w-full rounded-lg border px-3 text-sm transition-colors",
          "focus:border-ink focus:outline-none",
          error ? "border-sale" : "border-line",
          ltr && "text-left [direction:ltr] placeholder:text-right",
          className,
        )}
        {...rest}
      />
      {error ? (
        <p id={`${inputId}-error`} className="text-sale text-xs">
          {error}
        </p>
      ) : hint ? (
        <p id={`${inputId}-hint`} className="text-muted text-xs">
          {hint}
        </p>
      ) : null}
    </div>
  );
});

type TextareaProps = ComponentProps<"textarea"> & { label?: string; error?: string };

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea({ label, error, className, id, ...rest }, ref) {
  const autoId = useId();
  const inputId = id ?? autoId;
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-ink-soft text-sm font-medium">
          {label}
        </label>
      )}
      <textarea
        ref={ref}
        id={inputId}
        aria-invalid={error ? true : undefined}
        className={cn(
          "bg-surface focus:border-ink min-h-24 w-full rounded-lg border p-3 text-sm focus:outline-none",
          error ? "border-sale" : "border-line",
          className,
        )}
        {...rest}
      />
      {error && <p className="text-sale text-xs">{error}</p>}
    </div>
  );
});
