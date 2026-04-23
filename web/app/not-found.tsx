import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-4 text-center">
      <span className="text-5xl">♞</span>
      <h1 className="text-2xl font-bold">Page not found</h1>
      <p className="max-w-sm text-muted-foreground">
        Looks like that move isn't on the board. Try one of these:
      </p>
      <div className="flex gap-3">
        <Link href="/">
          <Button variant="outline">Home</Button>
        </Link>
        <Link href="/app">
          <Button>Dashboard</Button>
        </Link>
      </div>
    </div>
  );
}
