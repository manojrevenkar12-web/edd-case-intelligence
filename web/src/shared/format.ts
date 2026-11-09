export const pct = (n: number, d = 1) => `${(n * 100).toFixed(d)}%`;
export const signedPts = (n: number, d = 1) => `${n >= 0 ? "+" : "−"}${Math.abs(n * 100).toFixed(d)} pts`;
export const usd = (n: number) => `$${n.toFixed(3)}`;
export const label = (s: string) => s.replaceAll("_", " ");
