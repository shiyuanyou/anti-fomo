/**
 * Shared utility functions and constants
 */

/** Format a numeric amount: ≥10000 → "X.X万", else locale-formatted */
export function formatAmount(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(1) + "万";
  return n.toLocaleString();
}

/** 10-color gradient palette for treemap blocks and detail chips */
export const PALETTE = [
  { from: "#0EA5E9", to: "#0284C7" },   // sky
  { from: "#8B5CF6", to: "#7C3AED" },   // violet
  { from: "#F43F5E", to: "#E11D48" },   // rose
  { from: "#10B981", to: "#059669" },   // emerald
  { from: "#F59E0B", to: "#D97706" },   // amber
  { from: "#6366F1", to: "#4F46E5" },   // indigo
  { from: "#EC4899", to: "#DB2777" },   // pink
  { from: "#14B8A6", to: "#0D9488" },   // teal
  { from: "#EF4444", to: "#DC2626" },   // red
  { from: "#84CC16", to: "#65A30D" },   // lime
] as const;

/** Allocation bar color palette (flat colors for template cards) */
export const ALLOC_PALETTE = [
  "#38BDF8", "#818CF8", "#34D399", "#FBBF24", "#F87171",
  "#A78BFA", "#F472B6", "#2DD4BF", "#FB923C", "#A3E635",
] as const;

/** Risk level badge colors */
export const RISK_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  "低":   { bg: "rgba(16, 185, 129, 0.12)", border: "rgba(16, 185, 129, 0.3)", text: "#34D399" },
  "中":   { bg: "rgba(56, 189, 248, 0.12)", border: "rgba(56, 189, 248, 0.3)", text: "#38BDF8" },
  "中高": { bg: "rgba(245, 158, 11, 0.12)", border: "rgba(245, 158, 11, 0.3)", text: "#FBBF24" },
  "高":   { bg: "rgba(239, 68, 68, 0.12)",  border: "rgba(239, 68, 68, 0.3)",  text: "#F87171" },
};
