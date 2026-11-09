"use client";

import { useId, useState, type ReactNode } from "react";

import { M } from "@/constants/messages";
import { cn } from "@/lib/utils";

/** `shippingPoints` come from admin (site settings); the tab is hidden when there are none. */
export function ProductTabs({ description, shippingPoints }: { description: string; shippingPoints: string[] }) {
  const id = useId();
  const tabs: { key: string; label: string; content: ReactNode }[] = [
    { key: "description", label: M.product.description, content: <p className="leading-8 whitespace-pre-line">{description}</p> },
  ];
  if (shippingPoints.length > 0) {
    tabs.push({
      key: "shipping",
      label: M.product.shipping,
      content: (
        <ul className="list-disc space-y-2 ps-5 leading-7">
          {shippingPoints.map((point, i) => (
            <li key={i}>{point}</li>
          ))}
        </ul>
      ),
    });
  }
  const [active, setActive] = useState(tabs[0].key);

  return (
    <div>
      <div role="tablist" className="border-line flex gap-6 border-b">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            id={`${id}-${tab.key}-tab`}
            role="tab"
            type="button"
            aria-selected={active === tab.key}
            aria-controls={`${id}-${tab.key}-panel`}
            onClick={() => setActive(tab.key)}
            className={cn(
              "-mb-px border-b-2 py-3 text-sm font-medium",
              active === tab.key ? "border-ink text-ink" : "text-muted hover:text-ink border-transparent",
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {tabs.map((tab) => (
        <div
          key={tab.key}
          id={`${id}-${tab.key}-panel`}
          role="tabpanel"
          aria-labelledby={`${id}-${tab.key}-tab`}
          hidden={active !== tab.key}
          className="text-ink-soft py-5 text-sm"
        >
          {tab.content}
        </div>
      ))}
    </div>
  );
}
