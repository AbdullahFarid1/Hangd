import { redirect } from "next/navigation";
import { Nav } from "@/components/Nav";
import { getCurrentUser } from "@/lib/queries";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();
  if (!user) redirect("/login");

  return (
    <div className="flex min-h-screen flex-col">
      <Nav userEmail={user.email} />
      <main className="container flex-1 py-8">{children}</main>
    </div>
  );
}
