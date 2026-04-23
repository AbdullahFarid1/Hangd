import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { notFound } from "next/navigation";
import { OpeningWinRateBar } from "@/components/OpeningWinRateBar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getInsights } from "@/lib/queries";

export default async function OpeningsPage({ params }: { params: { id: string } }) {
  const insights = await getInsights(params.id);
  if (!insights) notFound();

  const repertoire = insights.payload.repertoire ?? [];
  const white = repertoire.filter((r) => r.your_color === "White");
  const black = repertoire.filter((r) => r.your_color === "Black");

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <Link href={`/app/analyses/${params.id}`}>
            <Button variant="ghost" size="sm" className="mb-2 -ml-2">
              <ArrowLeft className="h-4 w-4" />
              Back to dashboard
            </Button>
          </Link>
          <h1 className="text-3xl font-bold tracking-tight">Opening repertoire</h1>
          <p className="text-muted-foreground">
            Win rates per opening you've actually reached. Sorted by total games.
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>As White</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {white.length === 0 ? (
              <p className="text-sm text-muted-foreground">No White games found.</p>
            ) : (
              white.map((row, i) => (
                <OpeningWinRateBar key={`${row.opening_name}-${row.eco}`} row={row} index={i} />
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>As Black</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {black.length === 0 ? (
              <p className="text-sm text-muted-foreground">No Black games found.</p>
            ) : (
              black.map((row, i) => (
                <OpeningWinRateBar key={`${row.opening_name}-${row.eco}`} row={row} index={i} />
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
