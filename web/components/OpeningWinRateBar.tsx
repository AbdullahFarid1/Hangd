"use client";

import { motion } from "framer-motion";
import type { RepertoireRow } from "@/lib/types";
import { formatPercent } from "@/lib/utils";

export function OpeningWinRateBar({ row, index = 0 }: { row: RepertoireRow; index?: number }) {
  const total = row.total || 1;
  const win = (row.win / total) * 100;
  const draw = (row.draw / total) * 100;
  const loss = (row.loss / total) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03 }}
      className="grid grid-cols-[minmax(140px,2fr)_3fr_minmax(80px,auto)] items-center gap-3"
    >
      <div className="min-w-0">
        <div className="truncate text-sm font-medium" title={row.opening_name}>
          {row.opening_name || "(no opening tag)"}
        </div>
        <div className="text-[11px] text-muted-foreground">
          {row.eco} · {row.total} games
        </div>
      </div>
      <div className="flex h-3 w-full overflow-hidden rounded-full border border-border">
        <div className="bg-ok h-full" style={{ width: `${win}%` }} title={`${row.win} wins`} />
        <div
          className="bg-muted-foreground/50 h-full"
          style={{ width: `${draw}%` }}
          title={`${row.draw} draws`}
        />
        <div className="bg-blunder h-full" style={{ width: `${loss}%` }} title={`${row.loss} losses`} />
      </div>
      <div className="text-right text-sm tabular-nums">{formatPercent(row.win_rate)}</div>
    </motion.div>
  );
}
