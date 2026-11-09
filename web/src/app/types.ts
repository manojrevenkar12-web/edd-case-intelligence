export interface Eval {
  flag_precision: number;
  flag_recall: number;
  risk_accuracy: number;
  high_risk_recall: number;
  case_correct: number;
  no_draft_rate: number;
  cost_per_case_usd: number;
  p95_latency_ms: number;
  case_correct_ci: [number, number];
  high_risk_recall_ci: [number, number];
  failure_modes: Record<string, number>;
}

export interface Test {
  effect: number;
  ci: [number, number];
  p_one_sided: number;
  confirmed: boolean;
  n: number;
}

export interface Experiment {
  id: string;
  hypothesis: string;
  metric: string;
  direction: "greater" | "less";
  dev: Test;
  heldout: Test;
}

export interface Week {
  week: number;
  config: string;
  factual_edit_rate: number;
  edit_ucl: number | null;
  case_correct: number;
  crypto_recall: number | null;
  alerts: string[];
}

export interface Policy {
  friction: number;
  recall: number;
  caught: number;
  good_asked: number;
}

export interface Dashboard {
  chosen_config: Record<string, string | number | boolean>;
  agreement: { heldout: { cases: number; disagreements: number; risk: number; flags: Record<string, number> } };
  experiments: Experiment[];
  heldout: {
    baseline: Eval;
    chosen: Eval;
    without_checks: Eval;
    lift: { effect: number; ci: [number, number] };
    checks: { unsupported_flags_dropped: number; cases_with_unsupported_flag_without_checks: number; cases_with_wrong_number_corrected: number };
  };
  production: { weeks: Week[]; first_alert_week: number | null; false_alert_weeks: number; promoted_week: number | null };
  deflection: { customers: number; test: number; positives_test: number; auc: number; auc_rules: number; model: Policy[]; rules: Policy[] };
}
