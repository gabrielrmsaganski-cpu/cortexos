import { Panel } from "./Panel";

export function EmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <Panel className="border-dashed">
      <h3 className="font-display text-xl text-white">{title}</h3>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">{description}</p>
    </Panel>
  );
}
