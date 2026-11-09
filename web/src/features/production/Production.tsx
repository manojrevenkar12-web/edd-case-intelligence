import type { Dashboard } from "../../app/types";
import { EmptyState } from "../../shared/states";
import { space } from "../../theme/tokens";
import { EditChart } from "./EditChart";

export function Production({ data }: { data: Dashboard }) {
  const p = data.production;
  if (p.weeks.length === 0) return <EmptyState title="No production weeks yet.">Run make dev.</EmptyState>;
  const newWeek = 7;
  return (
    <div className="board">
      <EditChart weeks={p.weeks} newTypologyWeek={newWeek} promotedWeek={p.promoted_week} />
      <p className="ink2 measure" style={{ marginTop: space[4] }}>
        A mule typology paid as "orders" and emptied to exchanges the examples never showed arrives in week {newWeek}. The edit
        rate crosses its limit the same week (alert in week {p.first_alert_week}; {p.false_alert_weeks} false alerts before
        it). A candidate with updated examples runs in shadow on weeks 8 and 9, passes the gate and serves from week{" "}
        {p.promoted_week}.
      </p>
    </div>
  );
}
