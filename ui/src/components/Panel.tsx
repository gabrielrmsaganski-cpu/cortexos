import type { ReactNode } from "react";

import { cn } from "../lib/format";

export function Panel({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "rounded-3xl border border-edge bg-panel/90 p-5 shadow-panel backdrop-blur",
        className,
      )}
    >
      {children}
    </section>
  );
}
