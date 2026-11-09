import { motion, useReducedMotion } from "framer-motion";
import type { Experiment } from "../../app/types";
import { label } from "../../shared/format";
import { chart, color, font, motion as m, stroke } from "../../theme/tokens";

/** Each pre-registered hypothesis: the effect estimated on the development split (grey) and tested once on the
 *  held-out split (teal when the Holm-corrected test confirmed it, outlined when it did not). */
export function Forest({ experiments }: { experiments: Experiment[] }) {
  const reduce = useReducedMotion();
  const W = chart.width;
  const left = chart.forestLabel;
  const right = W - chart.forestPad;
  const all = experiments.flatMap((e) => [e.dev.ci[0], e.dev.ci[1], e.heldout.ci[0], e.heldout.ci[1]]);
  const lo = Math.min(-0.05, ...all);
  const hi = Math.max(0.05, ...all);
  const x = (v: number) => left + ((v - lo) / (hi - lo)) * (right - left);
  const H = experiments.length * chart.forestRow + chart.pad.bottom;
  return (
    <figure style={{ margin: 0 }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Effects of seven pre-registered prompt experiments">
        <line x1={x(0)} x2={x(0)} y1={0} y2={H - chart.pad.bottom + 6} stroke={color.ink2} strokeWidth={stroke.hair} />
        {[lo, 0, hi].map((v) => (
          <text key={v} x={x(v)} y={H - 10} textAnchor="middle" fontSize={font.size.xs} fill={color.ink2}>
            {`${v > 0 ? "+" : ""}${(v * 100).toFixed(0)} pts`}
          </text>
        ))}
        {experiments.map((e, i) => {
          const y = i * chart.forestRow + chart.forestRow / 2;
          const confirmed = e.heldout.confirmed;
          return (
            <g key={e.id}>
              <text x={0} y={y - 3} fontSize={font.size.sm} fill={color.ink}>
                {e.id.split("-").slice(1).join(" ")}
              </text>
              <text x={0} y={y + 12} fontSize={font.size.xs} fill={color.muted}>
                {label(e.metric)}, expect {e.direction === "greater" ? "higher" : "lower"}
              </text>
              <line x1={x(e.dev.ci[0])} x2={x(e.dev.ci[1])} y1={y - 5} y2={y - 5} stroke={color.baseline} strokeWidth={stroke.line} />
              <circle cx={x(e.dev.effect)} cy={y - 5} r={chart.dot - 1} fill={color.baseline} />
              <motion.line
                y1={y + 5}
                y2={y + 5}
                stroke={color.chosen}
                strokeWidth={stroke.line}
                initial={reduce ? false : { x1: x(e.heldout.effect), x2: x(e.heldout.effect) }}
                animate={{ x1: x(e.heldout.ci[0]), x2: x(e.heldout.ci[1]) }}
                transition={{ duration: m.draw, ease: m.ease, delay: i * m.stagger }}
              />
              <circle cx={x(e.heldout.effect)} cy={y + 5} r={chart.dot} fill={confirmed ? color.chosen : color.card}
                stroke={color.chosen} strokeWidth={stroke.line}>
                <title>{`${e.hypothesis} Held-out: ${confirmed ? "confirmed" : "not confirmed"}.`}</title>
              </circle>
            </g>
          );
        })}
      </svg>
      <figcaption className="legend">
        <span>grey: development split</span>
        <span>teal: held-out split, run once (filled when confirmed after the Holm correction)</span>
      </figcaption>
    </figure>
  );
}
