# SubstitutionBench

**The cost-optimization LLM benchmark.**

Most benchmarks answer: *"Which model is the smartest?"*
SubstitutionBench answers: *"How cheap can you go before anyone notices?"*

## The Problem

Using a frontier model (GPT-5.5, Claude-Opus) for git commits, high school math, summarization, or basic QA is a waste of intelligence and money. A smaller, cheaper, or local model often produces output that is functionally indistinguishable — but nobody tells you which model, or for which tasks.

## The Idea

SubstitutionBench measures **Frontier Coverage**: for each task category, what is the smallest/cheapest model whose output is nearly indistinguishable from a frontier reference model? The output is a **substitution curve** per task — not a single ranking.

- A 7B model covering 90% of HellaSwag is *interesting signal* — it means you can run that task class on a consumer gaming GPU for the cost of electricity.
- A 70B model covering 78% of code tasks tells you the substitution floor for code generation.
- The curve itself is the contribution: where does quality plateau relative to cost?

## Approach: Build on Saturated Benchmarks

Rather than designing tasks from scratch, SubstitutionBench converts existing saturated benchmarks into substitution curves. Saturated benchmarks already solved the hard problems: task design, evaluation rubrics, and answer validation. We flip the question from "What's the max score?" to "At what cost/size does the score hit the JND threshold from ceiling?"

### Candidate Benchmark Sources

| Domain | Benchmarks | Why |
|--------|-----------|-----|
| Retrieval & Comprehension | MMLU-Pro, TriviaQA, HellaSwag, WinoGrande | Likely high coverage even for small models |
| Code & Structured Output | HumanEval, MBPP, LiveCodeBench | Binary pass/fail — clean substitution point |
| Math | GSM8K, MATH (tiered subsets) | Sharply stratified by difficulty |
| Language & Summarization | CNN/DM, XSum, translation benches | Likely high coverage |
| Creative & Conceptual | MT-Bench, ArenaHard, writing benchmarks | Likely low coverage, more subjective |
| Agentic & Multi-step | GAIA, τ²-Bench, tool-use benchmarks | Likely lowest coverage |

## Formal Grounding

Three economics/psychology frameworks map onto this benchmark:

1. **Weber's Law / Just Noticeable Difference (JND)** — the minimum detectable difference between two stimuli, detected 50% of the time. Applied here: at what point can a human evaluator *not reliably distinguish* frontier output from candidate output?

2. **Vertical Differentiation** — economic models where products differ in quality, not just price. Consumers sort along a quality spectrum; there's always a "good enough" segment. The benchmark identifies where on the spectrum the substitution point falls per task type.

3. **Diminishing Marginal Returns to Quality** — each additional unit of model intelligence yields smaller perceptible improvements. The "substitution point" is where the derivative effectively hits zero.

## Metrics & Aggregation Structure

### MVP Artifacts

Current MVP data/plot generator:

```bash
python -m pytest tests -q
python scripts/build_mvp_metrics.py
python scripts/build_site.py
python -m http.server 8765 --directory docs
```

Generated outputs:

- `data/mvp_metrics.csv` — per-model benchmark rows with Frontier Coverage %, score gap, and JND-equivalent flag.
- `data/mvp_substitution_floors.csv` — cheapest/smallest frontier-equivalent model per benchmark at configured thresholds.
- `data/mvp_threshold_sensitivity.csv` — substitution floor recomputed at 1/3/5 percentage-point JND thresholds.
- `reports/mvp-metrics.md` — human-readable MVP summary.
- `reports/plots/*.svg` — static SVG substitution curves and cheapest-equivalent summary.
- `docs/` — mobile-friendly static website dashboard fed by generated `docs/data.js`.

### Top-Level: Frontier Coverage %

What percentage of the tested task space can a given model handle at frontier quality? A 7B model might cover 45%. A 70B model might cover 78%. The frontier reference model is 100% by definition.

### Domain Sub-Aggregates

Coverage % per domain, each with its own substitution floor:

- **Retrieval & Comprehension** — expected high coverage
- **Code & Structured Output** — moderate, bifurcated by complexity
- **Math** — sharply stratified by difficulty tier
- **Language & Summarization** — expected high coverage
- **Creative & Conceptual** — expected low coverage
- **Agentic & Multi-step** — expected lowest coverage

### Per-Benchmark

Individual substitution curves (model size/cost vs quality score).

### Per-Model Cards

"This model covers X% of tasks, strongest in Y, weakest in Z. Substitution floor: $N/M tokens."

## Inverse View: Substitution Ceiling

For a given model tier, what's the maximum task coverage? "A 7B model can substitute for frontier on 62% of tested tasks." This number grows over time as small models improve — it's the progress indicator.

The ceiling is bounded by the task taxonomy, not by a platonic definition of "all tasks." We should be explicit: "Substitution Ceiling covers N benchmarks across M task categories."

## Design Decisions (Open)

- **JND threshold definition per category** — What counts as "nearly indistinguishable" for code (binary) vs summarization (gradient) vs creative (subjective)?
- **Evaluation mode** — LLM-as-judge (fast but biased), human eval (gold standard but expensive), automated metrics (clean for verifiable tasks), paired comparison (most robust)?
- **Frontier reference model pinning** — Pin per benchmark version (e.g., "Claude-4-class as of Q2 2026") rather than tracking a moving target.
- **Tail risk** — Report both mean coverage AND failure rate. A model matching frontier 90% of the time but hallucinating 10% is different from one matching 85% consistently.

## Related Work

| Work | Relevance | Gap |
|------|-----------|-----|
| [Sustainability via LLM Right-sizing](https://arxiv.org/abs/2504.13217) (Haase et al., 2025) | Closest concept: "When is a smaller model good enough?" 11 models, 10 occupational tasks | Academic study, not a reusable benchmark. LLM-as-judge, not human indistinguishability. Doesn't produce substitution curves. |
| [LLMRouterBench](https://arxiv.org/abs/2601.07206) (2026) | Quality-cost Pareto frontier analysis, 400K instances, 33 models | About routing individual queries, not finding minimum sufficient model per task category. Engineering artifact, not substitution measurement. |
| [Unified Routing & Cascading](https://arxiv.org/abs/2410.10347) (De Koninck et al., ICML 2025) | Cascade routing: 45-85% cost savings maintaining 95% quality | Engineering solution (start cheap, escalate on failure), not a benchmark measuring substitution floors. |
| [Factory Router](https://factory.ai/news/factory-router) (Factory, 2026) | Commercial proof that per-session model routing can preserve near-frontier engineering pass rates while cutting full-session cost 20-25%; see [`docs/research/factory-router-study.md`](docs/research/factory-router-study.md) | Product/router layer, not neutral public benchmark. Terminal-Bench 2.0 is public; full Legacy-Bench is controlled/vendor-access. |

**No existing benchmark measures JND-based indistinguishability between frontier and cheaper models across task categories, outputting substitution curves with per-domain substitution floors.**

## License

MIT
