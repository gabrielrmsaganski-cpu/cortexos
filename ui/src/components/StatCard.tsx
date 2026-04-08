import { Panel } from "./Panel";

export function StatCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail?: string;
}) {
  return (
    <Panel className="min-h-28">
      <div className="text-[11px] uppercase tracking-[0.2em] text-muted">{label}</div>
      <div className="mt-3 font-display text-3xl font-semibold text-white">{value}</div>
      {detail ? <div className="mt-2 text-sm text-slate-300">{detail}</div> : null}
    </Panel>
  );
}
