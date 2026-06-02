# Factory Router Study

Status: source-grounded product/architecture note  
Date: 2026-06-02  
Scope: what Factory Router reveals about real-world model substitution, routing, and the next SubstitutionBench product shape.

## Sources inspected

Primary Factory sources:

- Factory announcement: <https://factory.ai/news/factory-router>
- X announcement video/post: <https://x.com/i/status/2061862733126275549>
- Factory chart assets from the announcement:
  - <https://factory.ai/static/benchmark-results-822afb.png>
  - <https://factory.ai/static/admin-routing-guidance-3af9a8.png>
  - <https://factory.ai/static/pareto-frontier-0e7767.png>

Benchmark source checks:

- Terminal-Bench 2.0 repo: <https://github.com/laude-institute/terminal-bench-2>
- Terminal-Bench 2.0 README: <https://raw.githubusercontent.com/laude-institute/terminal-bench-2/main/README.md>
- Harbor registry: <https://raw.githubusercontent.com/harbor-framework/harbor/main/registry.json>
- Legacy-Bench repo: <https://github.com/Factory-AI/legacy-bench>
- Legacy-Bench README: <https://raw.githubusercontent.com/Factory-AI/legacy-bench/main/README.md>
- Legacy-Bench announcement: <https://factory.ai/news/legacy-bench>

Extraction notes:

- `web_extract` / `web_search` were blocked by Firecrawl credit limits, so the article was read through browser automation and direct HTTP fetches.
- `xurl` is not installed on this machine, so the X post/video was inspected through browser automation and screenshot/vision sampling.

## Factory's public claims

Factory Router is presented as a model router for Droid sessions:

> Factory Router cuts token spend by 20-25% while maintaining frontier performance. It automatically selects the right model for each task, and routes across providers if an endpoint degrades.

The stated operating pattern:

1. Pick a model for each Droid session.
2. Use efficient models for work that does not need frontier capability.
3. Keep frontier models available for work that does.
4. If the selected model struggles, move the session to a more capable model.
5. If providers degrade, hit rate limits, or capacity is constrained, fail over across models/providers/capacity sources.
6. Let enterprise admins shape the routing policy with org-level model policy and routing guidance.

## Reported benchmark results

Factory reports everything relative to a Claude Opus 4.7 baseline.

### Shipping setting

Terminal-Bench 2:

- Pass rate: 99% of Claude Opus 4.7.
- Cost per session: 20% lower; Factory Router runs at 80% of Opus cost.
- Cost per successful run: 80.5% of Opus.
- Scope note from article/chart: Terminal-Bench 2 averages all 89 tasks, across multiple runs.

Legacy-Bench:

- Pass rate: 96% of Claude Opus 4.7.
- Cost per session: 25% lower; Factory Router runs at 75% of Opus cost.
- Cost per successful run: 78.0% of Opus.
- Scope note from article/chart: full suite, across multiple runs.

### Aggressive setting

Factory also describes aggressive routing points past the bend in the Pareto curve:

- Terminal-Bench 2: 56% of Opus cost, 81% of Opus pass rate.
- Legacy-Bench: 30% of Opus cost, 49% of Opus pass rate.

This is the most important chart: they are not claiming "cheaper is always fine." They are explicitly saying there is a flat stretch, then a bend, then performance falls apart.

## X video observations

The X post text says:

> Introducing model routing to Factory. Factory Router picks the right model for every task, automatically. Maintain frontier performance while cutting costs by 25%.

Sampled video frames showed:

- Slogan frame: "Same tasks. Lower cost."
- Session UI frame:
  - `ACTIVE SESSION`
  - `STREAMING`
  - selected model: `Claude Opus 4.7`
  - provider: `BEDROCK`
  - status: `Generating implementation plan...`
- Task UI frame:
  - `ACTIVE TASK`
  - `WORKING`
  - selected model: `Kimi K2.6`
  - task: `Drafting refactor for payments module...`
- Benchmark frame repeating the Terminal-Bench 2 / Legacy-Bench claims.

Interpretation: the video reinforces that Factory is selling per-session/per-task model selection inside the Droid workflow, not a static leaderboard replacement.

## Enterprise routing controls

The admin-routing screenshot exposes a simple but revealing policy surface:

- `Automatic model selection for every Droid session`
- `Enabled org-wide`
- `Routing rules & context`
- Prompt-like guidance: "Describe workflow patterns, codebase areas, toolchains, and model preferences."

Visible examples:

- `Routine refactors, formatting, and doc updates -> favor cost-efficient models`
- `auth/ and payments/ need deeper reasoning -> keep on frontier models`
- `Search-heavy investigation -> route to open-source models`

Implication: their router likely combines benchmark priors, task/session classification, organizational policy, and runtime escalation signals. The admin layer is natural-language policy over a benchmarked/costed routing substrate.

## Public benchmark availability

### Terminal-Bench 2.0

Public and ingestible.

Verified from Harbor registry:

- `name`: `terminal-bench`
- `version`: `2.0`
- public task count: 89
- first task example:
  - `name`: `adaptive-rejection-sampler`
  - `git_url`: `https://github.com/laude-institute/terminal-bench-2.git`
  - `git_commit_id`: `69671fbaac6d67a7ef0dfec016cc38a64ef7a77c`
  - `path`: `adaptive-rejection-sampler`

The README says Terminal-Bench measures agents/models performing valuable work in containerized environments, with examples including assembling proteins, debugging async code, and resolving security vulnerabilities. It is run through Harbor using `terminal-bench@2.0`.

SubstitutionBench implication: Terminal-Bench 2.0 should be a first-class source target for agentic terminal/workflow substitution. It has a clean public dataset path.

### Legacy-Bench

Partly public, full suite controlled.

Verified from Legacy-Bench README:

- It evaluates AI coding agents on maintaining, debugging, and modernizing legacy code.
- It spans hundreds of tasks across six legacy language families and real enterprise domains.
- The public repo contains ten representative public sample tasks.
- The full benchmark is available for evaluation by contacting Factory.

Verified from Harbor registry:

- `name`: `legacy-bench`
- `version`: `1.0`
- public task count: 10
- first task example:
  - `name`: `1907c2-c-debug-legacy-buddy-fix`
  - `git_url`: `https://github.com/Factory-AI/legacy-bench.git`
  - `git_commit_id`: `12fa7cf969b7a253183388040d566fb353a1ab31`
  - `path`: `tasks/1907c2-c-debug-legacy-buddy-fix`

SubstitutionBench implication: we can ingest/cite the public sample and metadata, but Factory's full-suite Router result is not independently reproducible from public artifacts unless they provide access or per-task result exports.

## What Factory is probably solving under the hood

The announcement is consistent with a practical router/cascade stack:

1. **Task/session classification**
   - Infer whether the session is docs/refactor/search/debug/auth/payment/legacy/etc.
   - Use code path, toolchain, prompt intent, repo metadata, and perhaps early trace signals.

2. **Benchmark prior by task family**
   - Map a task class to evidence from Terminal-Bench, Legacy-Bench, SWE-bench-like tasks, internal enterprise evals, and provider reliability data.

3. **Cost/performance frontier selection**
   - Choose the cheapest candidate/policy on the flat part of the curve that meets the quality floor.

4. **Runtime escalation**
   - Escalate if the cheaper model stalls, loops, fails tests, produces low-confidence plans, burns tokens, or hits verifier failures.

5. **Provider failover**
   - Separate reliability routing from capability routing: same/near-equivalent model through a healthier provider path when capacity degrades.

6. **Org policy overlay**
   - Admin rules override or bias routing for sensitive paths, preferred models, compliance constraints, open-source preferences, and cost posture.

7. **Cost per successful session accounting**
   - Optimize not just token price, but completed work per dollar after retries/escalations/failures.

## SubstitutionBench thesis update

Factory Router strongly validates the direction we moved toward:

> Substitution is not a global model ranking problem. It is a benchmark-grounded, task-family-specific, policy-sensitive cost/performance problem.

SubstitutionBench should not try to be Factory Router. It should become the neutral evidence layer that explains when a router, model, or policy is credible for a task family.

The correct unit of claim is:

> Candidate system X is a valid substitute for baseline Y on benchmark/task-family Z under floor F, with cost-per-success C and caveats K.

Not:

> Model X replaces Model Y.

## Product implications for SubstitutionBench

### 1. Routers need to be first-class candidates

Today we mostly model individual models. Factory makes clear that a dynamic routing policy is a candidate system too.

Add candidate types:

- `single_model`
- `static_policy`
- `dynamic_router`
- `router_with_escalation`
- `router_with_failover`

A router result should carry its own pass rate, average session cost, cost per success, latency, escalation rate, and failover rate.

### 2. Add Pareto frontier views

The dashboard needs a pass-rate-vs-cost view per benchmark/task family.

Minimum viable view:

- x-axis: relative full-session cost vs baseline.
- y-axis: relative pass rate vs baseline.
- mark baseline at 100% / 100%.
- mark candidate models/policies/routers.
- identify the cheapest candidate above the selected floor.
- visually mark the "flat stretch" and "bend" where further savings start destroying pass rate.

### 3. Cost per successful run should become a core metric

Factory explicitly guards against routers that look cheap only because they abandon hard sessions.

SubstitutionBench should track:

- average session cost;
- pass rate;
- cost per successful run;
- relative cost per successful run;
- failed-attempt cost;
- retry/escalation cost where available.

### 4. Add policy tiers, not one cutoff

The current 95% threshold is useful, but Factory's public numbers show at least three policy regimes:

- **Frontier-equivalent:** 98-99%+ of baseline; use for high-risk work.
- **Production-cost:** 95-97%+ of baseline; good default substitution floor.
- **Aggressive/economy:** lower pass floor; useful only when degradation is acceptable and clearly labeled.

### 5. Model escalation explicitly

A cheap model that often escalates to Opus is not the same thing as a cheap substitute.

Track, when available:

- initial model;
- final model;
- escalation count/rate;
- escalation reason;
- success after escalation;
- cost before escalation;
- total cost after escalation;
- regret vs starting frontier.

### 6. Split quality substitution from reliability failover

Factory blends both in the product story, but SubstitutionBench should separate them:

- quality substitute: cheaper system clears pass-rate floor;
- economic substitute: lower cost per success;
- reliability substitute: provider/model path keeps work moving during outage/capacity issue;
- latency substitute: faster system meets quality floor;
- compliance substitute: org-approved/local/open-source path.

### 7. Add task-policy mapping

Factory's admin examples are exactly the natural-language version of the decision tree we started building.

SubstitutionBench should map user intent to recommended floors:

- routine refactor/docs/formatting -> production-cost or aggressive if tests are strong;
- auth/payments/security/data deletion -> frontier-equivalent;
- search-heavy investigation -> prefer benchmarks with retrieval/tool/source-grounding evidence;
- legacy modernization -> Legacy-Bench-like evidence, but mark full-suite data as controlled;
- terminal/autonomous tool work -> Terminal-Bench 2.0 evidence.

## Data-model sketch

A future result row should be able to represent both a model and a router:

```text
benchmark_result
  benchmark_id
  task_family
  baseline_system_id
  candidate_system_id
  candidate_type
  routing_policy_id
  score_metric
  pass_rate
  baseline_pass_rate
  relative_pass_rate
  avg_session_cost
  baseline_avg_session_cost
  relative_session_cost
  cost_per_success
  baseline_cost_per_success
  relative_cost_per_success
  latency
  sample_size
  stderr_or_ci
  escalation_rate
  failover_rate
  run_count
  public_raw_results_available
  source_url
  notes
```

And policy/floor metadata:

```text
substitution_floor
  floor_id
  label
  benchmark_id
  task_family
  baseline_system_id
  min_relative_pass_rate
  max_relative_cost_per_success
  risk_tier
  caveat_text
```

## Recommended next build slices

1. **Add Factory Router as a research/reference entry**
   - Add this note to the repo.
   - Add Factory Router to related work / competitive references.
   - Classify it as commercial router evidence, not a benchmark source with raw public data.

2. **Create a `system_type` field**
   - Allow benchmark candidates to be `model` or `router_policy`.
   - This is the smallest schema move that prevents SubstitutionBench from being model-only.

3. **Add cost-per-success fields**
   - Even if current sources do not populate them yet, the dashboard should reserve the concept.

4. **Add a Pareto frontier prototype**
   - One benchmark view is enough at first.
   - Use existing model cost/score rows plus placeholder support for router points.

5. **Ingest Terminal-Bench 2.0 metadata from Harbor**
   - Public, 89 tasks, directly relevant to Factory's claim.

6. **Add Legacy-Bench as controlled/public-subset benchmark metadata**
   - Public sample exists; full suite controlled.
   - Do not pretend the full suite is independently reproducible.

7. **Add source-confidence labels**
   - `public_raw_results`
   - `public_aggregate_only`
   - `public_sample_only`
   - `vendor_claim`
   - `controlled_access`

## Open questions

- What exact signals does Factory use to decide a selected model is "struggling"?
- Are their pass rates based on single-attempt sessions, retries, or full Droid workflows with intermediate escalation?
- How much of the 20-25% cost saving comes from cheaper initial model choice vs provider pricing vs early stopping/caching/tool behavior?
- What models are in the efficient pool besides the video-visible `Kimi K2.6` and frontier `Claude Opus 4.7`?
- Are Terminal-Bench 2.0 public leaderboard aggregates enough for our first agentic substitution floor, or do we need to run the benchmark ourselves?

## Bottom line

Factory Router is probably the closest live commercial proof that SubstitutionBench's core question matters.

They are solving the operational version:

> Route each session to the cheapest reliable model/policy that will still finish the work.

SubstitutionBench should solve the evidence version:

> Show, by benchmark and task family, where that substitution is justified, what it saves, where the Pareto bend is, and what risks remain.
