import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPercent(value: number | null | undefined, digits = 1) {
  if (value == null || Number.isNaN(value)) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatNumber(value: number | null | undefined) {
  if (value == null) return "—";
  return new Intl.NumberFormat("en-US").format(value);
}

export function classifyError(label: string) {
  switch (label) {
    case "blunder":
      return "text-blunder bg-blunder/10 border-blunder/30";
    case "mistake":
      return "text-mistake bg-mistake/10 border-mistake/30";
    case "inaccuracy":
      return "text-inaccuracy bg-inaccuracy/10 border-inaccuracy/30";
    default:
      return "text-ok bg-ok/10 border-ok/30";
  }
}
