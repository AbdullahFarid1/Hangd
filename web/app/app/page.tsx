import Link from "next/link";
import { ArrowRight, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { listJobs } from "@/lib/queries";
import { Progress } from "@/components/ui/progress";

const STATUS_BADGE: Record<string, string> = {
  queued: "bg-muted text-muted-foreground",
  running: "bg-inaccuracy/15 text-inaccuracy",
  done: "bg-ok/15 text-ok",
  failed: "bg-destructive/15 text-destructive",
};

export default async function DashboardHubPage() {
  const jobs = await listJobs();

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Your analyses</h1>
          <p className="text-muted-foreground">
            Every PGN bundle you've uploaded, with its analysis state.
          </p>
        </div>
        <Link href="/app/upload">
          <Button>
            <Plus className="h-4 w-4" />
            New analysis
          </Button>
        </Link>
      </div>

      {jobs.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-center">
            <span className="text-3xl">♞</span>
            <p className="text-lg font-medium">No analyses yet</p>
            <p className="max-w-sm text-sm text-muted-foreground">
              Upload your White and Black PGN files to get your first dashboard.
            </p>
            <Link href="/app/upload">
              <Button>
                <Plus className="h-4 w-4" />
                Upload PGNs
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3">
          {jobs.map((job) => {
            const fraction = (job.progress_moves_total || 0) === 0
              ? 0
              : job.progress_moves_done / job.progress_moves_total;
            const href =
              job.status === "done"
                ? `/app/analyses/${job.id}`
                : `/app/jobs/${job.id}`;
            return (
              <Link key={job.id} href={href}>
                <Card className="transition-colors hover:border-primary/40">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">
                        {new Date(job.created_at).toLocaleString()}
                      </CardTitle>
                      <span
                        className={`rounded-md px-2 py-0.5 text-xs font-medium capitalize ${STATUS_BADGE[job.status]}`}
                      >
                        {job.status}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-4">
                      <div className="flex-1">
                        <Progress value={fraction} />
                        <div className="mt-1 text-xs text-muted-foreground">
                          {job.progress_moves_done} / {job.progress_moves_total} moves
                          {job.progress_games_total > 0 &&
                            ` · ${job.progress_games_done} / ${job.progress_games_total} games`}
                        </div>
                      </div>
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
