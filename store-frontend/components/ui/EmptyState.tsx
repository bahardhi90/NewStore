import type { ReactNode } from "react";

export function EmptyState({ title, text, action, icon }: { title: string; text?: string; action?: ReactNode; icon?: ReactNode }) {
  return (
    <div className="rounded-card border-line flex flex-col items-center justify-center gap-3 border border-dashed px-6 py-16 text-center">
      {icon && <div className="text-muted">{icon}</div>}
      <p className="text-lg font-bold">{title}</p>
      {text && <p className="text-muted max-w-md text-sm leading-7">{text}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
