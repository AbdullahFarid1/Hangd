"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";

const PIECES = ["♚", "♛", "♜", "♝", "♞", "♟", "♔", "♕", "♖", "♗", "♘", "♙"];

interface PieceConfig {
  char: string;
  left: string;
  size: number;
  delay: number;
  duration: number;
  drift: number;
  rotateRange: number;
}

function generate(count: number): PieceConfig[] {
  const out: PieceConfig[] = [];
  for (let i = 0; i < count; i++) {
    out.push({
      char: PIECES[i % PIECES.length],
      left: `${(i / count) * 100 + (Math.random() * 6 - 3)}%`,
      size: 28 + Math.random() * 64,
      delay: Math.random() * 8,
      duration: 16 + Math.random() * 14,
      drift: (Math.random() - 0.5) * 80,
      rotateRange: (Math.random() - 0.5) * 60,
    });
  }
  return out;
}

export function FloatingPieces({ count = 14 }: { count?: number }) {
  // Stable across renders so SSR/CSR positions match.
  const pieces = useMemo(() => generate(count), [count]);

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      {pieces.map((p, i) => (
        <motion.span
          key={i}
          className="absolute select-none text-primary/15 dark:text-primary/20"
          style={{
            left: p.left,
            top: "100%",
            fontSize: p.size,
          }}
          initial={{ y: 0, x: 0, rotate: 0, opacity: 0 }}
          animate={{
            y: ["0vh", "-110vh"],
            x: [0, p.drift, -p.drift, 0],
            rotate: [0, p.rotateRange, -p.rotateRange, 0],
            opacity: [0, 0.6, 0.6, 0],
          }}
          transition={{
            duration: p.duration,
            delay: p.delay,
            repeat: Infinity,
            ease: "linear",
          }}
        >
          {p.char}
        </motion.span>
      ))}
    </div>
  );
}
