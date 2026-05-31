# GPQA Diamond Benchmark Scores

> Pilot data collection for SubstitutionBench. Last updated: May 31, 2026.
> Sources: pricepertoken.com (Artificial Analysis data), OpenRouter, HuggingFace model cards, Interfaze.ai, LangDB, gemma4all.com, llm-stats.com.
> GPQA Diamond = 198 multiple-choice graduate-level science questions (biology, physics, chemistry).
> PhD experts score ~65%; skilled non-experts ~34%.

## Frontier Reference Models

| Model | Provider | GPQA Diamond | Input $/M | Output $/M |
|-------|----------|-------------|-----------|------------|
| Gemini 3.1 Pro Preview | Google | 94.1 | $2.00 | $12.00 |
| Qwen3.7 Max | Alibaba | 92.3 | $1.25 | $3.75 |
| Gemini 3.5 Flash | Google | 92.2 | $1.50 | $9.00 |
| GPT-5.4 (flagship) | OpenAI | 92.0 | $2.50 | $15.00 |
| GPT-5.3 Codex | OpenAI | 91.5 | $1.75 | $14.00 |
| Claude Opus 4.7 | Anthropic | 91.4 | $5.00 | $25.00 |
| Claude Sonnet 4.6 | Anthropic | 89.9† | $3.00 | $15.00 |
| Gemini 3 Pro Preview | Google | 90.8 | $2.00 | $12.00 |
| GPT-5.2 Pro | OpenAI | 90.3 | $10.50 | $84.00 |

† Interfaze.ai per-domain breakdown: Physics 93.0%, Chemistry 89.0%, Biology 80.0%

## Models of Interest (Will's Requested Set)

### Qwen 3.5 Family

| Model | GPQA Diamond | Params | Source |
|-------|-------------|--------|--------|
| Qwen3.5-397B-A17B | 89.3 | 397B (17B active) | pricepertoken |
| Qwen3.5-122B-A10B | — | 122B (10B active) | Not found |
| Qwen3.5-35B-A3B | 84.2 | 35B (3B active) | gemma4all.com (vs Gemma 4 26B) |
| Qwen3.5-27B | 85.5 | 27B dense | gemma4all.com (vs Gemma 4 31B) |
| Qwen3.5-9B | 79.1† | 9B dense | gemma4all.com (vs Gemma 4 E4B). HuggingFace PR pending. |
| Qwen3.5-4B | 76.2 | 4B dense | gemma4all.com |

† Qwen3.5-9B GPQA score: gemma4all reports 79.1% in the 4B comparison but the HuggingFace PR #2 to add GPQA Diamond eval hasn't been merged yet. May need verification.

**NOTABLE:** Qwen3.5 has much better GPQA Diamond coverage than MATH-500 on public leaderboards.

### Qwen 3.6 Family

| Model | GPQA Diamond | Params | Source |
|-------|-------------|--------|--------|
| Qwen3.6-Plus | — | — | Not found on any leaderboard |

**Still absent.** Qwen3.6-Plus positioned for coding/agents, not knowledge benchmarks.

### Gemma 4 Family

| Model | GPQA Diamond | Params | Source |
|-------|-------------|--------|--------|
| Gemma 4 31B (IT) | 84.3–85.7‡ | 31B dense | gemma4all: 84.3%; pricepertoken: 85.7% |
| Gemma 4 26B A4B | 82.3 | 26B (4B active) | gemma4all.com |
| Gemma 4 E4B | 58.6 | 8B (4.5B effective) | gemma4all.com |
| Gemma 4 E2B | — | 5.1B (2.3B effective) | Not found |

‡ Discrepancy: gemma4all.com reports 84.3%, pricepertoken.com reports 85.7%. Likely different eval conditions or thinking mode.

### DeepSeek V4 Flash

| Model | GPQA Diamond | Params | Notes |
|-------|-------------|--------|-------|
| DeepSeek V4 Flash | 89.4 | 284B (13B active) | pricepertoken. Non-reasoning. Best value at this tier. |
| DeepSeek V4 Flash (HF card) | — | 284B | HF card doesn't report GPQA Diamond |

**Huge signal for SubstitutionBench:** DeepSeek V4 Flash scores 89.4% on GPQA Diamond (non-reasoning!)
at $0.098/$0.197 per million tokens. That's within 5 points of GPT-5.4 (92.0%) at ~1/50th the price.

### MiniMax Family

| Model | GPQA Diamond | Params | Source |
|-------|-------------|--------|--------|
| MiniMax M2.7 | 87.4 | ~230B | pricepertoken. Strong near-frontier score. |
| MiniMax M2.5 | 80.1†† | 230B (10B active) | pricepertoken Tier 3 estimate. |

†† Pricepertoken places MiniMax M2.5 in Tier 3 (80-84.9%) but doesn't list exact score in the summary.

### GPT-5.4 Family

| Model | GPQA Diamond | Params | Notes |
|-------|-------------|--------|-------|
| GPT-5.4 (flagship) | 92.0 | — | pricepertoken |
| GPT-5.4 Mini | 82.8 | — | pricepertoken, Interfaze.ai. Per-domain: Physics 90.7%, Chem 75.3%, Bio 84.2% |
| GPT-5.4 Mini (llm-stats) | 92.8 | — | llm-stats.com reports 92.8% — massive discrepancy! Likely different eval conditions |
| GPT-5.4 Nano | — | — | Not found for GPQA Diamond |

**Important:** 82.8% vs 92.8% discrepancy for GPT-5.4 Mini — mirrors the MATH-500 issue.
The 82.8% (Interfaze/pricepertoken) is likely standard eval; 92.8% may be high-effort/thinking mode.

### Claude Haiku 4.5

| Model | GPQA Diamond | Params | Source |
|-------|-------------|--------|--------|
| Claude Haiku 4.5 | 67.2 | — | OpenRouter/Artificial Analysis (reasoning) |
| Claude Haiku 4.5 (non-thinking) | 40.0† | — | serenitiesai.com |

† Very low non-thinking score. The 67.2% is already with reasoning/thinking.

## Full Leaderboard (PricePerToken — Tiered)

### Tier 1: 90%+ (Frontier — 6 models)
| Rank | Model | Score | In $/M | Out $/M |
|------|-------|-------|--------|---------|
| 1 | Gemini 3.1 Pro Preview | 94.1 | $2.00 | $12.00 |
| 2 | Qwen3.7 Max | 92.3 | $1.25 | $3.75 |
| 3 | Gemini 3.5 Flash | 92.2 | $1.50 | $9.00 |
| 4 | GPT-5.4 | 92.0 | $2.50 | $15.00 |
| 5 | GPT-5.3 Codex | 91.5 | $1.75 | $14.00 |
| 6 | Claude Opus 4.7 | 91.4 | $5.00 | $25.00 |

### Tier 2: 85-89.9% (Near-Frontier — 15 models)
| Model | Score | In $/M | Out $/M |
|-------|-------|--------|---------|
| **DeepSeek V4 Flash** | **89.4** | **$0.098** | **$0.197** |
| **Qwen3.5 397B A17B** | **89.3** | $0.390 | $0.900 |
| **DeepSeek V4 Pro** | **88.8** | $0.435 | $0.870 |
| **MiniMax M2.7** | **87.4** | $0.279 | $1.200 |
| DeepSeek V3.2 Speciale | 87.1 | $0.270 | $0.400 |
| **Gemma 4 31B** | **85.7** | **$0.120** | **$0.370** |
| Grok 4.1 Fast Thinking | 85.3 | $0.000 | $0.000 (free) |
| Step 3.5 Flash | 83.1 | $0.090 | $0.300 |
| GPT-5 Mini | 82.8 | $0.125 | $1.000 |
| GPT-OSS-120B | 78.2 | $0.039 | $0.100 |

### Tier 3: 80-84.9% (Strong — ~25 models)
| Model | Score | In $/M | Out $/M | Notes |
|-------|-------|--------|---------|-------|
| GPT-5.4 Mini | 82.8 | $0.40 | $1.60 | pricepertoken (standard eval) |
| MiniMax M2.5 | ~80 | $0.15 | $1.15 | Estimated from tier placement |

### Tier 4: 70-79.9% (Capable)
| Model | Score | Notes |
|-------|-------|-------|
| Claude Sonnet 4 Thinking | 77.7 | pricepertoken |
| DeepSeek R1 | 70.8 | pricepertoken |
| o1 | 74.7 | pricepertoken |
| Claude Haiku 4.5 (thinking) | 67.2 | OpenRouter/AA |

### Tier 5: Below 70%
| Model | Score | Notes |
|-------|-------|-------|
| GPT-4.1 | 66.6 | pricepertoken |
| Claude 3.5 Sonnet | 59.9 | pricepertoken |
| GPT-4o Mini | 42.6 | pricepertoken |
| Claude Haiku 4.5 (non-thinking) | 40.0 | serenitiesai |

## Qwen 3.5 vs Gemma 4 Comparison (from gemma4all.com)

| Benchmark | Qwen3.5 27B | Gemma 4 31B | Edge |
|-----------|-------------|-------------|------|
| MMLU-Pro | 86.1% | 85.2% | Qwen (+0.9) |
| **GPQA Diamond** | **85.5%** | **84.3%** | **Qwen (+1.2)** |
| LiveCodeBench v6 | 80.7% | 80.0% | Qwen (+0.7) |
| TAU2 (agentic) | 79.0% | 76.9% | Qwen (+2.1) |
| MMMLU | 85.9% | 88.4% | Gemma (+2.5) |

| Benchmark | Qwen3.5 35B-A3B | Gemma 4 26B-A4B | Edge |
|-----------|-----------------|-----------------|------|
| MMLU-Pro | 85.3% | 82.6% | Qwen (+2.7) |
| **GPQA Diamond** | **84.2%** | **82.3%** | **Qwen (+1.9)** |
| TAU2 (agentic) | 81.2% | 68.2% | Qwen (+13.0!) |

| Benchmark | Qwen3.5 4B | Gemma 4 E4B | Edge |
|-----------|-----------|------------|------|
| MMLU-Pro | 79.1% | 69.4% | Qwen (+9.7) |
| **GPQA Diamond** | **76.2%** | **58.6%** | **Qwen (+17.6!)** |

## GPQA Diamond vs MATH-500: Key Comparison

This comparison highlights why GPQA Diamond is better for SubstitutionBench:

| Metric | MATH-500 | GPQA Diamond |
|--------|----------|-------------|
| **Best score** | 99.4% | 94.1% |
| **Avg score** | 83.5% | 66.9% |
| **Std dev** | 16.3 | 17.1 |
| **Frontier floor distance** | ~3% (99.4 vs 96) | ~5% (94.1 vs 89) |
| **Budget floor distance** | ~10% (99.4 vs 89) | ~24% (94.1 vs 70) |
| **Score spread** | 85 points | 74 points |
| **Saturation** | Heavy (50+ models >90%) | Moderate |
| **Small model scores** | Qwen3 4B: 93.3% | Qwen3.5 4B: 76.2% |
| **Substitution insight** | "Everyone's good at math now" | Real cost/size differentiation |

**GPQA Diamond is clearly the better choice:**
- Wider score spread in the interesting substitution zone (70-90%)
- Less saturation — small models DON'T hit frontier scores
- More differentiation between model tiers
- The "DeepSeek V4 Flash at $0.10 getting 89.4% while Claude Sonnet 4 Thinking gets 77.7%" story is the EXACT signal SubstitutionBench is designed to surface

## Data Gaps

1. **Qwen3.6-Plus GPQA Diamond** — Still absent. May not have been evaluated.
2. **GPT-5.4 Mini discrepancy** — 82.8% vs 92.8% needs resolution (eval conditions).
3. **MiniMax M2.5 exact score** — Estimated ~80% from tier, not pinned.
4. **Gemma 4 31B discrepancy** — 84.3% vs 85.7% across sources.
5. **Per-domain breakdowns** — Only available for 5 models on Interfaze.ai. More would be valuable.

## Key Early Insights

- **DeepSeek V4 Flash is the SubstitutionBench poster child** — 89.4% at $0.098/$0.197 per M tokens.
  That's 97% of frontier performance (relative to 92.0%) at ~1/50th the cost.
- **Open-weight models punch way above their weight** — Gemma 4 31B (85.7%) at $0.12/$0.37
  beats Claude Sonnet 4 Thinking (77.7%) at $3/$15. A 31B open model substitutes for
  a frontier proprietary model on graduate science.
- **Qwen3.5 dominates on GPQA Diamond** — The 4B model (76.2%) beats Gemma 4 E4B (58.6%)
  by 17 points. The 27B model (85.5%) beats Gemma 4 31B (84.3%). Clear family-level advantage.
- **Claude family is surprisingly weak on GPQA Diamond** — Claude Sonnet 4 Thinking at 77.7%
  and Claude Haiku 4.5 at 67.2% trail similarly-priced models by 10-15 points. This is likely
  a knowledge/evaluation artifact, not a capability gap, but it's exactly the kind of finding
  SubstitutionBench would surface.
- **The thinking mode gap is smaller on GPQA Diamond than MATH-500** — Likely because GPQA
  is more knowledge-dependent than reasoning-dependent. Good for cleaner comparisons.
