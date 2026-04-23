import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { notFound } from "next/navigation";
import { RepeatOffenderCard } from "@/components/RepeatOffenderCard";
import { Button } from "@/components/ui/button";
import { getInsights } from "@/lib/queries";

export default async function RepeatsPage({ params }: { params: { id: string } }) {
  const insights = await getInsights(params.id);
  if (!insights) notFound();

  const rows = insights.payload.repeat_offenders ?? [];

  return (
    <div className="space-y-6">
      <div>
        <Link href={`/app/analyses/${params.id}`}>
          <Button variant="ghost" size="sm" className="mb-2 -ml-2">
            <ArrowLeft className="h-4 w-4" />
            Back to dashboard
          </Button>
        </Link>
        <h1 className="text-3xl font-bold tracking-tight">Repeat-offender mistakes</h1>
        <p className="text-muted-foreground">
          The exact (move number, SAN) errors you've made at least 3 times. Highest-impact at the top.
        </p>
      </div>

      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No repeated mistakes found yet — or you don't have enough games for patterns to emerge.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {rows.map((row, i) => (
            <RepeatOffenderCard key={`${row.side}-${row.move_san}-${i}`} row={row} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}
