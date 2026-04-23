"use client";

import { animate, useInView, useMotionValue, useTransform } from "framer-motion";
import { useEffect, useRef } from "react";

interface AnimatedCounterProps {
  value: number;
  duration?: number;
  format?: (n: number) => string;
  className?: string;
}

const defaultFormat = (n: number) =>
  new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(Math.round(n));

export function AnimatedCounter({
  value,
  duration = 1.6,
  format = defaultFormat,
  className,
}: AnimatedCounterProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-50px" });
  const motionValue = useMotionValue(0);
  const display = useTransform(motionValue, format);

  useEffect(() => {
    if (!inView) return;
    const controls = animate(motionValue, value, {
      duration,
      ease: "easeOut",
    });
    return () => controls.stop();
  }, [inView, value, duration, motionValue]);

  useEffect(() => {
    return display.on("change", (latest) => {
      if (ref.current) ref.current.textContent = latest;
    });
  }, [display]);

  return <span ref={ref} className={className}>0</span>;
}
