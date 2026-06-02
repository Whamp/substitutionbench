# Saturated Benchmarks and Source Audit

Status: working policy for issue #9  
Date: 2026-06-01  
Scope: benchmark selection, saturated-benchmark handling, and source reconnaissance for the next SubstitutionBench index revision.

## Core correction

The first implementation used Artificial Analysis aggregate indexes as component definitions:

- General = AA Intelligence Index
- Math = AA Math Index
- Coding = AA Coding Index + LiveCodeBench
- Agentic = τ²-bench + Terminal-Bench Hard + IFBench

That is the wrong ontology for SubstitutionBench. Artificial Analysis is a useful source, but its aggregate indexes should not define SubstitutionBench's task-family baskets.

SubstitutionBench should be benchmark-first:

> Use task-representative benchmarks to find the cheapest/smallest model that is close enough to frontier for that task family.

Saturated benchmarks are not noise. They are often the strongest substitution signal.

## Saturated benchmark policy

### Why saturated benchmarks matter

A saturated benchmark represents a task class that is plausibly solved for frontier systems. That is exactly where substitution is economically interesting:

- Frontier quality is no longer meaningfully differentiated.
- Many cheaper/smaller/local models may sit inside the acceptable quality band.
- The benchmark becomes less useful for ranking frontier models and more useful for finding the substitution floor.

A saturated benchmark asks:

> What is the cheapest model that clears the solved-task threshold?

Not:

> Which frontier model is marginally smarter?

### The staleness problem

The same thing that makes a benchmark useful for substitution also makes leaderboards stop caring about it. Once a benchmark saturates, current frontier models are often not run on it anymore. Sources may:

- drop the benchmark from the current leaderboard;
- freeze old rows;
- omit new frontier models entirely;
- keep older non-frontier rows that are still useful for substitution.

Treating missing current-frontier rows as bad performance is wrong. Treating them as unknown is honest but can make the index unusable. SubstitutionBench needs an explicit assumption policy.

## Saturation classification

A benchmark is `saturated` if it meets at least two of these conditions:

1. **Ceiling ratio:** top-3 average frontier anchor is at least 95% of the known/theoretical ceiling, or at least 95% of the empirical ceiling when no theoretical ceiling is available.
2. **Compressed top:** gap between observed #1 and #3 is no more than 2 percentage points.
3. **Crowded frontier band:** at least 5 non-frontier models are within 1 percentage point of the frontier anchor, or at least 10 models are within the default 95% threshold.

A benchmark is `fully_saturated` if it meets all three.

A benchmark is `active_unsaturated` if it fails these conditions and still discriminates frontier performance.

A benchmark is `stale_protocol` if the benchmark/harness/question set changed enough that old rows are no longer comparable.

## Assumed frontier policy

### Decision

Keep the original clean complete-coverage rule for normal models:

> A model needs data for every benchmark in an index to appear in that index.

But add one narrow exception:

> A missing current-frontier row on a saturated benchmark may be filled with an explicit assumed-frontier observation.

This preserves the original clean index membership rule while avoiding the stale-frontier-row failure mode.

### Frontier model set

Create a versioned operator-curated frontier set, for example:

```text
frontier_set_2026_06_01 = [
  GPT-5.5,
  Claude Opus 4.8,
  Gemini 3.1 Pro,
  GPT-5.4,
  Claude Opus 4.7,
  ...
]
```

A model can be frontier-class if it is:

- explicitly in the versioned frontier set; or
- released/updated in the last 12 months and top-tier on an active broad benchmark source.

The curated list wins. SubstitutionBench should not silently infer frontier status without showing the rule.

### Assigned score

If `(frontier model, saturated benchmark)` is missing:

```text
assumed_score = frontier_anchor
```

Where `frontier_anchor` remains the top-3 average of real observed scores for that benchmark.

Do **not** assign the theoretical ceiling unless the observed anchor equals the ceiling. Using the anchor is conservative and avoids giving assumed frontier models extra credit.

### Provenance

Assumed frontier rows are not real observations. They must be labeled everywhere:

- source: `substitutionbench_assumption`
- observation kind: `assumed_frontier_score`
- provenance: `assumed_frontier:anchored`
- reason: `Current frontier model missing on saturated benchmark; assigned top-3 observed frontier anchor.`

Assumed scores may be used for:

- frontier anchor continuity;
- index membership;
- component/index calculation;
- UI transparency.

Assumed scores must **not** be used as external evidence that the model actually ran the benchmark.

### Non-frontier missing rows

No assumption. Missing non-frontier rows stay `unknown` and fail complete-coverage membership.

This matters. If a cheap model is missing from MATH-500, we do not get to assume it clears MATH-500 just because frontier probably does.

## Freshness states

Every benchmark source field should have a freshness state:

- `fresh`: source updated this benchmark within 90 days.
- `aging`: updated within 90-180 days; no known protocol change.
- `stale_source`: source stopped refreshing this saturated benchmark, but old rows remain protocol-compatible.
- `stale_protocol`: benchmark/harness/question set changed; old rows are not comparable.
- `no_score_source`: source has tasks/eval set but no model-score table.

Index treatment:

- `fresh` / `aging`: normal use.
- `stale_source`: use existing real rows; allow assumed frontier rows for saturated benchmarks; flag in UI.
- `stale_protocol`: exclude old rows from resolved scores.
- `no_score_source`: use for task taxonomy only until a score source is found.

## What the UI should show

For every benchmark/index:

- saturation state: active / saturated / fully saturated;
- freshness state: fresh / aging / stale source / stale protocol;
- assumed frontier count;
- real observation count;
- substitution floor: cheapest qualifying non-frontier model;
- frontier anchor and how it was computed.

The key product copy should be direct:

- `Solved benchmark: cheapest model above 95% is X at $Y/task.`
- `No substitute: no cheaper non-frontier model clears 95%.`
- `Assumed frontier rows: current frontier models were not rerun; scores anchored to top-3 observed ceiling.`

## Source audit

### Recommended v1 score sources

#### Artificial Analysis individual benchmark fields

Use for:

- current model roster;
- pricing/speed where available;
- individual benchmark fields with protocol metadata.

Do not use as primary definitions:

- AA Intelligence Index;
- AA Math Index;
- AA Coding Index.

Those are source aggregates, not SubstitutionBench task-family definitions.

Useful fields already observed in the AA API payload:

- `math_500`
- `aime`
- `aime_25`
- `gpqa`
- `hle`
- `mmlu_pro`
- `livecodebench`
- `scicode`
- `lcr`
- `tau2`
- `terminalbench_hard`
- `ifbench`
- plus AA aggregate indexes, which should be secondary only.

Recommendation: v1 as source fields, not as component indexes.

#### LiveCodeBench official

Sources:

- `https://livecodebench.github.io/leaderboard.html`
- `https://raw.githubusercontent.com/LiveCodeBench/LiveCodeBench.github.io/main/build/performances_generation.json`
- `https://raw.githubusercontent.com/LiveCodeBench/LiveCodeBench.github.io/main/build/v5.json`

Observed fields:

- model;
- question/task id;
- date;
- difficulty;
- platform;
- `pass@1`.

Recommendation: v1 coding source. Prefer official LiveCodeBench over aggregator rows when protocol-equivalent.

#### BigCodeBench

Hugging Face sources:

- `bigcode/bigcodebench-results`
- `bigcode/bigcodebench-hard-results`
- `bigcode/bigcodebench-solve-rate`
- `bigcode/bigcodebench-elo`

Observed fields include:

- model;
- model size / type metadata;
- `complete`;
- `instruct`;
- date;
- task solve rate.

Recommendation: v1 coding source if extraction remains stable. Strong fit because task solve rates help identify saturation.

#### Open LLM Leaderboard

Hugging Face sources:

- `open-llm-leaderboard/contents`
- `open-llm-leaderboard/results`

Observed score columns:

- IFEval;
- BBH;
- MATH Lvl 5;
- GPQA;
- MuSR;
- MMLU-Pro;
- average;
- model metadata and parameter counts.

Recommendation: v1 supplemental source for open-weight model coverage. Not enough for proprietary frontier alone.

#### Aider code editing leaderboard

Source:

- `https://aider.chat/docs/leaderboards/edit.html`

Observed fields:

- model;
- pass rate;
- well-formed edit format rate;
- command/edit format;
- total cost.

Recommendation: v1/v2 coding-editing source. Keep separate from pure code-generation benchmarks.

#### SWE-bench Verified

Sources:

- `https://www.swebench.com/`
- `https://github.com/SWE-bench/experiments`
- Hugging Face task dataset: `SWE-bench/SWE-bench_Verified`

HF provides the benchmark tasks. The model scores live elsewhere, especially in the experiments repo/leaderboard artifacts.

Recommendation: v1 if score extraction from experiments repo is stable; otherwise v2. Treat as agentic software-engineering, not pure model coding.

### Recommended v2 / source-research targets

#### Terminal-Bench

Sources:

- `https://www.tbench.ai/`
- `https://github.com/laude-institute/terminal-bench`
- Hugging Face datasets including `harborframework/terminal-bench-2.0` and related verified datasets.

Observed task artifacts:

- instructions;
- task config;
- solution scripts;
- tests;
- Docker/environment definitions.

Recommendation: v2 agentic/terminal benchmark. Include in v1 only if a stable public score export is found.

#### HLE / Humanity's Last Exam

Sources:

- `https://lastexam.ai/`
- `https://scale.com/leaderboard/humanitys_last_exam`
- HF dataset: `cais/hle`
- HF Space found: `zoom-ai/hle-leaderboard`, with static leaderboard data in `app.py`.

Recommendation: v2 frontier-boundary/general-reasoning benchmark. Must split text-only vs multimodal/full-set.

#### LMArena / Arena Hard

Sources:

- `lmarena-ai/arena-leaderboard` HF Space;
- `arena_hard_auto_leaderboard_v0.1.csv`;
- `leaderboard_table_YYYYMMDD.csv` snapshots.

Recommendation: optional separate preference/chat basket. Do not mix into core task-family substitution unless explicitly framed as chat preference substitution.

### Exclude as v1 scored sources unless better artifacts are found

- HF task-only datasets with no model-score table.
- stale Arena Hard snapshots as current capability.
- vendor-reported benchmark claims without protocol metadata.
- aggregate indexes that hide component/protocol details.

## Revised sub-index direction

The final basket needs a data-driven pass after source extraction, but the product direction should be:

### Math / formal reasoning

Purpose: solved quantitative reasoning substitution.

Candidate benchmarks:

- MATH-500;
- AIME / AIME 2025;
- GPQA Diamond if treated as science reasoning, not pure math;
- Open LLM Leaderboard MATH Lvl 5 as open-model coverage backfill.

Expected saturation behavior:

- MATH-500 likely saturated or near-saturated.
- AIME is small-N/protocol-sensitive; useful but needs strict year/k/tool metadata.

### Coding generation

Purpose: code writing from prompt.

Candidate benchmarks:

- LiveCodeBench official pass@1;
- BigCodeBench complete/instruct;
- HumanEval+/MBPP+ only as saturated lower-tier signals if clean scores exist.

Expected saturation behavior:

- older code-generation benchmarks are saturated and useful for substitution floors;
- LiveCodeBench/BigCodeBench provide harder/current discrimination.

### Code editing / software engineering

Purpose: modify existing code, repair bugs, apply diffs.

Candidate benchmarks:

- Aider edit/polyglot;
- SWE-bench Verified;
- SWE-bench Lite only as a secondary/stale comparison if needed.

This should probably be separate from Coding Generation, or Coding should become two subcomponents.

### Agentic / tool use

Purpose: operate tools, terminal, browser, and multi-step workflows.

Candidate benchmarks:

- Terminal-Bench;
- τ²-bench;
- IFBench / IFEval;
- HLE with tools/full-set if score source is credible.

### General / knowledge / chat

This is the least crisp component. It should not exist just because AA has an Intelligence Index.

Candidate options:

1. Replace General with **Knowledge / Broad Reasoning**:
   - MMLU-Pro;
   - GPQA;
   - HLE text-only;
   - BBH/MuSR.

2. Or split General into optional non-hero indexes:
   - Preference/chat: LMArena / Arena Hard;
   - Knowledge: MMLU-Pro / HLE text-only;
   - Instruction following: IFEval.

Recommendation: do not let a vague General index dominate the hero until its task-family purpose is clear.

## Immediate implementation order

1. Build a source registry table for the new candidate sources.
2. Add benchmark metadata fields:
   - saturation state;
   - freshness state;
   - protocol version;
   - theoretical/empirical ceiling;
   - score direction;
   - task family.
3. Add assumed-frontier observations for saturated benchmarks only.
4. Rebuild component baskets using benchmark-first definitions.
5. Recompute substitution floors per benchmark and per component.
6. Update the dashboard to expose saturation/staleness/assumption badges.

## Open product decisions

1. Should **General** stay in the hero composite, or should the hero become Math + Coding + Agentic only until General is better defined?
2. Should Coding be split into **Coding Generation** and **Code Editing/SWE**?
3. Should assumed frontier rows count as complete coverage? Recommendation: yes, but only for curated frontier models on saturated benchmarks.
4. Should the UI default to showing saturated substitution floors before aggregate index scores? Recommendation: yes for saturated benchmarks.
