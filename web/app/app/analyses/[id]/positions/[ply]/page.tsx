import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { notFound } from "next/navigation";
import { EvalBar } from "@/components/EvalBar";
import { MiniBoard } from "@/components/MiniBoard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getMoveByPly } from "@/lib/queries";
import { classifyError, cn, formatNumber } from "@/lib/utils";

interface MoveRow {
  ply: number;
  move_number: number;
  side: string;
  san: string;
  uci: string;
  fen_before: string | null;
  best_cp: number | null;
  played_cp: number | null;
  cp_drop: number | null;
  error_type: string;
  mate_swing: boolean;
  phase: string;
}

export default async function PositionPage({ params }: { params: { id: string; ply: string } }) {
  const ply = Number(params.ply);
  if (!Number.isFinite(ply)) notFound();

  const row = (await getMoveByPly(params.id, ply)) as MoveRow | null;
  if (!row || !row.fen_before) notFound();

  return (
    <div className="space-y-6">
      <div>
        <Link href={`/app/analyses/${params.id}`}>
          <Button variant="ghost" size="sm" className="mb-2 -ml-2">
            <ArrowLeft className="h-4 w-4" />
            Back to dashboard
          </Button>
        </Link>
        <h1 className="text-2xl font-bold">
          Move {row.move_number} · {row.san}
        </h1>
        <p className="text-sm text-muted-foreground">
          {row.side} to move · {row.phase}
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-[auto_1fr]">
        <div className="flex items-start gap-3">
          <MiniBoard fen={row.fen_before} size={320} blackBottom={row.side === "Black"} />
          <EvalBar cp={row.best_cp ?? 0} height={320} />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>What happened</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Row label="Engine eval before move" value={`${formatNumber(row.best_cp)} cp`} />
            <Row label="Eval after your move" value={`${formatNumber(row.played_cp)} cp`} />
            <Row label="Centipawn drop" value={`${formatNumber(row.cp_drop)} cp`} />
            <div>
              <span className="text-muted-foreground">Verdict</span>
              <div className="mt-1">
                <span
                  className={cn(
                    "rounded-md border px-2 py-0.5 text-xs font-medium capitalize",
                    classifyError(row.error_type),
                  )}
                >
                  {row.error_type}
                  {row.mate_swing && " · mate swing"}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border/60 pb-2 last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="tabular-nums">{value}</span>
    </div>
  );
}
