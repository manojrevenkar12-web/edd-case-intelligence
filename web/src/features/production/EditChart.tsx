import { motion, useReducedMotion } from "framer-motion";
import type { Week } from "../../app/types";
import { chart, color, font, motion as m, stroke } from "../../theme/tokens";

/** The factual-edit rate week by week against its control limit, with what happened on the timeline. */
export function EditChart({ weeks, newTypologyWeek, promotedWeek }: { weeks: Week[]; newTypologyWeek: number; promotedWeek: number | null }) {
  const reduce = useReducedMotion();
  const { width: W, lineHeight: H, pad: P } = chart;
  const maxY = Math.max(0.25, ...weeks.map((w) => w.factual_edit_rate));
  const x = (wk: number) => P.left + ((wk - 1) / (weeks.length - 1)) * (W - P.left - P.right);
  const y = (v: number) => P.top + (1 - v / maxY) * (H - P.top - P.bottom);
  const path = weeks.map((w, i) => `${i ? "L" : "M"}${x(w.week)},${y(w.factual_edit_rate)}`).join(" ");
  const ucl = weeks.find((w) => w.edit_ucl !== null)?.edit_ucl ?? null;
  const firstUcl = weeks.find((w) => w.edit_ucl !== null)?.week ?? 1;
  return (
    <figure style={{ margin: 0 }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Weekly factual edit rate with control limit">
        {[0, 0.1, 0.2].map((v) => (
          <g key={v}>
            <line x1={P.left} x2={W - P.right} y1={y(v)} y2={y(v)} stroke={color.rule} strokeWidth={stroke.hair} />
            <text x={P.left - 8} y={y(v) + 4} textAnchor="end" fontSize={font.size.xs} fill={color.ink2}>{`${v * 100}%`}</text>
          </g>
        ))}
        {ucl !== null && (
          <line x1={x(firstUcl)} x2={W - P.right} y1={y(ucl)} y2={y(ucl)} stroke={color.alert} strokeDasharray="4 4" strokeWidth={stroke.hair} />
        )}
        <line x1={x(newTypologyWeek)} x2={x(newTypologyWeek)} y1={P.top} y2={H - P.bottom} stroke={color.event} strokeWidth={stroke.hair} />
        <text x={x(newTypologyWeek) + 4} y={P.top + 10} fontSize={font.size.xs} fill={color.event}>new mule typology</text>
        {promotedWeek && (
          <>
            <line x1={x(promotedWeek)} x2={x(promotedWeek)} y1={P.top} y2={H - P.bottom} stroke={color.chosen} strokeWidth={stroke.hair} />
            <text x={x(promotedWeek) + 4} y={P.top + 26} fontSize={font.size.xs} fill={color.chosen}>candidate promoted</text>
          </>
        )}
        <motion.path d={path} fill="none" stroke={color.ink} strokeWidth={stroke.line}
          initial={reduce ? false : { pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: m.draw, ease: m.ease }} />
        {weeks.map((w) => (
          <circle key={w.week} cx={x(w.week)} cy={y(w.factual_edit_rate)} r={chart.dot}
            fill={w.alerts.length ? color.alert : color.card} stroke={w.alerts.length ? color.alert : color.ink} strokeWidth={stroke.hair}>
            <title>{`Week ${w.week}: ${(w.factual_edit_rate * 100).toFixed(1)}% factual edits. ${w.alerts.join("; ")}`}</title>
          </circle>
        ))}
        {weeks.map((w) => (
          <text key={`l${w.week}`} x={x(w.week)} y={H - 12} textAnchor="middle" fontSize={font.size.xs} fill={color.ink2}>{w.week}</text>
        ))}
      </svg>
      <figcaption className="legend">
        <span>line: share of drafts an analyst corrected on substance (flags, risk, documents or a number)</span>
        <span>dashed: 3-sigma control limit from weeks 1 to 4</span>
        <span>red points: weeks with an alert</span>
      </figcaption>
    </figure>
  );
}
