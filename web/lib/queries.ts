import { createClient } from "@/lib/supabase/server";
import type { AnalysisJob, InsightSummary } from "@/lib/types";

export async function getCurrentUser() {
  const supabase = createClient();
  const { data } = await supabase.auth.getUser();
  return data.user;
}

export async function listJobs(): Promise<AnalysisJob[]> {
  const supabase = createClient();
  const { data } = await supabase
    .from("analysis_jobs")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(50);
  return (data ?? []) as AnalysisJob[];
}

export async function getJob(id: string): Promise<AnalysisJob | null> {
  const supabase = createClient();
  const { data } = await supabase
    .from("analysis_jobs")
    .select("*")
    .eq("id", id)
    .single();
  return (data as AnalysisJob | null) ?? null;
}

export async function getInsights(jobId: string): Promise<InsightSummary | null> {
  const supabase = createClient();
  const { data } = await supabase
    .from("insights_summary")
    .select("*")
    .eq("job_id", jobId)
    .single();
  return (data as InsightSummary | null) ?? null;
}

export async function getRepeatOffendersForJob(jobId: string) {
  const insights = await getInsights(jobId);
  return insights?.payload.repeat_offenders ?? [];
}

export async function getMoveByPly(gameJobId: string, ply: number) {
  const supabase = createClient();
  const { data } = await supabase
    .from("moves")
    .select("*, games!inner(job_id)")
    .eq("games.job_id", gameJobId)
    .eq("ply", ply)
    .limit(1)
    .single();
  return data;
}
