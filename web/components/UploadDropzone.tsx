"use client";

import { useState, type DragEvent } from "react";
import { motion } from "framer-motion";
import { UploadCloud, FileText, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadDropzoneProps {
  label: string;
  hint?: string;
  accept?: string;
  onFile: (file: File | null) => void;
  selectedName?: string | null;
}

export function UploadDropzone({
  label,
  hint = "Drag your .pgn here or click to browse",
  accept = ".pgn",
  onFile,
  selectedName,
}: UploadDropzoneProps) {
  const [hover, setHover] = useState(false);

  function handleDrop(e: DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    setHover(false);
    const file = e.dataTransfer.files?.[0];
    if (file) onFile(file);
  }

  return (
    <label
      onDragOver={(e) => {
        e.preventDefault();
        setHover(true);
      }}
      onDragLeave={() => setHover(false)}
      onDrop={handleDrop}
      className={cn(
        "group relative flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-border bg-card/50 p-10 transition-colors",
        hover && "border-primary bg-primary/5",
      )}
    >
      <motion.div
        animate={{ y: hover ? -4 : 0 }}
        transition={{ type: "spring", stiffness: 200, damping: 15 }}
        className="rounded-full bg-primary/10 p-3 text-primary"
      >
        <UploadCloud className="h-6 w-6" />
      </motion.div>
      <div className="text-center">
        <div className="font-medium">{label}</div>
        <div className="text-xs text-muted-foreground">{hint}</div>
      </div>

      <input
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => onFile(e.target.files?.[0] ?? null)}
      />

      {selectedName && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mt-2 flex items-center gap-2 rounded-md border border-border bg-background px-3 py-1.5 text-sm"
        >
          <FileText className="h-4 w-4 text-primary" />
          <span className="max-w-[200px] truncate" title={selectedName}>
            {selectedName}
          </span>
          <button
            type="button"
            className="text-muted-foreground hover:text-foreground"
            onClick={(e) => {
              e.preventDefault();
              onFile(null);
            }}
            aria-label="Clear file"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </motion.div>
      )}
    </label>
  );
}
