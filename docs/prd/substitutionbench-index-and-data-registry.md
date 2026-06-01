# PRD: SubstitutionBench Index and Data Registry

## Problem Statement

SubstitutionBench needs to answer a specific model-selection question quickly:

> Which cheaper or smaller model is close enough to frontier quality for this task family, and what evidence supports that substitution?

The current prototype has useful raw ingredients, but the product destination is not yet durable enough. It needs one canonical hero metric, transparent index construction, trustworthy data provenance, and conflict handling across benchmark sources. Artificial Analysis provides strong current model/pricing/speed coverage, but it intentionally drops or stops refreshing saturated evals over time. That creates a product-specific data gap: saturated benchmarks are often where substitution signal is strongest.

If SubstitutionBench relies only on raw Artificial Analysis coverage, current frontier models can disappear from saturated benchmarks and the dashboard will lie by omission. If it averages every available benchmark row directly, domains with more benchmark fields get silent extra weight. If it merges conflicting scores without provenance, it creates fake precision.

## Target Users / Actors

- **Technical decision-maker** evaluating model spend from phone or laptop.
- **AI engineer / agent builder** choosing whether a cheaper model is good enough for a task family.
- **Local-inference user** who eventually wants to compare hosted API economics against consumer-GPU runtime cost.
- **SubstitutionBench maintainer / agent** curating benchmark sources, resolving conflicts, and regenerating static dashboard artifacts.

## Desired End-State

SubstitutionBench ships a mobile-friendly dashboard backed by a local SQLite benchmark registry.

The first screen shows one canonical hero chart:

- active index: **SubstitutionBench Index v1** by default;
- x-axis: model name;
- y-axis: average `% of frontier`;
- threshold: 95% default, continuously adjustable;
- bars sorted by `% of frontier` descending;
- vertical separator between qualifying and non-qualifying models;
- color encodes substitution state;
- cost panel ranks qualifying, cheaper substitutes by estimated API task cost.

Users can drill down into component indexes — General, Math, Coding, Agentic — without losing the one-hero-chart product spine. Each score shown in the dashboard is a resolved score with provenance, freshness, and conflict visibility.

## Solution

### Product Model

SubstitutionBench Index v1 is a composite index:

```text
SubstitutionBench Index v1 = average(
  General Index,
  Math Index,
  Coding Index,
  Agentic Index
)
```

Default component weights are equal:

- General: 25%
- Math: 25%
- Coding: 25%
- Agentic: 25%

Each component index is a curated, versioned basket of benchmarks. The top-level index averages component index values, not raw benchmark rows. This prevents benchmark-count weighting from giving a domain more influence merely because it has more available fields.

The score hierarchy is:

```text
benchmark score
→ benchmark % of frontier
→ component index % of frontier
→ SubstitutionBench Index % of frontier
```

### Scoring Grammar

For each benchmark:

- frontier anchor: average of the top 3 observed scores;
- benchmark ratio: `model_score / frontier_anchor`;
- component index value: average of benchmark ratios in the component basket;
- SubstitutionBench Index value: average of component index values.

Default qualification threshold:

```text
model index % of frontier >= 95%
```

A model is a usable substitute only if it is:

1. non-frontier;
2. at or above the selected `% of frontier` threshold;
3. cheaper than the frontier reference under the active cost model.

If no cheaper non-frontier model qualifies, the state is **frontier-bound / no substitute yet**. That is valid signal, not failure.

### Data Registry

SQLite is the canonical data store. CSV/JSON files may be generated for the static dashboard, but they are not the source of truth.

The database preserves three layers:

1. **Raw pulls** — source response body or pointer, endpoint/query, fetched timestamp, status, checksum.
2. **Normalized observations** — one row per `(source, model, benchmark, eval variant, score, date/protocol)` observation.
3. **Resolved scores** — one selected score per `(model, benchmark, index version)` used by indexes and charts, with a resolution reason and pointer to the winning observation.

Raw observations are evidence. Resolved scores are product data.

### Data Sources

Artificial Analysis is the preferred primary source for:

- current model roster;
- pricing;
- speed;
- actively maintained benchmark fields.

Artificial Analysis is not enough by itself because it drops or stops updating saturated evals. Supplemental sources are allowed and expected for backfill, especially when evaluating current SOTA models on saturated benchmarks.

Initial supplemental source candidates:

- Hugging Face Open LLM Leaderboard results datasets;
- Hugging Face leaderboard Spaces/datasets;
- LiveCodeBench public JSON;
- SWE-bench leaderboard JSON;
- BigCode / code leaderboards;
- HELM / academic aggregators;
- original benchmark leaderboards and papers.

Every supplemental observation must carry:

- source URL;
- eval date or publication date;
- model variant / reasoning effort;
- benchmark version;
- eval protocol or scaffold notes;
- trust level;
- freshness label.

### Conflict Resolution

SubstitutionBench preserves all observations and resolves scores through explicit source hierarchy rules.

Conflict policy:

- never overwrite a prior observation just because a newer source disagrees;
- never silently average incompatible eval protocols;
- use preferred-source hierarchy per benchmark;
- average only when protocol equivalence is established;
- expose conflict count and source disagreement in detail UI;
- resolved score must point back to the winning observation and explain why it won.

Examples:

- For LiveCodeBench, prefer official LiveCodeBench JSON over an aggregator if protocol-equivalent values differ.
- For SWE-bench, use official SWE-bench rows but label them `agent-scaffolded`; do not treat them as pure model ability.
- For Artificial Analysis-maintained fields, use AA unless the official benchmark source is fresher and protocol-equivalent.

## User Stories

1. As a technical decision-maker, I want one default SubstitutionBench Index chart, so I can quickly see which models are close enough to frontier.
2. As a model-selection user, I want qualified models ranked by estimated task cost, so I can pick the cheapest acceptable substitute.
3. As a skeptical user, I want to see when no substitute exists, so I do not incorrectly downshift from a frontier model.
4. As a user comparing domains, I want drilldowns for General, Math, Coding, and Agentic indexes, so I can understand why a model qualifies or fails overall.
5. As a maintainer, I want raw source pulls cached locally, so the product does not repeatedly hit APIs or lose reproducibility.
6. As a maintainer, I want all conflicting observations preserved, so source disagreements are transparent rather than hidden.
7. As a user, I want missing saturated evals labeled unknown/stale rather than treated as failures, so current SOTA models are not unfairly excluded.

## Success Criteria

- Dashboard has one default hero chart for SubstitutionBench Index v1.
- Hero chart uses `% of frontier`, not point-gap/JND grammar.
- SubstitutionBench Index v1 averages component indexes rather than raw benchmark rows.
- General, Math, Coding, and Agentic component drilldowns use the same chart grammar.
- Qualification threshold defaults to 95% and can be adjusted continuously.
- Sorted bar chart includes a vertical separator between qualifying and non-qualifying models.
- Bar state colors mean:
  - Violet: frontier context / frontier anchor;
  - Green: qualifies and is cheaper;
  - Amber: qualifies but is not an economic substitute;
  - Red/Gray: below cutoff.
- Cost ranking uses estimated API task cost for MVP.
- SQLite stores raw pulls, normalized observations, resolved scores, index versions, and pricing observations.
- Dashboard/index generation consumes resolved scores only.
- Source freshness, missing coverage, and conflicts are visible in the analysis/source transparency area.
- Missing saturated evals are represented as unknown/stale coverage, not as below-threshold model performance.

## Constraints / Non-Negotiables

- Do not call Artificial Analysis or other credentialed APIs from client-side dashboard code.
- Do not expose API keys in static assets, git, browser code, or local network preview URLs.
- Do not collapse incompatible benchmark protocols into one average.
- Do not silently discard conflicting source observations.
- Do not treat SWE-bench agent scaffold results as pure model scores.
- Do not curate indexes to avoid “no substitute yet” results.
- Do not let benchmark-count imbalance determine component weights accidentally.
- Keep the dashboard mobile-friendly and scannable from Telegram/Android.
- Prefer TDD and vertical slices for implementation.

## Key Product / Technical Decisions

### Decision: Use `% of frontier` as the primary quality metric

- **Why:** It directly answers whether a model is close enough to frontier quality.
- **Alternatives rejected:** point-gap/JND as default grammar; raw leaderboard score as primary product metric.
- **Status:** accepted.

### Decision: Frontier anchor defaults to top-3 average

- **Why:** A single top row may be stale, lucky, or differently configured. Top-3 average is more robust while still representing practical frontier.
- **Alternatives rejected:** single best score; fixed named frontier model only.
- **Status:** accepted.

### Decision: Use a vertical separator after sorting by `% of frontier`

- **Why:** The separator delineates membership in the qualifying set. A horizontal line would encode the numeric threshold but does not show the boundary as clearly after sorting.
- **Alternatives rejected:** horizontal-only threshold line.
- **Status:** accepted.

### Decision: Substitution requires quality and economics

- **Why:** Close but expensive is not a substitute. Cheap but below frontier threshold is not safe.
- **Alternatives rejected:** quality-only qualification; cheapest-model leaderboard.
- **Status:** accepted.

### Decision: SubstitutionBench Index v1 is a composite of component indexes

- **Why:** Preserves one hero metric while avoiding flat benchmark soup and silent benchmark-count weighting.
- **Alternatives rejected:** one arbitrary raw benchmark basket; multiple unrelated hero charts; direct average of every benchmark row.
- **Status:** accepted.

### Decision: Artificial Analysis is primary but not exclusive

- **Why:** AA is strong for current roster, pricing, speed, and active evals, but it intentionally drops saturated evals over time.
- **Alternatives rejected:** AA-only complete coverage rule for all benchmarks.
- **Status:** accepted.

### Decision: SQLite is canonical data registry/cache

- **Why:** Prevents repeated API calls, preserves raw evidence, enables conflict transparency, and makes generated dashboard artifacts reproducible.
- **Alternatives rejected:** CSV/JSON files as canonical data store; direct API-to-dashboard flow.
- **Status:** accepted.

### Decision: Dashboard consumes resolved scores only

- **Why:** Raw observations are evidence; resolved scores are product data. This keeps charts deterministic and auditable.
- **Alternatives rejected:** every chart independently choosing/averaging source rows.
- **Status:** accepted.

## Feature-Level Evidence Expectations

### Test expectations

- Unit tests for score ratio calculation against top-3 frontier anchor.
- Unit tests for component index and SubstitutionBench Index aggregation.
- Unit tests for complete-coverage and unknown/stale coverage behavior.
- Unit tests for substitution state classification: frontier, qualifying-cheaper, qualifying-expensive, below cutoff.
- Unit tests for conflict resolution source hierarchy.
- Integration test that generates static dashboard data from SQLite resolved scores.
- Regression test that `.env` and API keys are never emitted into generated dashboard assets.

### Visual/manual expectations

- Mobile screenshot of default SubstitutionBench Index v1 hero chart.
- Mobile screenshot showing component drilldown using the same chart grammar.
- Screenshot/state proving “no substitute yet” is explicit and not hidden.
- Screenshot/state showing source transparency: cache freshness, source mix, missing coverage, conflict count.
- Example model detail showing resolved score, source, freshness, and conflicting observations.

### Data/evidence expectations

- SQLite database can be queried for raw AA fetch metadata.
- SQLite database can show multiple observations for the same model/benchmark when sources conflict.
- Generated static artifact can be traced back to resolved scores.
- AA pull count/rate-limit behavior is cached and does not repeat unnecessarily.

## Out of Scope

- Public marketing landing page.
- Full research report.
- Local GPU/electricity cost mode for MVP.
- Custom user-weighted component indexes for MVP.
- Full automated ingestion of every possible benchmark source.
- Claiming benchmark rows are equivalent without protocol review.
- GitHub issue decomposition; that belongs in the next `to-issues` phase.
- Production multi-user backend.

## Source Context / Links

- Product context: `PRODUCT.md`
- Design notes: `DESIGN.md`
- Current static dashboard: `docs/index.html`, `docs/app.js`, `docs/styles.css`, `docs/data.js`
- Artificial Analysis fetch script: `scripts/fetch_artificial_analysis.py`
- Artificial Analysis raw/flat data: `data/artificial_analysis/`
- Current PRD: `docs/prd/substitutionbench-index-and-data-registry.md`

## Further Notes

Current prototype code still contains old JND/point-gap grammar in places. The PRD destination supersedes that language: the product grammar is `% of frontier` with a 95% default threshold.

Some pricing values from Artificial Analysis appear as zero and require normalization before cost ranking can be trusted. Zero must not automatically mean free.

Saturated benchmark gaps should be treated as coverage/freshness issues. They should not disqualify current frontier models without explanation.
