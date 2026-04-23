"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { UploadDropzone } from "@/components/UploadDropzone";
import { createClient } from "@/lib/supabase/client";

async function sha256Hex(file: File): Promise<string> {
  const buf = await file.arrayBuffer();
  const digest = await crypto.subtle.digest("SHA-256", buf);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export function UploadForm() {
  const router = useRouter();
  const [whiteFile, setWhiteFile] = useState<File | null>(null);
  const [blackFile, setBlackFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function uploadOne(supabase: ReturnType<typeof createClient>, userId: string, file: File, kind: "white_file" | "black_file") {
    const sha = await sha256Hex(file);
    const path = `${userId}/${Date.now()}-${kind}-${sha.slice(0, 8)}.pgn`;
    const { error: upErr } = await supabase.storage.from("pgns").upload(path, file, {
      contentType: "application/x-chess-pgn",
      upsert: false,
    });
    if (upErr) throw upErr;

    const { data, error: insErr } = await supabase
      .from("uploads")
      .insert({
        user_id: userId,
        color_file: kind,
        storage_path: path,
        original_filename: file.name,
        sha256: sha,
        bytes: file.size,
      })
      .select("id")
      .single();
    if (insErr) throw insErr;
    return data.id as string;
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!whiteFile && !blackFile) {
      setError("Please pick at least one PGN file.");
      return;
    }
    setBusy(true);
    try {
      const supabase = createClient();
      const { data: userData } = await supabase.auth.getUser();
      const userId = userData.user?.id;
      if (!userId) throw new Error("Not signed in.");

      const upload_white = whiteFile ? await uploadOne(supabase, userId, whiteFile, "white_file") : null;
      const upload_black = blackFile ? await uploadOne(supabase, userId, blackFile, "black_file") : null;

      const { data: job, error: jobErr } = await supabase
        .from("analysis_jobs")
        .insert({ user_id: userId, upload_white, upload_black })
        .select("id")
        .single();
      if (jobErr) throw jobErr;

      router.push(`/app/jobs/${job.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit}>
      <Card>
        <CardContent className="space-y-4 p-6">
          <UploadDropzone
            label="Games as White"
            onFile={setWhiteFile}
            selectedName={whiteFile?.name ?? null}
          />
          <UploadDropzone
            label="Games as Black"
            onFile={setBlackFile}
            selectedName={blackFile?.name ?? null}
          />
          {error && (
            <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}
        </CardContent>
        <CardFooter className="justify-between">
          <p className="text-xs text-muted-foreground">
            Analysis runs in the background. You can leave this page.
          </p>
          <Button type="submit" disabled={busy}>
            {busy ? "Uploading…" : "Start analysis"}
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}
