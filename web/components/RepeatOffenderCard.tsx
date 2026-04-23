"use client";

import { motion } from "framer-motion";
import type { RepeatOffenderRow } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { classifyError, cn } from "@/lib/utils";

export function RepeatOffenderCard({ row, index = 0 }: { row: RepeatOffenderRow; index?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
    >
      <Card className="overflow-hidden">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="font-mono text-base">{row.move_san}</CardTitle>
            <span
              className={cn(
                "rounded-md border px-2 py-0.5 text-xs font-medium capitalize",
                classifyError(row.error_type),
              )}
            >
              {row.error_type}
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              As <span className="font-medium text-foreground">{row.side}</span>
            </span>
            <div className="text-right">
              <div className="text-2xl font-bold tabular-nums">{row.count}</div>
              <div className="text-[11px] text-muted-foreground">repetitions</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
