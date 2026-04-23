import { UploadForm } from "./UploadForm";

export default function UploadPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">New analysis</h1>
        <p className="text-muted-foreground">
          Upload one PGN of games where you played White, one of games as Black. (You can
          submit just one if you only want analysis for that color.)
        </p>
      </div>
      <UploadForm />
    </div>
  );
}
