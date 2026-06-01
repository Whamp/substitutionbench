# SubstitutionBench Design Notes

## Visual strategy

Dark product dashboard with restrained color. Bar color encodes substitution state, not provider identity:

- Violet: frontier anchor / frontier context.
- Green: clears the `% of frontier` cutoff and is cheaper than frontier — usable substitute.
- Amber: clears the quality cutoff but is not an economic substitute yet because price is missing or not cheaper than frontier.
- Red/gray: below the selected quality cutoff.

Provider identity is secondary and should be shown via logo, initials, or metadata labels rather than bar color.

## Typography

Use Inter for UI and JetBrains Mono for numeric labels, prices, score gaps, and compact data chips. Prefer fixed product UI sizing over marketing-scale fluid typography.

## Layout principles

- Mobile-first validation: default SubstitutionBench Index hero chart, component-index drilldowns, selected task family chart, threshold control, API-cost ranking for qualified models, universe/source transparency.
- Visual encodings should carry the story before explanatory copy.
- The core chart question is not “which model wins?” but “how close is each model to frontier, and which close-enough models are cheap?”
- If no cheaper model clears the selected `% of frontier` cutoff for a task family, the chart must clearly state “no substitute yet” rather than hide the benchmark or imply a weak substitute.
- `% of frontier` is the primary y-axis for both curated-index hero charts and per-benchmark charts.
- API price/cost is the primary ordering axis for qualified models once the quality threshold is met.
- Quality distance from frontier is a qualifier and confidence signal, not the whole product.
- API pricing is the MVP cost model.
- Local hardware cost mode is a future feature; when added, it must filter eligibility by model size/fit threshold before ranking by local economics.
- Hardware and electricity assumptions should have smart defaults, but visible user controls must exist once local mode exists because the benchmark is meant to help users choose for their own hardware.
- Benchmark cards must explain what task type the score represents, including an example question shape.
- Tables are secondary evidence and should degrade into grouped cards on mobile.

## Components

- Continuous frontier-quality threshold control with visible focus and active state. Default is 95% of frontier score; users can set values like 93% or 90%.
- Hero index bar chart: x-axis model name, y-axis `% of frontier` for the selected curated index.
- Bar chart ordering: sort by `% of frontier` descending; cost is not the ordering dimension in the primary quality chart.
- Index membership requires complete benchmark coverage: a model appears in an index only if it has data for every benchmark in that index.
- Per-benchmark bar chart: x-axis model name, y-axis `% of frontier` for the selected benchmark, with the continuous threshold line shown.
- Cutoff indicator: sort bar charts by `% of frontier` and show the quality cutoff as a vertical separator between models that meet the threshold and models that do not. The separator delineates the qualifying model set, not the numeric y-axis value.
- No-substitute state: when no cheaper non-frontier model clears the cutoff, show an explicit frontier-bound / no-substitute-yet badge or callout on the task card and keep the chart visible as evidence.
- Future cost-assumption controls for local inference: hardware profile, model size/fit threshold, electricity rate, task token volume, and throughput.
- Benchmark status rows showing selected task family, qualifying model count, cheapest qualifying model, price, score ratio, and savings multiple.
- Plain-language threshold explanation tied to the selected frontier-score ratio and frontier anchor.
- Benchmark guide cards with task description, example question shape, and source scope.
- Analysis universe section showing observation rows, unique model count, source mix, included model lists, cache freshness, and unresolved source conflicts.
- Artificial Analysis-inspired plot deck: selected-index `% of frontier` hero bar chart, selected-benchmark `% of frontier` bar chart, and API-cost ranking for qualified models.
- The primary substitution plot is the **curated index frontier-coverage chart**: each model's `% of frontier` for a selected, versioned benchmark basket.
- The selected task-family plot uses the same bar-chart grammar with a visible qualification threshold line.
- Estimated API task cost is the secondary sort key for models that meet the quality threshold; `$ / 1M tokens`, runtime, tok/s, power draw, and model size are supporting labels.
- Token economics bars are log-compressed so cheap floors remain visible next to frontier pricing.
- Frontier-score ratio sensitivity belongs in the selected threshold control and live decision line; point-gap/JND sensitivity is secondary audit mode, not the default product grammar.

## Accessibility

- Do not rely on color alone. Pair state colors with labels.
- Touch targets should be at least 44px.
- Charts need text equivalents in nearby cards.
- No horizontal scrolling as the primary mobile path.
