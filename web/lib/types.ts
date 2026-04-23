// Mirror of the Python `backend/insight_bundler.py` payload shape.
// Keep in sync with that module.

export type ErrorLabel = "ok" | "inaccuracy" | "mistake" | "blunder";
export type PhaseKind = "opening" | "middlegame" | "endgame";
export type ColorFile = "white_file" | "black_file";
export type JobStatus = "queued" | "running" | "done" | "failed";

export interface PhaseWinrateRow {
  phase: PhaseKind;
  error_type: ErrorLabel;
  win: number;
  loss: number;
  draw: number;
  total: number;
  win_rate: number | null;
}

export interface PhaseSummaryRow {
  phase: PhaseKind;
  win: number;
  loss: number;
  draw: number;
  total: number;
  win_rate: number | null;
}

export interface RepeatOffenderRow {
  side: "White" | "Black";
  error_type: ErrorLabel;
  move_number: number;
  san: string;
  move_san: string;
  count: number;
}

export interface HeatmapRow {
  move_number: number;
  error_type: ErrorLabel;
  count: number;
}

export interface TrendRow {
  period: string;
  blunder?: number;
  mistake?: number;
  inaccuracy?: number;
  total_errors?: number;
  games?: number;
  errors_per_game?: number | null;
}

export interface EndgameTypeRow {
  signature: string;
  wins: number;
  losses: number;
  draws: number;
  total: number;
  win_rate: number | null;
}

export interface RepertoireRow {
  your_color: "White" | "Black";
  opening_name: string;
  eco: string;
  win: number;
  loss: number;
  draw: number;
  total: number;
  win_rate: number | null;
  avg_cp_drop?: number | null;
  most_common_error?: ErrorLabel | "";
}

export interface PerColorBlock {
  phase_winrates: PhaseWinrateRow[];
  phase_summary: PhaseSummaryRow[];
  totals: Record<string, number>;
  prescription: string;
}

export interface InsightPayload {
  kpis: {
    total_games: number;
    total_moves: number;
    total_errors: number;
    blunders: number;
    mistakes: number;
    inaccuracies: number;
    stability_score: number;
  };
  phase_winrates: PhaseWinrateRow[];
  phase_summary: PhaseSummaryRow[];
  per_color: { white?: PerColorBlock; black?: PerColorBlock };
  combined_prescription: string;
  repeat_offenders: RepeatOffenderRow[];
  heatmap: HeatmapRow[];
  trend: TrendRow[];
  endgame_types: EndgameTypeRow[];
  repertoire: RepertoireRow[];
  empty?: boolean;
}

export interface AnalysisJob {
  id: string;
  user_id: string;
  upload_white: string | null;
  upload_black: string | null;
  status: JobStatus;
  progress_games_done: number;
  progress_games_total: number;
  progress_moves_done: number;
  progress_moves_total: number;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface InsightSummary {
  id: string;
  user_id: string;
  job_id: string;
  payload: InsightPayload;
  generated_at: string;
}
