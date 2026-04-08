import type { ReactNode } from "react";

import { cn, statusTone } from "../lib/format";

export function Badge({
  children,
  tone,
}: {
  children: ReactNode;
  tone?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.18em]",
        tone ?? "bg-white/10 text-slate-200",
      )}
    >
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  return <Badge tone={statusTone(status)}>{status}</Badge>;
}
