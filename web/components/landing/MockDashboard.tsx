"use client";

import { motion } from "framer-motion";
import { AlertOctagon, BarChart3, Repeat, Sparkles } from "lucide-react";

const PHASES = [
  { name: "Opening", value: 0.62, color: "hsl(40 90% 60%)" },
  { name: "Middlegame", value: 0.41, color: "hsl(28 70% 55%)" },
  { name: "Endgame", value: 0.48, color: "hsl(0 70% 55%)" },
];

const HEATMAP_DATA = Array.from({ length: 30 }, (_, i) => ({
  blunder: Math.max(0, Math.sin(i / 4) * 0.4 + Math.random() * 0.5),
  mistake: Math.max(0, Math.cos(i / 3) * 0.5 + Math.random() * 0.4),
  inaccuracy: Math.random() * 0.6 + 0.2,
}));

const REPEATS = [
  { move: "4. Bg5", side: "White", count: 37, kind: "blunder" },
  { move: "9. O-O", side: "Black", count: 18, kind: "blunder" },
  { move: "12. Nf3", side: "White", count: 14, kind: "mistake" },
];

export function MockDashboard() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.8, ease: "easeOut" }}
      className="relative mx-auto max-w-5xl"
    >
      {/* Glow underneath */}
      <div
        aria-hidden
        className="absolute -inset-12 -z-10 rounded-[3rem] blur-3xl"
        style={{
          background:
            "radial-gradient(60% 50% at 50% 50%, hsl(var(--primary) / 0.18), transparent 70%)",
        }}
      />

      <div className="overflow-hidden rounded-2xl border border-border bg-card/80 backdrop-blur shadow-2xl">
        {/* Fake browser chrome */}
        <div className="flex items-center gap-2 border-b border-border bg-background/60 px-4 py-2">
          <div className="flex gap-1.5">
            <div className="h-2.5 w-2.5 rounded-full bg-blunder/70" />
            <div className="h-2.5 w-2.5 rounded-full bg-inaccuracy/70" />
            <div className="h-2.5 w-2.5 rounded-full bg-ok/70" />
          </div>
          <div className="ml-2 flex-1 text-center text-[11px] text-muted-foreground font-mono">
            hangd.app/app/analyses/sample
          </div>
        </div>

        {/* Dashboard body */}
        <div className="p-6 space-y-6">
          {/* KPI strip */}
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <KpiPreview label="Games" value="1,204" icon={BarChart3} />
            <KpiPreview label="Blunders" value="312" icon={AlertOctagon} accent="text-blunder" />
            <KpiPreview label="Mistakes" value="987" accent="text-mistake" />
            <KpiPreview label="Inaccuracies" value="2,142" accent="text-inaccuracy" />
          </div>

          <div className="grid gap-6 md:grid-cols-[260px_1fr]">
            {/* Phase ring */}
            <div className="rounded-xl border border-border bg-background/60 p-4">
              <div className="mb-3 flex items-center gap-2 text-sm font-medium">
                <Sparkles className="h-3.5 w-3.5 text-primary" />
                Win rate by phase
              </div>
              <div className="space-y-3">
                {PHASES.map((p, i) => (
                  <div key={p.name}>
                    <div className="mb-1 flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">{p.name}</span>
                      <span className="font-mono">{(p.value * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                      <motion.div
                        initial={{ width: 0 }}
                        whileInView={{ width: `${p.value * 100}%` }}
                        viewport={{ once: true }}
                        transition={{ duration: 1, delay: 0.2 + i * 0.15, ease: "easeOut" }}
                        className="h-full rounded-full"
                        style={{ background: p.color }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Heatmap */}
            <div className="rounded-xl border border-border bg-background/60 p-4">
              <div className="mb-3 text-sm font-medium">When you err in a game</div>
              <div className="space-y-1">
                {(["blunder", "mistake", "inaccuracy"] as const).map((kind, row) => (
                  <div key={kind} className="flex gap-px">
                    {HEATMAP_DATA.map((d, i) => {
                      const v = d[kind];
                      return (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, scale: 0.5 }}
                          whileInView={{ opacity: 1, scale: 1 }}
                          viewport={{ once: true }}
                          transition={{ delay: i * 0.012 + row * 0.06, duration: 0.18 }}
                          className="h-4 flex-1 rounded-sm"
                          style={{
                            background:
                              kind === "blunder"
                                ? `hsl(0 70% 55% / ${0.15 + v * 0.7})`
                                : kind === "mistake"
                                  ? `hsl(28 90% 55% / ${0.15 + v * 0.7})`
                                  : `hsl(48 90% 55% / ${0.15 + v * 0.7})`,
                          }}
                        />
                      );
                    })}
                  </div>
                ))}
              </div>
              <div className="mt-2 flex justify-between text-[10px] text-muted-foreground">
                <span>Move 1</span>
                <span>15</span>
                <span>30</span>
              </div>
            </div>
          </div>

          {/* Repeat offenders */}
          <div className="rounded-xl border border-border bg-background/60 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-medium">
              <Repeat className="h-3.5 w-3.5 text-primary" />
              You keep making these
            </div>
            <div className="grid gap-2 md:grid-cols-3">
              {REPEATS.map((r, i) => (
                <motion.div
                  key={r.move}
                  initial={{ opacity: 0, x: -10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.2 + i * 0.1 }}
                  className="flex items-center justify-between rounded-md border border-border bg-card px-3 py-2"
                >
                  <div>
                    <div className="font-mono text-sm">{r.move}</div>
                    <div className="text-[11px] text-muted-foreground">As {r.side}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold tabular-nums">{r.count}</div>
                    <div className="text-[10px] text-muted-foreground capitalize">{r.kind}s</div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function KpiPreview({
  label,
  value,
  icon: Icon,
  accent,
}: {
  label: string;
  value: string;
  icon?: typeof BarChart3;
  accent?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-background/60 p-3">
      <div className="flex items-center justify-between">
        <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
          {label}
        </span>
        {Icon && <Icon className={`h-3.5 w-3.5 ${accent ?? "text-primary"}`} />}
      </div>
      <div className={`mt-1 text-xl font-bold tabular-nums ${accent ?? "text-foreground"}`}>
        {value}
      </div>
    </div>
  );
}
