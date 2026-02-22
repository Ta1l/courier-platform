import { useState, type ReactNode } from "react";

import { Icons } from "./Icons";

type FAQItemProps = {
  q: string;
  a: ReactNode;
};

export function FAQItem({ q, a }: FAQItemProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b border-[var(--color-border)]">
      <button
        className="flex w-full items-center justify-between gap-3 py-4 text-left text-[15px] font-semibold text-[var(--color-text)] transition-colors hover:text-[var(--color-brand)] focus:outline-none sm:text-base"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <span>{q}</span>
        <span className={`ml-2 shrink-0 transition-transform duration-200 ${open ? "rotate-180" : ""}`}>
          {Icons.chevronDown}
        </span>
      </button>
      <div className={`overflow-hidden transition-all duration-200 ${open ? "max-h-48 pb-4" : "max-h-0"}`}>
        <div className="text-sm text-[var(--color-text-secondary)] sm:text-base">{a}</div>
      </div>
    </div>
  );
}
