"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { createClient } from "@/lib/supabase/client";
import type { AnalysisJob } from "@/lib/types";
import { Progress } from "@/components/ui/progress";

export function ProgressLive({ initial }: { initial: AnalysisJob }) {
  const [job, setJob] = useState(initial);
  const router = useRouter();

  useEffect(() => {
    const supabase = createClient();
    const channel = supabase
      .channel(`job:${initial.id}`)
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "analysis_jobs",
          filter: `id=eq.${initial.id}`,
        },
        (payload) => {
          setJob(payload.new as AnalysisJob);
        },
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [initial.id]);

  useEffect(() => {
    if (job.status === "done") {
      router.replace(`/app/analyses/${job.id}`);
    }
  }, [job.status, job.id, router]);

  const total = job.progress_moves_total || 1;
  const fraction = Math.min(1, job.progress_moves_done / total);
  const pct = (fraction * 100).toFixed(1);

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <div className="flex items-baseline justify-between">
          <h1 className="text-2xl font-bold">Analysing your games</h1>
          <span className="text-sm text-muted-foreground capitalize">{job.status}</span>
        </div>
        <p className="text-sm text-muted-foreground">
          Stockfish is reviewing every move you played. You can leave this tab open or come back later.
        </p>
      </div>

      <Progress value={fraction} className="h-3" />

      <div className="grid grid-cols-3 gap-4 text-center">
        <Stat label="Games" value={`${job.progress_games_done} / ${job.progress_games_total}`} />
        <Stat label="Moves" value={`${job.progress_moves_done} / ${job.progress_moves_total}`} />
        <Stat label="Progress" value={`${pct}%`} highlight />
      </div>

      {job.status === "failed" && job.error_message && (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          <strong>Failed:</strong> {job.error_message}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</div>
      <motion.div
        key={value}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className={`mt-1 text-xl font-bold tabular-nums ${highlight ? "text-primary" : ""}`}
      >
        {value}
      </motion.div>
    </div>
  );
}
