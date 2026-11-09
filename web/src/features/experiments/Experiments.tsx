import type { Experiment } from "../../app/types";
import { EmptyState } from "../../shared/states";
import { space } from "../../theme/tokens";
import { Forest } from "./Forest";

export function Experiments({ experiments }: { experiments: Experiment[] }) {
  if (experiments.length === 0) return <EmptyState title="No experiments registered.">Add one to experiments/registry.yaml.</EmptyState>;
  const confirmed = experiments.filter((e) => e.heldout.confirmed);
  return (
    <div className="board">
      <Forest experiments={experiments} />
      <p className="ink2 measure" style={{ marginTop: space[4] }}>
        Confirmed on the held-out split: {confirmed.map((e) => e.hypothesis).join(" ")} Not confirmed:{" "}
        {experiments.length - confirmed.length} of {experiments.length}, including putting computed facts first and more
        worked examples, which looked promising or neutral on the development split.
      </p>
    </div>
  );
}
