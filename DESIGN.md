# SubstitutionBench Design Notes

## Visual strategy

Dark product dashboard with restrained color. Green means inside the selected JND band. Red means outside band. Violet is reserved for selected controls and frontier anchors.

## Typography

Use Inter for UI and JetBrains Mono for numeric labels, prices, score gaps, and compact data chips. Prefer fixed product UI sizing over marketing-scale fluid typography.

## Layout principles

- Mobile-first validation: answer, threshold explanation, benchmark status, chart, universe transparency, details.
- Visual encodings should carry the story before explanatory copy.
- Price is the primary visual axis for substitution floors.
- Coverage is secondary and should not be the dominant bar length in floor summaries.
- Benchmark cards must explain what task type the score represents, including an example question shape.
- Tables are secondary evidence and should degrade into grouped cards on mobile.

## Components

- Segmented JND selector with visible focus and active states.
- Benchmark status rows showing benchmark, status, floor model, price, gap, and savings multiple.
- Plain-language JND explanation tied to the selected threshold and benchmark frontier score.
- Benchmark guide cards with task description, example question shape, and source scope.
- Analysis universe section showing observation rows, unique model count, source mix, and included model lists.
- Artificial Analysis-style substitution curve: benchmark-selected score bars sorted by input price, with direct score labels and a visible JND cutoff line.
- Threshold sensitivity matrix for 1, 3, and 5 point JND bands.

## Accessibility

- Do not rely on color alone. Pair state colors with labels.
- Touch targets should be at least 44px.
- Charts need text equivalents in nearby cards.
- No horizontal scrolling as the primary mobile path.
