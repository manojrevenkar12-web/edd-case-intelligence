import type { Dashboard } from "../../app/types";
import { pct, signedPts, usd } from "../../shared/format";

export function Overview({ data }: { data: Dashboard }) {
  const h = data.heldout;
  return (
    <div className="board">
      <div className="figures">
        <div className="figure">
          <strong>{pct(h.chosen.case_correct)}</strong>
          <span className="ink2">
            of held-out cases fully right (every flag and the risk class), against {pct(h.baseline.case_correct)} for the
            baseline prompt: {signedPts(h.lift.effect)}, 95% CI {signedPts(h.lift.ci[0])} to {signedPts(h.lift.ci[1])}
          </span>
        </div>
        <div className="figure">
          <strong>{pct(h.chosen.high_risk_recall)}</strong>
          <span className="ink2">of high-risk cases drafted as high risk (baseline {pct(h.baseline.high_risk_recall)})</span>
        </div>
        <div className="figure">
          <strong>{h.checks.unsupported_flags_dropped}</strong>
          <span className="ink2">
            flags with missing or wrong evidence stopped before an analyst saw them; numbers corrected in{" "}
            {pct(h.checks.cases_with_wrong_number_corrected)} of drafts
          </span>
        </div>
        <div className="figure">
          <strong>{usd(h.chosen.cost_per_case_usd)}</strong>
          <span className="ink2">per case at list price (baseline {usd(h.baseline.cost_per_case_usd)})</span>
        </div>
      </div>
    </div>
  );
}
