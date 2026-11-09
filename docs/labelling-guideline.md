# Labelling guideline (v2)

For the EDD SMEs who label the golden set. The definitions are in `config/taxonomy.yaml`; this page says how to
apply them.

1. **A flag is an indicator, not a finding.** Record it when its definition is met, with the transfer ids that
   show it, even when the customer's business explains it. The explanation goes into the risk class.
2. **Risk.** Add the severities of the flags present. A flag counts as mitigated only when the declared business
   explains it *and* the business documents are on file.
3. **Profile mismatch** is the open definition: record it when monthly volume is three or more times the
   declared amount, or when the activity (many unrelated payers, exchange top-ups) is at odds with a declared
   occupation such as student or retail assistant. Two SMEs agree on it less than on any other flag
   (Cohen's kappa 0.73 on the held-out set); disagreements go to the senior reviewer.
4. **Documents.** One per flag kept, from the taxonomy; none when the risk is low.
