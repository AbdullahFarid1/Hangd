"use client";

import { motion } from "framer-motion";
import type { PhaseSummaryRow } from "@/lib/types";
import { formatPercent } from "@/lib/utils";

interface PhaseRingProps {
  rows: PhaseSummaryRow[];
  size?: number;
}

const COLORS: Record<string, string> = {
  opening: "hsl(40 90% 60%)",
  middlegame: "hsl(28 70% 55%)",
  endgame: "hsl(0 70% 55%)",
};

const PHASES: PhaseSummaryRow["phase"][] = ["opening", "middlegame", "endgame"];

export function PhaseRing({ rows, size = 220 }: PhaseRingProps) {
  const center = size / 2;
  const ringWidth = 14;
  const gap = 6;
  const ringByPhase = Object.fromEntries(rows.map((r) => [r.phase, r])) as Record<string, PhaseSummaryRow>;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-label="Phase win rates">
      {PHASES.map((phase, i) => {
        const row = ringByPhase[phase];
        const winRate = row?.win_rate ?? 0;
        const radius = center - ringWidth / 2 - i * (ringWidth + gap);
        const circumference = 2 * Math.PI * radius;
        const dashArray = circumference;
        return (
          <g key={phase} transform={`rotate(-90 ${center} ${center})`}>
            <circle
              cx={center}
              cy={center}
              r={radius}
              stroke="hsl(var(--muted))"
              strokeWidth={ringWidth}
              fill="transparent"
            />
            <motion.circle
              cx={center}
              cy={center}
              r={radius}
              stroke={COLORS[phase]}
              strokeWidth={ringWidth}
              fill="transparent"
              strokeLinecap="round"
              strokeDasharray={dashArray}
              initial={{ strokeDashoffset: dashArray }}
              animate={{ strokeDashoffset: dashArray * (1 - (winRate ?? 0)) }}
              transition={{ duration: 1, ease: "easeOut", delay: 0.1 * i }}
            />
          </g>
        );
      })}

      {/* Centre legend */}
      <g>
        {PHASES.map((phase, i) => {
          const row = ringByPhase[phase];
          return (
            <text
              key={phase}
              x={center}
              y={center - 18 + i * 18}
              textAnchor="middle"
              className="fill-foreground"
              style={{ fontSize: 11, fontFamily: "Inter, sans-serif" }}
            >
              <tspan style={{ fill: COLORS[phase] }}>●</tspan>{" "}
              {phase[0]?.toUpperCase()}
              {phase.slice(1)}: {formatPercent(row?.win_rate ?? null)}
            </text>
          );
        })}
      </g>
    </svg>
  );
}
