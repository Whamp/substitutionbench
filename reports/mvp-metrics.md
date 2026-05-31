# SubstitutionBench MVP Metrics

> Generated from `data/benchmark_observations.csv` using `scripts/build_mvp_metrics.py`.

## MVP metric definitions

- **Frontier score:** pinned top/reference score for the benchmark version/date.
- **Frontier Coverage %:** `model_score / frontier_score * 100`.
- **JND-equivalent:** model is within the configured percentage-point threshold of the frontier score.
- **Cheapest equivalent:** lowest input $/M token model inside the JND-equivalent band.
- **Smallest equivalent:** lowest known active-parameter count, falling back to total parameters, inside the JND-equivalent band.
- **Threshold sensitivity:** recompute the floor at 1, 3, and 5 percentage-point JND bands so the conclusion does not depend on one arbitrary cutoff.

## Benchmark substitution floors

### GPQA Diamond

- Frontier: **Gemini 3.1 Pro Preview** at **94.1%**
- JND band: within **3 percentage points**
- Cheapest equivalent: **Qwen3.7 Max** at **$1.25/M input**, score **92.4%**, coverage **98.2%**
- Smallest equivalent: not available in current parameter data

### MATH-500

- Frontier: **GPT-5 high** at **99.4%**
- JND band: within **3 percentage points**
- Cheapest equivalent: **Qwen3 30B A3B Thinking** at **$0.08/M input**, score **97.6%**, coverage **98.2%**
- Smallest equivalent: **Qwen3 30B A3B Thinking** at **3B params**

### SWE-bench Verified

- Frontier: **Claude Opus 4.8** at **88.6%**
- JND band: within **3 percentage points**
- Cheapest equivalent: **Claude Opus 4.8** at **$5.0/M input**, score **88.6%**, coverage **100.0%**
- Smallest equivalent: not available in current parameter data

## Plots

- `reports/plots/cheapest-equivalent.svg`
- `reports/plots/math-500-substitution-curve.svg`
- `reports/plots/gpqa-diamond-substitution-curve.svg`
- `reports/plots/swe-bench-verified-substitution-curve.svg`

## Generated CSVs

- `data/mvp_metrics.csv` — per-row frontier coverage and JND-equivalence flags.
- `data/mvp_substitution_floors.csv` — cheapest/smallest equivalent at configured benchmark thresholds.
- `data/mvp_threshold_sensitivity.csv` — floor recomputed at 1/3/5 point thresholds.

## Caveats

- This is an MVP from currently gathered public rows, not the final canonical dataset.
- Eval mode matters. Thinking/xhigh/non-thinking rows are deliberately kept separate.
- Some rows are aggregator/vendor/community quality and need confirmation before publication-grade claims.
- Saturation is treated as positive signal: the point is to find the floor, not crown the frontier winner.
