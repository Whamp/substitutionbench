# GPT-5.5 Delegate Research Audit — May 31, 2026

> Re-audit of the earlier GLM-backed SubstitutionBench research after OpenAI Codex auth was fixed.  
> Method: three `delegate_task` GPT-5.5 / openai-codex subagents independently rechecked frontier model coverage, candidate-model scores, and benchmark selection. Tars then spot-checked the highest-impact claims against live sources.

## Executive Verdict

The weaker GLM delegates missed material things.

1. **The frontier reference is stale.** Use **GPT-5.5** and **Claude Opus 4.8**, not GPT-5.4 / Claude Opus 4.7 / Claude Sonnet 4.
2. **The old “Claude is weak on GPQA” take is bad.** It was mostly stale-model contamination. Claude Opus 4.8 is now #1 on Artificial Analysis Intelligence Index, and Claude Opus 4.8 dominates Vals SWE-bench Verified.
3. **GPQA Diamond is still useful, but no longer the best single pilot.** It is now near-ceiling at the top: Gemini 3.1 Pro 94.1%, GPT-5.5 xhigh 93.5%, GPT-5.5 high 93.2%.
4. **Best pilot recommendation changed:** use a **multi-benchmark pilot**: SWE-bench Verified/Pro + LiveCodeBench + GPQA Diamond. If forced to pick one, use SWE-bench Verified for practical substitution signal.
5. **GLM is nuanced:** GLM 4.5 looks strong on MATH-500 but much weaker on GPQA; GLM-5/5.1 improve the GLM story but are verbose and not clearly cheap in real cost.
6. **Qwen3.7-Max is a major missed candidate.** It reports GPQA Diamond 92.4 and strong SWE-style/coding-agent results, but with reasoning-mode caveats and higher cost than the budget poster children.

## Source-Checked Corrections

### Frontier references

- **GPT-5.5**
  - OpenAI launched GPT-5.5 on Apr. 23/24, 2026 and positions it as the current frontier model for agentic coding, computer use, knowledge work, and scientific research.
  - Pricing: **$5/M input, $0.50/M cached input, $30/M output**.
  - Artificial Analysis GPQA Diamond leaderboard: **GPT-5.5 xhigh 93.5%**, **GPT-5.5 high 93.2%**.
  - Sources:
    - https://openai.com/index/introducing-gpt-5-5/
    - https://openai.com/api/pricing/
    - https://artificialanalysis.ai/evaluations/gpqa-diamond

- **Claude Opus 4.8**
  - Released May 28, 2026.
  - Artificial Analysis: **#1 / 150**, Intelligence Index **61.4**, ahead of GPT-5.5 xhigh 60.2 and GPT-5.5 high 58.9.
  - Pricing, official Anthropic API: **$5/M input**, **$25/M output**, **$0.50/M cache hit**; 5m cache write $6.25/M, 1h cache write $10/M.
  - AA notes Opus 4.8 is expensive, slower than average, and very verbose.
  - Sources:
    - https://artificialanalysis.ai/models/claude-opus-4-8
    - https://platform.claude.com/docs/en/about-claude/pricing

### GPQA Diamond update

- Top leaderboard now reads:
  - Gemini 3.1 Pro Preview: **94.1%**
  - GPT-5.5 xhigh: **93.5%**
  - GPT-5.5 high: **93.2%**
- This reduces GPQA's headroom as a single benchmark. With only 198 questions, a 93–94% score means ~12–14 misses, so tiny differences are statistically fragile.
- Source: https://artificialanalysis.ai/evaluations/gpqa-diamond

### SWE-bench Verified changed the story

Vals SWE-bench Verified, updated 2026-05-28, gives a much cleaner practical substitution signal:

| Rank | Model | Accuracy | Cost/Test | Latency |
|---:|---|---:|---:|---:|
| 1 | Claude Opus 4.8 | 88.60% ± 1.42 | $1.92 | 566.95s |
| 2 | GPT 5.5 | 82.60% ± 1.70 | $1.36 | 426.43s |
| 3 | Claude Opus 4.7 | 82.00% ± 1.72 | $2.42 | 441.99s |
| 4 | Gemini 3.5 Flash | 78.80% ± 1.83 | $0.95 | 254.13s |
| 8 | GPT 5.3 Codex | 78.00% ± 1.85 | $0.46 | 246.53s |
| 10 | DeepSeek V4 | 77.40% ± 1.87 | $0.44 | 634.61s |

Source: https://www.vals.ai/benchmarks/swebench

Important caveat: Vals page has an inconsistent narrative line saying GPT-5.5 leads, but its visible table ranks Claude Opus 4.8 first.

## Candidate Model Additions / Corrections

### Qwen3.7-Max — missed major candidate

- Qwen reports **GPQA Diamond 92.4**, beating Opus-4.6 Max 91.3 in their comparison.
- Qwen reports strong coding-agent numbers:
  - SWE-Verified **80.4**
  - SWE-Pro **60.6**
  - Terminal Bench 2.0-Terminus **69.7**
  - SciCode **53.5**
- Caveat: Qwen recommends explicit high-reasoning/xhigh prompting, so scores must be tagged by reasoning mode.
- Source: https://qwen.ai/blog?id=qwen3.7

### DeepSeek V4 Flash — still a strong budget story, but tag reasoning effort

- OpenRouter confirms:
  - 284B total / 13B active
  - 1M context
  - Pricing: **$0.0983/M input**, **$0.1966/M output**
  - Supports reasoning efforts `high` and `xhigh`; `xhigh` maps to max reasoning.
- Previous low-cost substitution story still holds, but every benchmark row must specify reasoning effort.
- Source: https://openrouter.ai/deepseek/deepseek-v4-flash/benchmarks

### GLM — prior data was incomplete

- Prior note only captured GLM 4.5 as strong on MATH-500.
- Delegate research found public listings suggesting **GLM 4.5 Thinking GPQA Diamond ~78.2%**, which materially weakens it as a GPQA substitute despite excellent MATH-500.
- GLM-5 is a better GLM candidate:
  - Open weights, MIT license
  - 744B total / 40B active
  - 200k context
  - AA Intelligence Index **50**, rank **#6 / 87** among comparable open-weight reasoning models
  - Pricing: **$1/M input**, **$3.20/M output**, **$0.20/M cache hit**
  - Caveat: very verbose — 110M output tokens in AA Intelligence Index eval; AA recommends considering newer GLM-5.1.
- Source: https://artificialanalysis.ai/models/glm-5

### MiniMax — likely stronger than old note, but source-dependent

- Delegate research found public claims:
  - MiniMax M2.7 GPQA-Diamond as high as **89.8** in vendor/paper trail.
  - Vals/search trail around **86.62 ± 1.95**, but extracted page was inconsistent.
  - MiniMax M2.5 GPQA around **85.2** via Papers with Code trail.
- Treat as promising but not clean enough for canonical table without another verification pass.

### Gemma 4 — GPQA claim solid; MATH-500 claim weakly sourced

- Google/HF material supports Gemma 4 31B GPQA Diamond **84.3%** and Gemma 4 26B A4B **82.3%**.
- The previous **MATH-500 94.5** claim was not re-confirmed from primary Gemma material during this pass. Keep only if original source is retained and cited.

## Benchmark Recommendation Update

### New recommendation

Use a **multi-benchmark pilot**:

1. **SWE-bench Verified / SWE-bench Pro** — main practical substitution benchmark.
2. **LiveCodeBench** — contamination-resistant coding anchor.
3. **GPQA Diamond** — science-reasoning anchor and continuity with prior work.

### If forced to choose one

Choose **SWE-bench Verified**.

Reason: it tests whether models can actually fix real software issues under a consistent harness. That is closer to the SubstitutionBench question — “how cheap can you go before anyone notices?” — than multiple-choice science QA.

### GPQA status

Keep GPQA, but demote it. It is clean, cheap, and well-known, but current frontier scores around 93–94% make it less discriminating than before.

### AIME status

Do not use AIME as the headline pilot. It is too small and too saturated; one problem is 3.33 percentage points.

### LiveCodeBench status

Good secondary benchmark. The public leaderboard has useful spread, but the visible extracted leaderboard did not yet include GPT-5.5 or Claude Opus 4.8, so current frontier rows may need to be run manually.

Source: https://livecodebench.github.io/leaderboard.html

## Action Items

1. Update canonical data files to replace GPT-5.4 / Claude Opus 4.7 frontier framing with GPT-5.5 / Claude Opus 4.8.
2. Add a `reasoning_effort` / `eval_mode` column to benchmark tables.
3. Add a `source_quality` column: official, independent, aggregator, vendor, community.
4. Promote SWE-bench Verified to pilot-primary and keep GPQA as secondary anchor.
5. Re-check MiniMax M2.7/M2.5 and GLM-5.1 before making them canonical table rows.
6. Preserve old GPQA and MATH files as historical snapshots unless/until cleaned with cited revisions.

## Confidence

- High: GPT-5.5 and Claude Opus 4.8 are the correct current frontier references.
- High: prior Claude weakness framing is invalid for current Anthropic.
- High: GPQA Diamond is less attractive as a single pilot after GPT-5.5 top-end update.
- Medium-high: SWE-bench Verified is the better pilot centerpiece.
- Medium: GLM/MiniMax exact GPQA rows need one more verification pass before canonicalization.
