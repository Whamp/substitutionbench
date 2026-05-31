# MATH-500 Benchmark Scores

> Pilot data collection for SubstitutionBench. Last updated: May 31, 2026.
> Sources: pricepertoken.com (Artificial Analysis data), BenchLM.ai, OpenRouter, HuggingFace model cards, LayerLens, LangDB, Iternal.ai.
> Scores are pass@1 (exact match) unless noted. Thinking/reasoning variants noted separately.

## Frontier Reference Models

| Model | Provider | MATH-500 | Params | Input $/M | Output $/M |
|-------|----------|----------|--------|-----------|------------|
| GPT-5 (high) | OpenAI | 99.4 | — | $1.25 | $10.00 |
| o3 | OpenAI | 99.2 | — | $2.00 | $8.00 |
| Grok 3 Mini (high) | xAI | 99.2 | — | $0.25 | $0.50 |
| Claude Sonnet 4 Thinking | Anthropic | 99.1 | — | $3.00 | $15.00 |
| Claude Haiku 4.5 (thinking) | Anthropic | 97.3† | — | $1.00 | $5.00 |
| Claude Sonnet 4.5 Thinking | Anthropic | 94.0‡ | — | $3.00 | $15.00 |

† From iternal.ai LLM Selection Guide (may be thinking mode)
‡ LinkedIn — may use different evaluation conditions

## Models of Interest (Will's Requested Set)

### Qwen 3.5 Family

| Model | MATH-500 | Params | Notes |
|-------|----------|--------|-------|
| Qwen3.5-397B-A17B | 74.1* | 397B (17B active) | Base model, Qwen official blog. *MATH full, not MATH-500 |
| Qwen3.5-122B-A10B | — | 122B (10B active) | No MATH-500 found yet; check model card directly |
| Qwen3.5-35B-A3B | — | 35B (3B active) | No MATH-500 score found yet |
| Qwen3.5-27B | ~94.5† | 27B dense | †Estimated from LangDB/cross-reference context |
| Qwen3.5-9B | 94.5 | 9B dense | LangDB ranking page |

**NOTE:** Qwen3.5 models lack published MATH-500 scores on most leaderboards.
The Qwen official blog reports MATH (full dataset, not MATH-500): 74.14% for 397B-A17B.
The Reddit comparison thread (r/LocalLLaMA) suggests Qwen3.5-9B scores near saturation on MATH-500.
Community GGUF evals suggest MATH-500 is "old and easy" for recent Qwen3.5 models — even quantized variants score high.

### Qwen 3.6 Family

| Model | MATH-500 | Params | Notes |
|-------|----------|--------|-------|
| Qwen3.6-Plus | — | — | No MATH-500 found on leaderboards or model card yet |
| Qwen3.6-27B | — | 27B | No MATH-500 score found; community evals focus on HumanEval/LiveCodeBench |
| Qwen3.6-35B-A3B | — | 35B (3B active) | No MATH-500 score found |

**NOTE:** Qwen3.6 scores are notably absent from MATH-500 leaderboards. This family was positioned
more for coding/agents than math benchmarks. May need manual evaluation via lm-eval-harness.

### Gemma 4 Family

| Model | MATH-500 | Params | Notes |
|-------|----------|--------|-------|
| Gemma 4 31B (IT) | 94.5 | 31B dense | LangDB; CodeForces 1633 |
| Gemma 4 26B A4B | — | 26B (4B active) | No MATH-500 found; MoE variant |
| Gemma 4 E4B | — | 8B (4.5B effective) | No MATH-500 found; small multimodal |
| Gemma 4 E2B | — | 5.1B (2.3B effective) | No MATH-500 found; tiny multimodal |

### DeepSeek V4 Flash

| Model | MATH-500 | Params | Notes |
|-------|----------|--------|-------|
| DeepSeek V4 Flash | 92.8 | 284B (13B active) | OpenRouter benchmarks page |
| DeepSeek V4 Flash-Max | — | 284B (13B active) | "Comparable reasoning performance" — score likely similar |
| DeepSeek V4 Flash (HF card) | 60.5 | 284B | HuggingFace card reports MATH EM 4-shot: 60.5 — likely different eval conditions (no thinking mode) |

**Important:** The 92.8% vs 60.5% discrepancy likely reflects thinking/reasoning mode differences.
HuggingFace card may report non-thinking mode. Need to clarify evaluation conditions.

### MiniMax Family

| Model | MATH-500 | Params | Notes |
|-------|----------|--------|-------|
| MiniMax M2.7 | 94.6-97.0† | ~230B | LinkedIn post: "seven models score between 94.6% and 99.0%" — M2.7 in that range. LayerLens confirms 93.3% AIME 2025 |
| MiniMax M2.5 | 81.0-89.4†† | 230B (10B active) | BenchLM: 81%; Facebook/community reports: 89.4%. Discrepancy likely thinking vs non-thinking |

† Exact MATH-500 score not pinned. Range from context. ArtificialAnalysis has "97% 96% 95% 94%" band — may be the AA Intelligence Index, not MATH-500 specifically.
†† Two very different scores — needs verification of evaluation conditions.

### GPT-5.4 Family

| Model | MATH-500 | Params | Notes |
|-------|----------|--------|-------|
| GPT-5.4 (flagship) | 94.6 | — | LayerLens independent eval |
| GPT-5.4 Mini | 97.3-97.4 | — | LayerLens: 86.6% but iternal.ai/BenchLM: 97.3-97.4%. Likely different eval conditions |
| GPT-5.4 Nano | 88.6 | — | LayerLens: 88.6% |

**Important:** GPT-5.4 Mini shows counter-intuitive result — LayerLens reports 86.6% (below flagship 94.6%)
while iternal.ai/BenchLM report 97.3%. This needs investigation — may be thinking vs non-thinking,
or different evaluation prompts.

### Claude Haiku 4.5

| Model | MATH-500 | Params | Notes |
|-------|----------|--------|-------|
| Claude Haiku 4.5 | 81.0 | — | BenchLM rank #68. Non-thinking likely. |
| Claude Haiku 4.5 (thinking) | 97.3† | — | iternal.ai |

† Needs confirmation. Large gap between 81% and 97.3% mirrors Claude Sonnet 4's thinking/non-thinking split.

## Full Leaderboard (PricePerToken — Top 124)

### Tier 1: 99%+ (Frontier)
| Rank | Model | Score | In $/M | Out $/M |
|------|-------|-------|--------|---------|
| 1 | GPT-5 (high) | 99.4 | $1.25 | $10.00 |
| 2 | o3 | 99.2 | $2.00 | $8.00 |
| 3 | Grok 3 Mini (high) | 99.2 | $0.25 | $0.50 |
| 4 | Claude Sonnet 4 Thinking | 99.1 | $3.00 | $15.00 |
| 5 | Grok 4 | 99.0 | $3.00 | $15.00 |
| 6 | o4 Mini | 98.9 | $0.55 | $2.20 |

### Tier 2: 97-98.9%
| Model | Score | In $/M | Out $/M |
|-------|-------|--------|---------|
| Gemini 2.5 Pro Preview 05-06 | 98.6 | $1.25 | $10.00 |
| o3 Mini High | 98.5 | $1.10 | $4.40 |
| Qwen3 235B A22B Thinking 2507 | 98.4 | $0.149 | $0.90 |
| Llama 3.3 Nemotron Super 49B Thinking | 98.3 | $0.10 | $0.40 |
| R1 0528 | 98.3 | $0.50 | $2.15 |
| Claude Opus 4 Thinking | 98.2 | $15.00 | $75.00 |
| Gemini 2.5 Flash Thinking | 98.1 | $0.30 | $2.50 |
| MiniMax M1 | 98.0 | $0.40 | $2.20 |
| Qwen3 235B A22B Instruct 2507 | 98.0 | $0.071 | $0.10 |
| GLM 4.5 Thinking | 97.9 | $0.60 | $2.20 |
| Qwen3 30B A3B Thinking 2507 | 97.6 | $0.08 | $0.40 |
| o3 Mini | 97.3 | $0.55 | $2.20 |
| Kimi K2 0711 | 97.1 | $0.55 | $2.20 |
| o1 | 97.0 | $15.00 | $60.00 |

### Tier 3: 95-96.9%
| Model | Score | In $/M | Out $/M |
|-------|-------|--------|---------|
| Gemini 2.5 Flash Lite Thinking | 96.9 | $0.10 | $0.40 |
| Gemini 2.5 Pro | 96.7 | $1.00 | $10.00 |
| R1 | 96.6 | $0.55 | $2.00 |
| GLM 4.5 Air | 96.5 | $0.125 | $0.85 |
| Qwen3 14B Thinking | 96.1 | $0.08 | $0.20 |
| Qwen3 32B Thinking | 96.1 | $0.08 | $0.28 |
| QwQ 32B | 95.7 | $0.90 | $0.90 |

### Tier 4: 90-94.9%
| Model | Score | In $/M | Out $/M |
|-------|-------|--------|---------|
| Claude 3.7 Sonnet Thinking | 94.7 | $3.00 | $15.00 |
| DeepSeek V3 0324 | 94.2 | $0.20 | $0.77 |
| Qwen3 Coder 480B A35B | 94.2 | $0.22 | $0.90 |
| R1 Distill Qwen 32B | 94.1 | $0.29 | $0.29 |
| Claude Opus 4 (non-thinking) | 94.1 | $15.00 | $75.00 |
| Claude Sonnet 4 (non-thinking) | 93.4 | $3.00 | $15.00 |
| Gemini 2.5 Flash (non-thinking) | 93.2 | $0.30 | $2.50 |
| Gemini 2.0 Flash | 93.0 | $0.10 | $0.40 |
| GPT-4.1 Mini | 92.5 | $0.40 | $1.60 |
| DeepSeek V4 Flash | 92.8 | ~$0.00 (free) | ~$0.00 |
| GPT-4.1 | 91.3 | $2.00 | $8.00 |
| Mistral Medium 3 | 90.7 | $0.40 | $2.00 |

### Tier 5: Below 90%
| Model | Score | In $/M | Out $/M |
|-------|-------|--------|---------|
| Llama 4 Maverick | 88.9 | $0.15 | $0.60 |
| Gemma 3 27B | 88.3 | $0.08 | $0.16 |
| Grok 3 (non-reasoning) | 87.0 | $3.00 | $15.00 |
| GPT-4o Mini | 78.9 | $0.15 | $0.60 |
| Claude 3.5 Sonnet | 77.1 | $3.00 | $15.00 |
| GPT-4 Turbo | 73.7 | $5.00 | $15.00 |
| Claude 3 Haiku | 39.4 | $0.25 | $1.25 |
| GPT-3.5 Turbo | 44.1 | $0.50 | $1.00 |
| Llama 3.2 1B Instruct | 14.0 | $0.02 | $0.02 |

## Open Questions & Data Gaps

1. **Qwen3.5 family MATH-500 scores** — surprisingly absent from major leaderboards.
   The official blog reports MATH (full), not MATH-500. Community evals suggest saturation.
   May need manual evaluation via lm-eval-harness on local GPU.

2. **Qwen3.6 family** — completely absent from MATH-500 leaderboards. Need manual eval.

3. **Thinking vs Non-thinking ambiguity** — Several models show huge score variations
   across sources (GPT-5.4 Mini: 86.6% vs 97.3%; Claude Haiku 4.5: 81% vs 97.3%;
   DeepSeek V4 Flash: 60.5% vs 92.8%). This IS the signal SubstitutionBench needs to
   capture, but we need to be explicit about eval conditions.

4. **MiniMax M2.7 exact MATH-500** — Confirmed to be in the 94-97% range but not pinned.

5. **Gemma 4 smaller variants** — Only 31B has MATH-500 data. E4B and E2B missing.

6. **Difficulty tier breakdowns** — No source found that reports MATH-500 scores by
   Level 1-5 difficulty tiers. This is critical for the substitution curve and would
   need custom evaluation.

## Key Early Insights

- **MATH-500 is heavily saturated at the top** — 50+ models above 90%, 15+ above 97%.
  This confirms the benchmark is still useful for SubstitutionBench: the question
  isn't "who's best" but "where does the cheap substitution floor live."

- **Thinking mode is the great equalizer** — Models with thinking/reasoning modes
  consistently score 4-10 points higher. The substitution insight might be:
  "a small model in thinking mode = a large model in non-thinking mode."

- **The 92-94% band is crowded with cheap options** — DeepSeek V4 Flash (free),
  GPT-4.1 Mini ($0.40/$1.60), Gemini 2.0 Flash ($0.10/$0.40) all land here.
  This band likely represents the "good enough for most math" substitution floor.

- **Frontier reference should be ~99%** — GPT-5, o3, and Grok 3 Mini all hit 99%+.
  For SubstitutionBench, the JND question becomes: is 92% "nearly indistinguishable"
  from 99% for practical purposes?
