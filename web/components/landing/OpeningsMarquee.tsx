"use client";

import { motion } from "framer-motion";

const OPENINGS = [
  "Sicilian Defense",
  "Queen's Gambit",
  "Ruy Lopez",
  "London System",
  "Caro-Kann",
  "King's Indian",
  "Nimzo-Indian",
  "Catalan",
  "French Defense",
  "Scandinavian",
  "English Opening",
  "Pirc Defense",
  "Slav Defense",
  "Grünfeld",
  "Reti Opening",
  "Bird's Opening",
  "Vienna Game",
  "Italian Game",
  "Petroff Defense",
  "Trompowsky Attack",
];

export function OpeningsMarquee() {
  // Doubled list for seamless loop.
  const items = [...OPENINGS, ...OPENINGS];

  return (
    <div className="relative w-full overflow-hidden border-y border-border bg-card/50 py-6">
      {/* Edge fade */}
      <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-32 bg-gradient-to-r from-background to-transparent" />
      <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-32 bg-gradient-to-l from-background to-transparent" />

      <motion.div
        className="flex gap-12 whitespace-nowrap"
        animate={{ x: ["0%", "-50%"] }}
        transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
      >
        {items.map((opening, i) => (
          <span
            key={i}
            className="flex items-center gap-3 text-lg font-medium text-muted-foreground"
          >
            <span className="text-primary">♞</span>
            {opening}
          </span>
        ))}
      </motion.div>
    </div>
  );
}
