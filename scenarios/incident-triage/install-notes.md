- **Evaluation final-answer check:** passes 0 of 15 runs on the development
  machine.  The tool-selection metrics are good (recall 1.0 in 13/15 runs), but
  `is_success` requires both tool and text checks to pass.  The text check fails
  because the agent writes IDs with non-breaking hyphens (U+2011) and produces
  long answers compared with one-line expectations.  Do not expect a green score.
- **Scene 6 of the demo script** references
  `evaluation/incident-triage/results/2026-10-16_11-37-26/summary_metrics.csv`
  which is from the development instance and is not in this zip.  Run the
  evaluation to produce your own results, or skip that part.
