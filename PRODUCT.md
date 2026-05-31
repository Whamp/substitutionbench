# SubstitutionBench Product Context

## Product

SubstitutionBench is an inverse benchmark for LLM model selection. It asks: which cheaper or smaller model is close enough to the frontier on a specific task family?

## Primary user

A technical decision-maker evaluating model spend from a phone or laptop. They need to trust the substitution story quickly without reading source data or code.

## Dashboard job

The MVP dashboard should make five facts obvious within seconds:

1. Which benchmarks are saturated enough to substitute.
2. Which model is the cheapest frontier-equivalent floor at the selected JND threshold.
3. What the selected JND threshold means in plain English.
4. Which models and sources are actually included in the analysis universe.
5. Which benchmarks still require frontier models.

## Register

Product dashboard. Design serves decision-making. It should feel closer to Linear, Stripe dashboards, or a quant research terminal than a marketing page.

## Tone

Precise, terse, skeptical. Avoid hype. Use benchmark language consistently: JND band, substitution floor, frontier anchor, in-band, outside band.

## Anti-goals

- Not a public landing page yet.
- Not a full research report.
- Not a leaderboard crowning the smartest model.
- Not a giant table that requires desktop inspection.
