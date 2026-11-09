"use client";

import { useState } from "react";

import { Modal } from "@/components/ui/Modal";
import { M } from "@/constants/messages";
import { toFaDigits } from "@/lib/format";
import type { SizeChart } from "@/types/api";

export type SizeGuideContent = { note: string; charts: SizeChart[] };

/** Tables are managed in admin (site settings). No tables, no button. */
export function SizeGuideButton({ guide }: { guide: SizeGuideContent }) {
  const [open, setOpen] = useState(false);
  if (guide.charts.length === 0) return null;
  return (
    <>
      <button type="button" onClick={() => setOpen(true)} className="text-brand text-xs underline underline-offset-4">
        {M.product.sizeGuide}
      </button>
      <Modal open={open} onClose={() => setOpen(false)} title={M.product.sizeGuide}>
        <div className="flex flex-col gap-6 p-5 text-sm">
          {guide.note && <p className="text-muted">{guide.note}</p>}
          {guide.charts.map((chart, i) => (
            <SizeTable key={i} chart={chart} />
          ))}
        </div>
      </Modal>
    </>
  );
}

function SizeTable({ chart }: { chart: SizeChart }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-center">
        <caption className="mb-2 text-start font-bold">{chart.title}</caption>
        <thead>
          <tr className="bg-sand">
            {chart.columns.map((h, i) => (
              <th key={i} scope="col" className="p-2 font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {chart.rows.map((row, r) => (
            <tr key={r} className="border-line border-b">
              {row.map((cell, i) => (
                <td key={i} className="p-2">
                  {i === 0 && /^\d+$/.test(cell) ? toFaDigits(cell) : cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
