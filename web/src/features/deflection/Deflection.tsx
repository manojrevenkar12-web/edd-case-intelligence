import type { Dashboard } from "../../app/types";
import { pct } from "../../shared/format";
import { space } from "../../theme/tokens";

export function Deflection({ data }: { data: Dashboard }) {
  const d = data.deflection;
  return (
    <div className="board">
      <table className="table">
        <caption className="ink2" style={{ textAlign: "left", paddingBottom: space[2] }}>
          {d.test.toLocaleString("en-GB")} new customers held out, {d.positives_test} of whom later became high-risk EDD cases. AUC{" "}
          {d.auc.toFixed(2)} for the model, {d.auc_rules.toFixed(2)} for the first-week rules.
        </caption>
        <thead>
          <tr>
            <th scope="col">Good customers asked for documents in week one</th>
            <th scope="col" className="r">Future high-risk cases stopped upstream (model)</th>
            <th scope="col" className="r">(rules)</th>
          </tr>
        </thead>
        <tbody>
          {d.model.map((m, i) => (
            <tr key={m.friction}>
              <td className="num">{pct(m.friction)} ({m.good_asked})</td>
              <td className="r num"><strong>{pct(m.recall, 0)}</strong> ({m.caught})</td>
              <td className="r num">{pct(d.rules[i]!.recall, 0)} ({d.rules[i]!.caught})</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
