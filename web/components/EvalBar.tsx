"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface EvalBarProps {
  /** Centipawn evaluation from White's POV. Positive = White is winning. */
  cp: number;
  className?: string;
  height?: number;
}

/** Map a cp value to 0..1 along the bar where 0.5 is even. */
function cpToFraction(cp: number) {
  // Logistic-ish curve: capped, with diminishing returns past ±400 cp.
  const k = 0.004;
  const x = 1 / (1 + Math.exp(-k * cp));
  return Math.max(0.02, Math.min(0.98, x));
}

export function EvalBar({ cp, className, height = 240 }: EvalBarProps) {
  const fraction = cpToFraction(cp);
  const whitePct = fraction * 100;
  const display = (cp / 100).toFixed(1);

  return (
    <div
      className={cn(
        "relative flex w-6 flex-col overflow-hidden rounded-md border border-border bg-black",
        className,
      )}
      style={{ height }}
      aria-label={`Engine evaluation: ${display}`}
    >
      <motion.div
        className="absolute bottom-0 left-0 right-0 bg-cream"
        initial={{ height: "50%" }}
        animate={{ height: `${whitePct}%` }}
        transition={{ type: "spring", stiffness: 70, damping: 18 }}
      />
      <span
        className={cn(
          "relative z-10 mx-auto mt-1 px-1 text-[10px] font-mono",
          cp >= 0 ? "self-start text-black" : "self-end mt-auto mb-1 text-cream",
        )}
      >
        {cp >= 0 ? `+${display}` : display}
      </span>
    </div>
  );
}
