// Every colour, size and duration the dashboard uses.
// A case file on a reviewer's desk: cool paper, ink, a teal pen for the chosen configuration, grey for the
// baseline, red only for what an analyst had to correct. Status always has a word as well as a colour.

export const color = {
  page: "#e9edf1",
  card: "#ffffff",
  ink: "#15202b",
  ink2: "#4a5662",
  muted: "#7b8794",
  rule: "#cfd6dd",
  wash: "rgba(15,118,110,0.08)",
  chosen: "#0f766e",
  baseline: "#8b95a1",
  alert: "#b42318",
  event: "#6941c6",
  focus: "#0f766e",
} as const;

export const font = {
  body: "'Source Sans 3', system-ui, -apple-system, 'Segoe UI', sans-serif",
  serif: "'Source Serif 4', Georgia, serif",
  size: { xs: 12, sm: 14, md: 16, lg: 19, xl: 23, xxl: 28, xxxl: 40, hero: 64 },
  weight: { regular: 400, semibold: 600 },
  leading: { tight: 1.1, body: 1.55 },
} as const;

export const space = { 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32, 10: 40, 12: 48, 16: 64 } as const;
export const radius = { sm: 2, md: 4 } as const;
export const stroke = { hair: 1, line: 2, focus: 2.5 } as const;
export const layout = { maxWidth: 1140, measure: 68 } as const;
export const motion = { base: 0.3, draw: 1.0, stagger: 0.05, ease: [0.22, 1, 0.36, 1] as [number, number, number, number] } as const;

export const chart = {
  width: 760,
  forestRow: 34,
  forestLabel: 230,
  forestPad: 24,
  dot: 4.5,
  lineHeight: 240,
  pad: { top: 16, right: 24, bottom: 34, left: 48 },
  barHeight: 12,
  barLabel: 170,
  barArea: 420,
  skeleton: 280,
} as const;

export const breakpoint = { narrow: 860 } as const;
