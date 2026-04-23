"use client";

import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface KpiTileProps {
  label: string;
  value: number | string;
  // Accepts a pre-rendered element (e.g. <AlertOctagon className="h-4 w-4" />).
  // Must NOT be a component function — server components can't serialize those across the RSC boundary.
  icon?: ReactNode;
  accent?: "blunder" | "mistake" | "inaccuracy" | "ok" | "primary";
  index?: number;
}

const ACCENT_CLASSES: Record<NonNullable<KpiTileProps["accent"]>, string> = {
  blunder: "text-blunder",
  mistake: "text-mistake",
  inaccuracy: "text-inaccuracy",
  ok: "text-ok",
  primary: "text-primary",
};

export function KpiTile({ label, value, icon, accent = "primary", index = 0 }: KpiTileProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="rounded-xl border border-border bg-card p-4"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wide text-muted-foreground">{label}</span>
        {icon && <span className={cn("inline-flex", ACCENT_CLASSES[accent])}>{icon}</span>}
      </div>
      <div className={cn("mt-2 text-2xl font-bold tabular-nums", ACCENT_CLASSES[accent])}>
        {typeof value === "number" ? new Intl.NumberFormat("en-US").format(value) : value}
      </div>
    </motion.div>
  );
}
