import type { Dashboard } from "../../app/types";
import { label } from "../../shared/format";
import { chart, color, font, space } from "../../theme/tokens";

export function Labels({ data }: { data: Dashboard }) {
  const a = data.agreement.heldout;
  const rows = Object.entries(a.flags).sort((x, y) => x[1] - y[1]);
  const rowH = chart.barHeight + space[3];
  return (
    <div className="board">
      <svg viewBox={`0 0 ${chart.barLabel + chart.barArea + 60} ${rows.length * rowH}`} width="100%" role="img"
        aria-label="Cohen's kappa between the two SMEs per flag">
        {rows.map(([f, k], i) => (
          <g key={f}>
            <text x={chart.barLabel - space[2]} y={i * rowH + chart.barHeight - 1} textAnchor="end" fontSize={font.size.sm} fill={color.ink}>{label(f)}</text>
            <rect x={chart.barLabel} y={i * rowH} width={Math.max(0, k) * chart.barArea} height={chart.barHeight} fill={k < 0.8 ? color.alert : color.chosen} />
            <text x={chart.barLabel + Math.max(0, k) * chart.barArea + space[2]} y={i * rowH + chart.barHeight - 1} fontSize={font.size.sm} fill={color.ink2}>{k.toFixed(2)}</text>
          </g>
        ))}
      </svg>
      <p className="ink2 measure" style={{ marginTop: space[4] }}>
        Two SMEs labelled the same {a.cases} cases and disagreed on {a.disagreements}; a senior reviewer adjudicated those against the
        guideline. Red bars (kappa below 0.8) are the definitions the guideline still leaves open, here "profile mismatch".
      </p>
    </div>
  );
}
