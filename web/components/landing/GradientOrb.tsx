"use client";

import { motion, useMotionValue, useSpring } from "framer-motion";
import { useEffect } from "react";

/** A glowing orb in the hero that softly follows the cursor. */
export function GradientOrb() {
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const sx = useSpring(x, { damping: 30, stiffness: 80 });
  const sy = useSpring(y, { damping: 30, stiffness: 80 });

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      x.set(e.clientX);
      y.set(e.clientY);
    };
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, [x, y]);

  return (
    <motion.div
      aria-hidden
      className="pointer-events-none fixed inset-0 z-0"
      style={{
        background: "radial-gradient(600px circle at var(--orb-x) var(--orb-y), hsl(var(--primary) / 0.18), transparent 60%)",
        // Bind motion values to CSS custom properties via inline style hack
        // (Framer Motion will update these on every frame).
      }}
    >
      <motion.div
        className="absolute inset-0"
        style={{
          x: sx,
          y: sy,
          width: 600,
          height: 600,
          marginLeft: -300,
          marginTop: -300,
          background:
            "radial-gradient(circle, hsl(var(--primary) / 0.22) 0%, transparent 70%)",
          filter: "blur(60px)",
        }}
      />
    </motion.div>
  );
}
