import { Activity, BrainCircuit, Database, Gauge, GitBranch, Home, Search, Settings, Sparkles, Upload, Workflow } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { cn } from "../lib/format";

const nav = [
  { to: "/", label: "Dashboard", icon: Home },
  { to: "/explorer", label: "Memory Explorer", icon: Database },
  { to: "/timeline", label: "Timeline", icon: GitBranch },
  { to: "/query", label: "Query Studio", icon: Search },
  { to: "/explain", label: "Explain Center", icon: BrainCircuit },
  { to: "/conflicts", label: "Conflict Center", icon: Workflow },
  { to: "/ingestion", label: "Ingestion", icon: Upload },
  { to: "/operations", label: "Operations", icon: Gauge },
  { to: "/evals", label: "Evaluations", icon: Activity },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppShell() {
  return (
    <div className="min-h-screen bg-ink bg-grid [background-size:36px_36px] text-white">
      <div className="mx-auto grid min-h-screen max-w-[1680px] grid-cols-1 gap-6 px-4 py-4 lg:grid-cols-[280px_1fr] lg:px-6">
        <aside className="rounded-[32px] border border-edge bg-[#081320]/95 p-5 shadow-panel">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl bg-accent/15 p-3 text-accent">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <div className="font-display text-xl font-semibold">CortexOS</div>
              <div className="text-sm text-slate-400">
                Explainable memory operating system for AI agents
              </div>
            </div>
          </div>
          <div className="mt-8 space-y-1">
            {nav.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-slate-300 transition",
                    isActive ? "bg-white/10 text-white" : "hover:bg-white/5 hover:text-white",
                  )
                }
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </NavLink>
            ))}
          </div>
          <div className="mt-8 rounded-3xl border border-white/10 bg-white/5 p-4">
            <div className="text-[11px] uppercase tracking-[0.2em] text-muted">Principles</div>
            <div className="mt-3 space-y-2 text-sm text-slate-300">
              <div>Verbatim first</div>
              <div>Hybrid retrieval</div>
              <div>Lifecycle aware</div>
              <div>Conflict explicit</div>
            </div>
          </div>
          <div className="mt-8 text-xs text-slate-500">Crafted by Gabriel Saganski</div>
        </aside>
        <main className="overflow-hidden rounded-[32px] border border-edge bg-gradient-to-br from-panel to-[#08111d] shadow-panel">
          <div className="border-b border-edge/80 px-6 py-5">
            <div className="font-display text-3xl font-semibold tracking-tight">Product Console</div>
            <div className="mt-2 max-w-4xl text-sm text-slate-300">
              Inspect memory state, retrieval paths, conflicts, operations, and demo-ready evals on top of the existing engine.
            </div>
          </div>
          <div className="p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
