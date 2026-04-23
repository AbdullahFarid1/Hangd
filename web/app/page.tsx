"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Brain,
  LineChart,
  Repeat,
  Shield,
  Sparkles,
  Target,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { AnimatedCounter } from "@/components/landing/AnimatedCounter";
import { FloatingPieces } from "@/components/landing/FloatingPieces";
import { GradientOrb } from "@/components/landing/GradientOrb";
import { MockDashboard } from "@/components/landing/MockDashboard";
import { OpeningsMarquee } from "@/components/landing/OpeningsMarquee";

const features = [
  {
    icon: Target,
    title: "Find your real weak spots",
    body: "Stockfish reviews every move and groups your errors by phase, opening, and recurring patterns — not just an overall accuracy number.",
  },
  {
    icon: Repeat,
    title: "Spot what you keep blundering",
    body: "Repeat-offender detection finds the exact (move number, SAN) errors you make over and over so you can study them once.",
  },
  {
    icon: LineChart,
    title: "Track improvement over time",
    body: "Rolling error-rate charts pulled from your PGN dates show whether your training is actually working.",
  },
  {
    icon: Brain,
    title: "Personalised prescription",
    body: "A short, plain-English training plan based on your weakest phase and most expensive mistakes.",
  },
  {
    icon: Shield,
    title: "Your data stays yours",
    body: "Private storage, row-level security in the database, signed URLs only. Delete your analyses anytime.",
  },
  {
    icon: Zap,
    title: "Built on Stockfish",
    body: "The same engine top players use. We don't shortcut to a heuristic — every move is engine-evaluated.",
  },
];

const HEADLINE_WORDS = ["Find", "out", "exactly", "where", "you"];

export default function LandingPage() {
  return (
    <div className="relative flex min-h-screen flex-col overflow-x-hidden">
      <GradientOrb />

      {/* Top bar */}
      <header className="relative z-30 border-b border-border/50 bg-background/40 backdrop-blur">
        <div className="container flex h-14 items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-lg font-bold">
            <motion.span
              className="text-xl"
              animate={{ rotate: [0, -10, 10, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            >
              ♞
            </motion.span>
            <span>Hangd</span>
          </Link>
          <div className="flex items-center gap-2">
            <Link href="/login">
              <Button variant="ghost" size="sm">Sign in</Button>
            </Link>
            <Link href="/login">
              <Button size="sm">Get started</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* HERO */}
      <section className="relative z-10 overflow-hidden">
        <FloatingPieces count={16} />

        <div className="container relative z-10 flex flex-col items-center gap-8 py-24 text-center md:py-36">
          <motion.span
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="rounded-full border border-primary/30 bg-primary/5 px-4 py-1.5 text-xs font-medium text-primary backdrop-blur"
          >
            <span className="inline-block animate-pulse">●</span> Powered by Stockfish · open source
          </motion.span>

          <h1 className="text-balance text-5xl font-bold tracking-tight md:text-7xl">
            <span className="block">
              {HEADLINE_WORDS.map((word, i) => (
                <motion.span
                  key={i}
                  initial={{ opacity: 0, y: 20, filter: "blur(8px)" }}
                  animate={{ opacity: 1, y: 0, filter: "blur(0)" }}
                  transition={{ delay: 0.15 + i * 0.08, duration: 0.6 }}
                  className="mr-3 inline-block"
                >
                  {word}
                </motion.span>
              ))}
            </span>
            <motion.span
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.7, duration: 0.7, ease: "backOut" }}
              className="block bg-gradient-to-br from-primary via-walnut to-blunder bg-clip-text text-transparent"
            >
              blunder.
            </motion.span>
          </h1>

          <motion.p
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.0 }}
            className="max-w-2xl text-balance text-lg text-muted-foreground md:text-xl"
          >
            Upload your PGN games. Hangd runs Stockfish on every move, finds the patterns
            you keep repeating, and tells you what to study next. No vague accuracy scores —
            actual fixable mistakes.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.15 }}
            className="flex flex-wrap items-center justify-center gap-3 pt-2"
          >
            <Link href="/login">
              <Button size="lg" className="group">
                Analyse my games
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
            <a
              href="https://github.com/AbdullahFarid1/Hangd"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button size="lg" variant="outline">
                View on GitHub
              </Button>
            </a>
          </motion.div>

          {/* Live counter strip */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.4, duration: 0.6 }}
            className="mt-8 grid w-full max-w-3xl grid-cols-2 gap-4 md:grid-cols-4"
          >
            <CounterTile value={12196} label="Games analysed" />
            <CounterTile value={759955} label="Moves classified" />
            <CounterTile value={113143} label="Errors caught" />
            <CounterTile value={1703} label="Openings tracked" />
          </motion.div>
        </div>
      </section>

      {/* Marquee */}
      <section className="relative z-10">
        <OpeningsMarquee />
      </section>

      {/* Mock dashboard preview */}
      <section className="container relative z-10 py-24 md:py-32">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mx-auto max-w-2xl space-y-3 text-center"
        >
          <span className="text-xs uppercase tracking-widest text-primary">
            Your post-mortem
          </span>
          <h2 className="text-balance text-3xl font-bold md:text-5xl">
            One dashboard. Every weakness exposed.
          </h2>
          <p className="text-balance text-muted-foreground">
            Win rate per phase, error heatmap, repeat-offender mistakes — all generated from
            your own games, not generic puzzles.
          </p>
        </motion.div>

        <div className="mt-16">
          <MockDashboard />
        </div>
      </section>

      {/* Features grid */}
      <section className="container relative z-10 py-16 md:py-24">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mx-auto max-w-2xl space-y-3 text-center"
        >
          <span className="text-xs uppercase tracking-widest text-primary">Features</span>
          <h2 className="text-balance text-3xl font-bold md:text-5xl">
            Engine-honest, player-focused.
          </h2>
        </motion.div>

        <div className="mt-12 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {features.map(({ icon: Icon, title, body }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ delay: i * 0.05, duration: 0.5 }}
              whileHover={{ y: -4, transition: { duration: 0.2 } }}
            >
              <Card className="group h-full overflow-hidden transition-colors hover:border-primary/40">
                <CardContent className="space-y-3 p-6">
                  <div className="inline-flex rounded-lg bg-primary/10 p-2 text-primary transition-colors group-hover:bg-primary/20">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-lg font-semibold">{title}</h3>
                  <p className="text-sm text-muted-foreground">{body}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="container relative z-10 py-24">
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="relative mx-auto max-w-3xl overflow-hidden rounded-3xl border border-border bg-card p-12 text-center"
        >
          <div
            aria-hidden
            className="absolute inset-0 -z-10 opacity-50"
            style={{
              background:
                "radial-gradient(circle at 50% 0%, hsl(var(--primary) / 0.18), transparent 60%)",
            }}
          />
          <Sparkles className="mx-auto h-8 w-8 text-primary" />
          <h2 className="mt-4 text-balance text-3xl font-bold md:text-4xl">
            Stop guessing what to study.
          </h2>
          <p className="mt-3 text-balance text-muted-foreground">
            Upload your PGN. Get a personalised, engine-backed training plan in minutes.
          </p>
          <div className="mt-6">
            <Link href="/login">
              <Button size="lg" className="group">
                Get started — it's free
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
          </div>
        </motion.div>
      </section>

      <footer className="relative z-10 border-t border-border py-8 text-center text-xs text-muted-foreground">
        Built with Stockfish, python-chess, Supabase, and Next.js. ♞
      </footer>
    </div>
  );
}

function CounterTile({ value, label }: { value: number; label: string }) {
  return (
    <div className="rounded-xl border border-border bg-card/60 p-4 backdrop-blur">
      <div className="text-2xl font-bold tabular-nums text-primary md:text-3xl">
        <AnimatedCounter value={value} />
      </div>
      <div className="mt-1 text-[11px] uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
    </div>
  );
}
