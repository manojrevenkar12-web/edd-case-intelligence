import { motion, useReducedMotion } from "framer-motion";
import { Deflection } from "../features/deflection/Deflection";
import { Experiments } from "../features/experiments/Experiments";
import { Labels } from "../features/labels/Labels";
import { Overview } from "../features/overview/Overview";
import { Production } from "../features/production/Production";
import { Section } from "../shared/Section";
import { ErrorState, Skeleton } from "../shared/states";
import { chart, font, motion as m, space } from "../theme/tokens";
import type { Dashboard } from "./types";
import { useJson } from "./useData";

export function App() {
  const load = useJson<Dashboard>("dashboard.json");
  const reduce = useReducedMotion();
  return (
    <main className="page">
      <motion.header initial={reduce ? false : { opacity: 0, y: space[2] }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: m.base, ease: m.ease }}>
        <h1 style={{ fontSize: font.size.xxxl }}>Enhanced due diligence drafts, measured</h1>
        <p className="lede measure">
          A model drafts the case summary, the red flags with the transfers that show them, the risk class and the documents
          to request. Code checks every claim; an analyst decides. Every number below comes from cases the model and the
          prompts were never tuned on.
        </p>
      </motion.header>
      {load.state === "loading" && (
        <div className="section">
          <Skeleton height={chart.skeleton} lines={3} label="Loading results" />
        </div>
      )}
      {load.state === "error" && (
        <div className="section">
          <ErrorState what="The results" message={load.message} onRetry={load.retry} />
        </div>
      )}
      {load.state === "ready" && (
        <>
          <Section id="held" title="On 900 held-out cases">
            <Overview data={load.data} />
          </Section>
          <Section id="exp" title="Seven hypotheses, written before the run"
            lede="Each experiment changes one thing in the prompt or the pipeline. Estimated on the development split, then tested once on the held-out split with a Holm correction.">
            <Experiments experiments={load.data.experiments} />
          </Section>
          <Section id="prod" title="Twelve weeks in production" lede="Monitoring from what production records: case features, the drafts, and the analysts' edits.">
            <Production data={load.data} />
          </Section>
          <Section id="defl" title="Stopping cases before they reach the team" lede="A first-week model asks a few customers for documents early, judged as a policy.">
            <Deflection data={load.data} />
          </Section>
          <Section id="labels" title="Where the labels come from">
            <Labels data={load.data} />
          </Section>
        </>
      )}
    </main>
  );
}
