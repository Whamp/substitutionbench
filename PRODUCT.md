# SubstitutionBench Product Context

## Product

SubstitutionBench is an inverse benchmark for LLM model selection. It asks: which cheaper or smaller model is close enough to the frontier on a specific task family?

## Primary user

A technical decision-maker evaluating model spend from a phone or laptop. They need to trust the substitution story quickly without reading source data or code.

## Shipping definition

For a given task family, SubstitutionBench ships the universe of models that are close enough to frontier quality, ranked by cost.

Example: for MATH-500-style math, show every available model whose score is at least the selected percentage of frontier quality, then rank those models by the cost required to complete that task family.

The default qualification threshold is **95% of frontier score**. Users must be able to change it continuously, not only through fixed presets. Values like 93% and 90% should work because the acceptable substitution band depends on use case and risk tolerance.

The product is not asking for more chart types. It is asking for better encodings of the substitution-relevant metrics across the model universe.

## Dashboard job

The MVP dashboard should make five facts obvious within seconds:

1. Across the selected SubstitutionBench index, which models have the strongest `% of frontier` score.
2. For a selected task family, which models are within the selected frontier-quality threshold.
3. Which qualifying model is cheapest for that selected task family under API pricing.
4. How quality, API cost, speed, and size trade off across all available models.
5. Which benchmarks and sources are included in the selected index and model universe.

## Indexes and chart spine

The hero chart should use a controlled **SubstitutionBench Index**, not a raw average across every benchmark row in the database.

The default **SubstitutionBench Index v1** is a composite average of component indexes:

- **General Index** — broad intelligence, knowledge, and reasoning tasks.
- **Math Index** — mathematical reasoning tasks.
- **Coding Index** — code generation, repair, and software reasoning tasks.
- **Agentic Index** — tool use, terminal work, instruction following, and task execution.

Each component index is a curated, versioned benchmark basket. The top-level SubstitutionBench Index averages the component index values, not the raw benchmark rows. This prevents one domain from receiving more weight merely because more benchmark fields are available for that domain.

The hierarchy is:

1. benchmark score;
2. benchmark `% of frontier`;
3. component index `% of frontier`;
4. SubstitutionBench Index `% of frontier`.

The default v1 weighting is equal component weight: **25% General, 25% Math, 25% Coding, 25% Agentic**. Component weights may become configurable later, but the default product claim should stay explicit and versioned.

SubstitutionBench must clearly show both substitutable and non-substitutable task families.

If no model clears the selected `% of frontier` threshold for a task family or component index, the correct conclusion is: **no substitute for frontier on this task yet**. That is useful signal and must not be hidden by curating easier benchmarks or weakening the threshold.

Indexes are curated for stability and control, not to avoid hard realities. A curated index may include benchmarks where no cheaper substitute exists; the UI should make that frontier-bound status obvious.

The hero chart is a bar chart across the model universe for the active index:

- x-axis: model name;
- y-axis: index `% of frontier`;
- default active index: SubstitutionBench Index v1;
- alternate active indexes: General, Math, Coding, Agentic;
- benchmark baskets: curated and versioned;
- frontier anchor per benchmark: average of the top 3 observed scores;
- model score ratio per benchmark: `model_score / frontier_anchor`;
- component index value: average of benchmark ratios across the benchmarks included in that component;
- SubstitutionBench Index value: average of component index values;
- eligibility: a model must satisfy the selected index coverage rule to appear in that index.

Per-benchmark charts use the same grammar:

- x-axis: model name;
- y-axis: `% of frontier` for the selected benchmark;
- ordering: sort models by `% of frontier` descending;
- threshold separator: after sorting models by `% of frontier`, show a vertical divider between qualifying and non-qualifying models;
- substitution rule: a task has a substitute only when at least one non-frontier model clears the selected `% of frontier` threshold and is cheaper than the frontier reference under API pricing.

## Frontier definition

The default frontier anchor is the **average of the top 3 observed scores for the selected task family**.

Why: one lucky, stale, or differently configured top row can distort the qualification threshold. A top-3 average dampens outliers while still representing the practical frontier.

The top observed model should still be displayed as context, but it should not be the default denominator for the substitution threshold.

## Data sources

Artificial Analysis should be a primary source for MVP model/benchmark data where available, especially for current model metadata, pricing, speed, and actively maintained benchmark fields.

Artificial Analysis is not sufficient as the only long-term source of truth for SubstitutionBench because it intentionally drops or stops updating saturated evaluations over time. That is reasonable for an intelligence leaderboard, but it creates a data gap for SubstitutionBench: saturated benchmarks are often exactly where substitution signal is strongest.

Data source policy:

- Use Artificial Analysis for current model roster, pricing, speed, and benchmark fields it actively maintains.
- Track benchmark freshness per model/field, especially for frontier models like GPT-5.5 and Claude Opus 4.8.
- Treat missing saturated-eval rows as **unknown**, not as failure or below-threshold performance.
- Allow supplemental sources for saturated benchmark results when AA has stopped updating a field.
- Store raw source pulls and normalized benchmark observations in a local SQLite database so API calls are cached, reproducible, and inspectable.
- Display source, date/freshness, and coverage state so stale or partial index values do not masquerade as current evidence.
- Maintain a source registry with trust tiers rather than merging all benchmark rows as if they are equally reliable.
- Preserve conflicting observations rather than overwriting them; the UI should explain which source won resolution and where alternatives disagree.

Initial supplemental source candidates:

- **Hugging Face Open LLM Leaderboard results dataset** — useful for open-model historical eval results and reproducible `lm-eval-harness` artifacts; treat as stronger for open weights than for closed frontier APIs.
- **Hugging Face leaderboard Spaces/datasets** — useful for community and domain-specific leaderboards, but require per-source trust assessment.
- **LiveCodeBench** — exposes leaderboard data as JSON and is useful for time-sliced coding performance.
- **SWE-bench** — exposes leaderboard data with agent/model results, resolved rates, dates, and costs; useful for software-agent substitution, but agent scaffolding must be separated from base model ability.
- **BigCode / code leaderboards** — useful for coding model coverage where benchmark versions and execution setup are clear.
- **HELM / academic benchmark aggregators** — useful for reproducible historical benchmark rows and source triangulation.
- **Original benchmark leaderboards or papers** — useful when they provide model-specific scores, eval version, prompt protocol, and date.

Relevant API facts verified from `https://artificialanalysis.ai/api-reference`:

- endpoint: `GET https://artificialanalysis.ai/api/v2/data/llms/models`;
- authentication: `x-api-key` header;
- free API includes independent model benchmarks, speed benchmarks, and pricing;
- rate limit: 1,000 requests/day;
- required attribution: link to `https://artificialanalysis.ai/`;
- useful fields include stable model IDs, creator IDs, benchmark evaluations, pricing, median output tokens/sec, and latency.

Do not call the Artificial Analysis API from client-side dashboard code. Fetch/cache server-side or during data-generation scripts so API keys and rate limits are not exposed.

## Data store and conflict transparency

SubstitutionBench should use SQLite as the local benchmark registry and cache. CSV/JSON exports may power the static dashboard, but they should be generated artifacts, not the canonical store.

The database should preserve three layers:

1. **Raw pulls** — source response body, source name, endpoint/query, fetched timestamp, status, and checksum. This prevents repeated API calls and makes every generated dataset reproducible.
2. **Normalized observations** — one row per `(source, model, benchmark, eval variant, score, date/protocol)` observation. Multiple rows for the same model/benchmark are allowed.
3. **Resolved scores** — one selected score per `(model, benchmark, index version)` used for chart/index calculation, with a resolution reason pointing back to the winning observation.

Conflict handling should be explicit:

- never overwrite a prior observation just because a newer source disagrees;
- never silently average scores from incompatible eval protocols;
- record all candidate observations and mark the resolved winner;
- expose conflict count/source disagreement in the model or benchmark detail UI;
- allow manual source hierarchy rules per benchmark when source reliability differs.

Minimum tables/concepts:

- `sources` — source identity, trust tier, URL, license/attribution notes.
- `fetch_runs` — source pulls, timestamps, endpoint/query, status, checksum, raw path/body pointer.
- `models` — canonical model identity plus aliases across sources.
- `benchmarks` — canonical benchmark identity, version, domain/component index, saturation/freshness policy.
- `benchmark_observations` — source score rows with score, units, date, eval mode, reasoning effort, scaffold/agent flag, source URL.
- `benchmark_resolutions` — selected score, resolution policy, winner observation, conflicting observation count.
- `index_versions` and `index_components` — versioned baskets and component weights.
- `pricing_observations` — source-specific input/output/blended pricing with date and billing assumptions.

## Cost model direction

API price is the MVP cost model.

Future cost should support local inference economics for consumer-grade GPUs, but this is explicitly out of scope for the MVP. Local hardware cost mode should only consider models below a configurable size/fit threshold, because large models that cannot realistically run on the user's hardware should not be eligible for local-cost ranking.

Future local inference economics should include:

- task token volume required to complete the benchmark/task family;
- model generation speed in tokens per second;
- wall-clock generation time;
- GPU power draw;
- electricity price per kWh;
- resulting local cost per task and effective local cost per token.

The primary ranking metric is **estimated task cost**:

- API mode: `(input tokens × input price) + (output tokens × output price)`;
- future local mode: `runtime hours × GPU watts ÷ 1000 × electricity $/kWh`, only for models that fit the selected hardware threshold;
- supporting labels: `$ / 1M tokens`, runtime, tok/s, power draw, and model size.

`$/1M tokens` is an input assumption. Estimated task cost is the user-facing answer.

Configurable assumptions should include at least:

- hardware profile or custom GPU power draw;
- model throughput for that hardware, measured or estimated;
- electricity rate;
- benchmark/task token volume;
- API pricing source when using hosted inference.

Smart defaults are acceptable only if every displayed local-cost number makes its assumptions visible and editable.

Example: if MATH-500 takes 3M output tokens and a model generates 60 tok/s, inference takes about 13.9 hours. At 230W and $0.14/kWh, electricity cost becomes an alternate model-cost estimate that may be more relevant than API pricing for local users.

## Register

Product dashboard. Design serves decision-making. It should feel closer to Linear, Stripe dashboards, or a quant research terminal than a marketing page.

## Tone

Precise, terse, skeptical. Avoid hype. Use benchmark language consistently: task family, frontier anchor, frontier score ratio, qualification threshold, substitution floor, in-band, outside band.

## Anti-goals

- Not a public landing page yet.
- Not a full research report.
- Not a leaderboard crowning the smartest model.
- Not a giant table that requires desktop inspection.
