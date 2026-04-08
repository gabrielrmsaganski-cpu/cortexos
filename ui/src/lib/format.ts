import { format, formatDistanceToNowStrict } from "date-fns";
import { clsx } from "clsx";

export function cn(...values: Array<string | false | null | undefined>) {
  return clsx(values);
}

export function formatNumber(value: number | undefined | null) {
  return typeof value === "number" ? new Intl.NumberFormat().format(value) : "0";
}

export function formatPct(value: number | undefined | null) {
  if (typeof value !== "number") return "0%";
  return `${Math.round(value * 100)}%`;
}

export function formatDateTime(value: string | undefined | null) {
  if (!value) return "n/a";
  return format(new Date(value), "yyyy-MM-dd HH:mm");
}

export function formatRelativeTime(value: string | undefined | null) {
  if (!value) return "n/a";
  return formatDistanceToNowStrict(new Date(value), { addSuffix: true });
}

export function clip(text: string | undefined | null, size = 120) {
  if (!text) return "";
  return text.length > size ? `${text.slice(0, size)}...` : text;
}

export function statusTone(status: string) {
  switch (status) {
    case "active":
      return "bg-success/15 text-success";
    case "superseded":
      return "bg-accentWarm/15 text-accentWarm";
    case "conflicting":
      return "bg-danger/15 text-danger";
    case "archived":
      return "bg-white/10 text-slate-300";
    default:
      return "bg-white/10 text-slate-200";
  }
}

export function healthTone(status: string) {
  return status === "ok" ? "text-success" : "text-danger";
}
