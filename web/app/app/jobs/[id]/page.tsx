import { notFound } from "next/navigation";
import { ProgressLive } from "@/components/ProgressLive";
import { getJob } from "@/lib/queries";

export default async function JobPage({ params }: { params: { id: string } }) {
  const job = await getJob(params.id);
  if (!job) notFound();

  return (
    <div className="mx-auto max-w-2xl">
      <ProgressLive initial={job} />
    </div>
  );
}
