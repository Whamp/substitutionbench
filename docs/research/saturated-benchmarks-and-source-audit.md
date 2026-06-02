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

## Benchmark task cards

Every benchmark in SubstitutionBench needs a plain-English task card. The card should answer:

1. What does the model actually have to do?
2. What real-world task class does this approximate?
3. If this benchmark is saturated, what work can probably be substituted away from frontier models?
4. What does the benchmark **not** prove?

This is not cosmetic. A benchmark score is only useful if a normal user understands the task class behind it. The dashboard should eventually expose these descriptions directly, not bury them in docs.

### Proposed task-class descriptions

#### MATH-500

Plain English: solve contest-style math word problems with exact numerical or symbolic answers.

Task class represented:

- algebra, geometry, probability, number theory, and intermediate contest math;
- careful multi-step quantitative reasoning;
- math-answer generation where the answer can be checked exactly.

If saturated, likely substitutable:

- routine contest-math solving;
- symbolic/numeric math explanations where the problem resembles known benchmark styles;
- math-heavy tutoring examples where exact answer checking is available.

Does not prove:

- novel mathematical research;
- long-horizon proof discovery;
- messy real-world quantitative modeling;
- reliability without answer verification.

#### AIME / AIME 2025

Plain English: solve short olympiad-style math problems, usually with integer answers.

Task class represented:

- high-school competition math;
- compact but tricky reasoning;
- exact-answer math with small sample size.

If saturated, likely substitutable:

- short competition-style math tasks;
- checking or generating AIME-like solutions;
- problems where the final answer can be independently verified.

Does not prove:

- broad mathematical competence by itself;
- stable model quality from tiny sample sizes;
- performance under different pass@k, tool-use, or consensus protocols unless labeled.

#### GPQA / GPQA Diamond

Plain English: answer very hard graduate-level science questions that are designed to fool non-experts.

Task class represented:

- expert scientific reasoning;
- physics, chemistry, biology, and related domain knowledge;
- choosing among plausible technical answers.

If saturated, likely substitutable:

- bounded expert-QA where answer choices are available;
- science reasoning questions with well-specified options;
- technical study/exam support where humans can verify sources.

Does not prove:

- open-ended scientific research;
- lab planning;
- correctness on undocumented edge cases;
- citation-grounded answers unless retrieval is part of the task.

#### MMLU-Pro

Plain English: answer harder multiple-choice questions across many academic and professional subjects.

Task class represented:

- broad textbook knowledge;
- professional/academic exam-style reasoning;
- multi-domain multiple-choice QA.

If saturated, likely substitutable:

- broad knowledge checks;
- classification-style expert QA;
- exam-prep style responses where answer choices or rubrics exist.

Does not prove:

- open-ended writing quality;
- fresh factual knowledge;
- tool use;
- deep performance in any one domain without drilldown benchmarks.

#### HLE / Humanity's Last Exam

Plain English: answer extremely difficult expert questions across many domains; some versions include multimodal questions.

Task class represented:

- frontier-bound expert reasoning;
- obscure domain knowledge;
- hard academic/professional questions beyond normal exam benchmarks.

If saturated, likely substitutable:

- probably little today; HLE is more useful as a no-substitute/frontier-bound detector.

Does not prove:

- everyday productivity tasks;
- agentic tool use unless the specific HLE variant includes tools;
- text-only vs multimodal ability unless split explicitly.

#### BBH / Big-Bench Hard

Plain English: solve tricky reasoning puzzles and tasks selected because earlier models struggled with them.

Task class represented:

- puzzle-like reasoning;
- symbolic manipulation;
- multi-step instruction following;
- classic hard eval tasks.

If saturated, likely substitutable:

- bounded reasoning puzzles;
- structured logic tasks;
- older benchmark-style chain-of-thought tasks.

Does not prove:

- modern frontier reasoning;
- real-world task robustness;
- interactive tool use.

#### MuSR

Plain English: solve multi-step reasoning questions over longer stories or scenarios.

Task class represented:

- reading comprehension with hidden implications;
- multi-hop reasoning;
- narrative or scenario-based deduction.

If saturated, likely substitutable:

- moderate-length reasoning over supplied context;
- scenario comprehension;
- analytical reading tasks with enough context in the prompt.

Does not prove:

- very long-context reliability;
- source retrieval;
- real-world planning beyond text scenarios.

#### IFEval / IFBench

Plain English: follow explicit instructions and constraints exactly.

Task class represented:

- formatting discipline;
- constraint obedience;
- structured output following;
- prompt compliance.

If saturated, likely substitutable:

- formatting tasks;
- structured response generation;
- simple assistant workflows where following constraints matters more than raw intelligence.

Does not prove:

- task correctness beyond following instructions;
- reasoning depth;
- tool use;
- safety judgment.

#### LiveCodeBench

Plain English: solve recent programming contest-style coding problems by writing working code.

Task class represented:

- algorithmic code generation;
- competitive-programming style reasoning;
- translating problem statements into executable code.

If saturated, likely substitutable:

- well-scoped coding challenge solutions;
- algorithmic snippets;
- code generation where tests can verify the output.

Does not prove:

- editing an existing codebase;
- debugging a large repo;
- product engineering judgment;
- multi-file software work.

#### BigCodeBench

Plain English: write functional code that uses real Python libraries and APIs, not just toy algorithms.

Task class represented:

- practical code generation;
- library/API usage;
- program synthesis with realistic dependencies;
- domain-level coding tasks.

If saturated, likely substitutable:

- small utility functions;
- library-call code snippets;
- coding tasks with clear input/output specs and tests.

Does not prove:

- repo-scale software engineering;
- architecture;
- debugging live systems;
- requirements clarification.

#### HumanEval+ / MBPP+

Plain English: write short Python functions that pass unit tests.

Task class represented:

- simple function synthesis;
- basic algorithmic programming;
- test-driven snippet completion.

If saturated, likely substitutable:

- small standalone coding tasks;
- simple helper functions;
- generated code where tests are available.

Does not prove:

- modern coding-agent performance;
- repository editing;
- ambiguous product requirements;
- integration work.

#### Aider code editing / polyglot

Plain English: edit existing code according to a requested change and produce a patch in the right format.

Task class represented:

- code editing, not just code generation;
- obeying diff/edit protocols;
- modifying existing files without breaking syntax;
- practical pair-programming style changes.

If saturated, likely substitutable:

- small code edits;
- mechanical refactors;
- patch-format workflows;
- low-risk implementation steps with tests.

Does not prove:

- architecture judgment;
- complex debugging;
- multi-agent orchestration;
- correctness without tests or review.

#### SWE-bench Verified

Plain English: fix real bugs in real GitHub repositories by producing patches that pass tests.

Task class represented:

- agentic software engineering;
- repo navigation;
- bug diagnosis;
- patch generation;
- test-driven repair.

If saturated, likely substitutable:

- only if the specific score source/scaffold is saturated. It would mean cheaper agent/model stacks can handle verified real-repo bug fixes at frontier-like rates.

Does not prove:

- pure base-model ability, because agent scaffold matters;
- product sense;
- UI taste;
- safe autonomous merging.

#### Terminal-Bench

Plain English: complete tasks in a terminal environment using files, commands, scripts, tests, and shell workflows.

Task class represented:

- CLI tool use;
- file-system operations;
- environment setup;
- data munging;
- build/test/debug loops;
- practical agent work on a machine.

If saturated, likely substitutable:

- command-line automation;
- routine devops-like tasks;
- scripted debugging and verification;
- bounded terminal workflows.

Does not prove:

- desktop UI use;
- long-running project planning;
- external side-effect safety;
- work requiring human judgment or credentials.

#### τ²-bench / tau2

Plain English: complete realistic tool-using assistant tasks, usually involving APIs, state, and multi-step goals.

Task class represented:

- function/tool calling;
- transactional workflows;
- multi-step assistant actions;
- state tracking across tool calls.

If saturated, likely substitutable:

- bounded tool workflows;
- API-backed assistant tasks;
- routine transactional agents.

Does not prove:

- open-ended autonomy;
- safe handling of surprising real-world side effects;
- broad reasoning outside the task protocol.

#### SciCode

Plain English: solve scientific coding problems where the model must implement code for science/math-style tasks.

Task class represented:

- scientific programming;
- numerical/scientific reasoning in code;
- translating formulas or scientific tasks into executable programs.

If saturated, likely substitutable:

- bounded scientific scripting;
- numeric helper programs;
- code-backed science/math exercises.

Does not prove:

- scientific discovery;
- experimental design;
- large simulation engineering;
- domain correctness without validation.

#### LCR

Plain English: code/reasoning benchmark field from Artificial Analysis that needs protocol documentation before product use.

Task class represented:

- currently insufficiently clear for user-facing task-class claims.

If saturated, likely substitutable:

- do not claim until protocol and task examples are documented.

Does not prove:

- anything product-facing until the benchmark definition is made explicit.

#### LMArena / Arena Hard

Plain English: compare model responses by preference or an automatic judge against challenging prompts.

Task class represented:

- chat quality;
- helpfulness/style/preference;
- general response quality under subjective evaluation.

If saturated, likely substitutable:

- chat-style assistant responses where preference quality is enough;
- drafting, explanation, and general assistant outputs.

Does not prove:

- factual correctness;
- task-specific reliability;
- tool use;
- math/coding correctness.

### Registry fields implied by task cards

Add benchmark metadata fields for:

- `plain_english_task`;
- `task_class`;
- `substitution_claim_when_saturated`;
- `does_not_prove`;
- `protocol_notes`;
- `score_interpretation`;
- `score_source_url`.

The UI should be able to render a card like:

```text
MATH-500
Task: solve contest-style math word problems with exact answers.
If solved: cheaper models can likely handle routine contest-math style work.
Does not prove: open-ended proof discovery or messy real-world modeling.
```

## Substitution discovery experience

The dashboard should not only rank models. It should help a buyer or builder answer a concrete question:

> What kind of work can I safely move off a frontier model, and what is the cheapest model class that clears the bar?

This calls for two complementary product surfaces.

### 1. Task decision tree

The decision tree should guide a non-benchmark expert from a plain-English task to candidate benchmarks, substitution claims, and model floors.

Recommended first-pass tree:

1. **Is the task mostly about producing a final answer, or taking actions?**
   - Final answer -> go to reasoning/knowledge/math/code-generation branches.
   - Actions -> go to code-editing, terminal, tool-use, or agentic-workflow branches.

2. **Does success have an objective verifier?**
   - Exact answer / tests / pass-fail checks -> saturated benchmarks can support strong substitution claims.
   - Human judgment / taste / open-ended strategy -> substitution claims should be weaker and provenance-heavy.

3. **What domain does the task resemble?**
   - Math word problems -> MATH-500, AIME.
   - Graduate science questions -> GPQA, GPQA Diamond, HLE where available.
   - Short coding tasks -> HumanEval+, MBPP+, BigCodeBench.
   - Recent contest-style coding -> LiveCodeBench.
   - Editing an existing repo -> Aider, SWE-bench Verified.
   - Terminal/computer operations -> Terminal-Bench.
   - API/tool/business workflows -> τ²-bench.
   - Instruction/format compliance -> IFEval/IFBench.
   - Subjective assistant quality -> Arena / Arena Hard.

4. **How much context and environment coupling is involved?**
   - Prompt-only, no files/tools -> lower deployment risk.
   - Existing repo, shell, APIs, multi-step state -> evaluate the agent stack, not only the base model.

5. **What failure cost is acceptable?**
   - Low-cost/verifiable failures -> use cheapest model above threshold.
   - High-cost or hard-to-detect failures -> require margin above threshold, stronger benchmarks, or keep frontier in the loop.

Decision tree output should include:

- matched task class;
- relevant benchmarks;
- saturation state;
- confidence level of the substitution claim;
- cheapest model above the selected threshold;
- what the benchmark does **not** prove;
- recommended validation before switching production traffic.

### 2. Searchable task-to-benchmark finder

Users should also be able to search natural task descriptions, e.g.:

- "write small Python functions from specs";
- "fix bugs in an existing repo";
- "answer graduate biology questions";
- "operate a terminal to install and test software";
- "follow exact formatting instructions".

The search index should be built from benchmark metadata, not model marketing copy. Searchable fields should include:

- `plain_english_task`;
- `task_class`;
- `substitution_claim_when_saturated`;
- `does_not_prove`;
- `protocol_notes`;
- benchmark aliases and common user phrases.

Search results should show benchmark cards first, then eligible model floors. The ranking should prefer task-class match quality over raw model score.

### Product principle

The hero question should shift from:

> Which model is best?

To:

> For this kind of task, what is the cheapest model I can justify using?

That is the actual SubstitutionBench wedge.

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
