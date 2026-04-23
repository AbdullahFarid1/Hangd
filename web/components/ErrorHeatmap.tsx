"use client";

import { motion } from "framer-motion";
import type { HeatmapRow, ErrorLabel } from "@/lib/types";
import { cn } from "@/lib/utils";

interface ErrorHeatmapProps {
  rows: HeatmapRow[];
  maxMove?: number;
}

const ERROR_TYPES: ErrorLabel[] = ["blunder", "mistake", "inaccuracy"];
const COLOR_BY_TYPE: Record<ErrorLabel, string> = {
  blunder: "0 70% 55%",
  mistake: "28 90% 55%",
  inaccuracy: "48 90% 55%",
  ok: "150 50% 45%",
};

export function ErrorHeatmap({ rows, maxMove = 60 }: ErrorHeatmapProps) {
  const grid = new Map<string, number>();
  let maxCount = 1;
  for (const row of rows) {
    grid.set(`${row.move_number}:${row.error_type}`, row.count);
    if (row.count > maxCount) maxCount = row.count;
  }

  const moves = Array.from({ length: maxMove }, (_, i) => i + 1);

  return (
    <div className="space-y-2">
      <div className="flex items-end gap-1">
        {/* y-axis labels */}
        <div className="flex flex-col text-xs text-muted-foreground gap-1 mr-1">
          {ERROR_TYPES.map((t) => (
            <div key={t} className="h-4 flex items-center capitalize">
              {t}
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-1 overflow-x-auto pb-2">
          {ERROR_TYPES.map((errorType) => (
            <div key={errorType} className="flex gap-px">
              {moves.map((m) => {
                const count = grid.get(`${m}:${errorType}`) ?? 0;
                const intensity = count === 0 ? 0 : 0.15 + 0.85 * (count / maxCount);
                return (
                  <motion.div
                    key={m}
                    initial={{ opacity: 0, scale: 0.6 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: m * 0.005, duration: 0.2 }}
                    className={cn("h-4 w-4 rounded-sm border border-border/40")}
                    style={{
                      background:
                        count === 0
                          ? "hsl(var(--muted))"
                          : `hsl(${COLOR_BY_TYPE[errorType]} / ${intensity})`,
                    }}
                    title={`Move ${m} · ${errorType}: ${count}`}
                  />
                );
              })}
            </div>
          ))}
        </div>
      </div>

      <div className="ml-12 flex justify-between text-[10px] text-muted-foreground">
        <span>1</span>
        <span>{Math.floor(maxMove / 2)}</span>
        <span>{maxMove}</span>
      </div>
    </div>
  );
}
