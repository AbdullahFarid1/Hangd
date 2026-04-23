import Link from "next/link";
import { notFound } from "next/navigation";
import { AlertOctagon, ArrowRight, BookOpen, Repeat, Sparkles, TrendingUp } from "lucide-react";
import { ErrorHeatmap } from "@/components/ErrorHeatmap";
import { KpiTile } from "@/components/KpiTile";
import { PhaseRing } from "@/components/PhaseRing";
import { RepeatOffenderCard } from "@/components/RepeatOffenderCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getInsights } from "@/lib/queries";
import { formatPercent } from "@/lib/utils";

export default async function AnalysisDashboardPage({ params }: { params: { id: string } }) {
  const insights = await getInsights(params.id);
  if (!insights) notFound();

  const { payload } = insights;
  if (payload.empty) {
    return (
      <div className="mx-auto max-w-md text-center">
        <h1 className="text-xl font-semibold">No moves were analysed</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          The PGN(s) might have been empty. Try a different upload.
        </p>
      </div>
    );
  }

  const { kpis } = payload;

  return (
    <div className="space-y-10">
      {/* KPI strip */}
      <section>
        <h1 className="mb-4 text-3xl font-bold tracking-tight">Your post-mortem</h1>
        <div className="grid gap-3 grid-cols-2 md:grid-cols-4 lg:grid-cols-7">
          <KpiTile label="Games" value={kpis.total_games} index={0} />
          <KpiTile label="Moves analysed" value={kpis.total_moves} index={1} />
          <KpiTile label="Total errors" value={kpis.total_errors} index={2} icon={<AlertOctagon className="h-4 w-4" />} />
          <KpiTile label="Blunders" value={kpis.blunders} accent="blunder" index={3} />
          <KpiTile label="Mistakes" value={kpis.mistakes} accent="mistake" index={4} />
          <KpiTile label="Inaccuracies" value={kpis.inaccuracies} accent="inaccuracy" index={5} />
          <KpiTile
            label="Stability"
            value={`${kpis.stability_score.toFixed(1)} cp`}
            accent="ok"
            index={6}
          />
        </div>
      </section>

      {/* Phase performance */}
      <section className="grid gap-6 lg:grid-cols-[auto_1fr]">
        <Card className="lg:w-[280px]">
          <CardHeader>
            <CardTitle>Win rate by phase</CardTitle>
          </CardHeader>
          <CardContent className="flex justify-center">
            <PhaseRing rows={payload.phase_summary} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              Training prescription
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
              {payload.combined_prescription}
            </pre>
          </CardContent>
        </Card>
      </section>

      {/* Error heatmap */}
      <section>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              When in the game you err
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ErrorHeatmap rows={payload.heatmap} />
          </CardContent>
        </Card>
      </section>

      {/* Repeat offenders preview */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Repeat className="h-4 w-4 text-primary" />
            You keep making these
          </h2>
          <Link href={`/app/analyses/${params.id}/repeats`}>
            <Button variant="ghost" size="sm">
              See all
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {payload.repeat_offenders.slice(0, 6).map((row, i) => (
            <RepeatOffenderCard key={`${row.side}-${row.move_san}-${i}`} row={row} index={i} />
          ))}
        </div>
      </section>

      {/* Quick links */}
      <section className="grid gap-4 sm:grid-cols-2">
        <Link href={`/app/analyses/${params.id}/openings`}>
          <Card className="h-full transition-colors hover:border-primary/40">
            <CardContent className="flex items-center justify-between p-6">
              <div>
                <div className="flex items-center gap-2 text-lg font-semibold">
                  <BookOpen className="h-4 w-4 text-primary" />
                  Opening repertoire
                </div>
                <p className="text-sm text-muted-foreground">
                  Win rates per opening you played, with avg cp drop.
                </p>
              </div>
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
            </CardContent>
          </Card>
        </Link>
        <Link href={`/app/analyses/${params.id}/repeats`}>
          <Card className="h-full transition-colors hover:border-primary/40">
            <CardContent className="flex items-center justify-between p-6">
              <div>
                <div className="flex items-center gap-2 text-lg font-semibold">
                  <Repeat className="h-4 w-4 text-primary" />
                  Repeat-offender mistakes
                </div>
                <p className="text-sm text-muted-foreground">
                  The exact moves you blunder over and over.
                </p>
              </div>
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
            </CardContent>
          </Card>
        </Link>
      </section>

      {/* Per-color summaries */}
      {payload.per_color.white && payload.per_color.black && (
        <section className="grid gap-6 md:grid-cols-2">
          {(["white", "black"] as const).map((color) => {
            const block = payload.per_color[color];
            if (!block) return null;
            return (
              <Card key={color}>
                <CardHeader>
                  <CardTitle className="capitalize">As {color}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-3 gap-2 text-center text-sm">
                    {block.phase_summary.map((row) => (
                      <div key={row.phase} className="rounded-md border border-border p-2">
                        <div className="text-xs text-muted-foreground capitalize">{row.phase}</div>
                        <div className="text-base font-semibold">{formatPercent(row.win_rate)}</div>
                      </div>
                    ))}
                  </div>
                  <pre className="max-h-60 overflow-auto whitespace-pre-wrap rounded-md bg-muted/50 p-3 text-xs">
                    {block.prescription}
                  </pre>
                </CardContent>
              </Card>
            );
          })}
        </section>
      )}
    </div>
  );
}
