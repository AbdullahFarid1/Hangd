import Link from "next/link";
import { AuthForm } from "./AuthForm";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm space-y-6">
        <Link href="/" className="flex items-center justify-center gap-2 text-2xl font-bold">
          <span>♞</span>
          <span>Hangd</span>
        </Link>
        <p className="text-center text-sm text-muted-foreground">
          Sign in (or create an account) to start analysing your games.
        </p>
        <AuthForm />
      </div>
    </div>
  );
}
