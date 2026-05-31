# SubstitutionBench Design Notes

## Visual strategy

Dark product dashboard with restrained color. Green means inside the selected JND band. Red means outside band. Violet is reserved for selected controls and frontier anchors.

## Typography

Use Inter for UI and JetBrains Mono for numeric labels, prices, score gaps, and compact data chips. Prefer fixed product UI sizing over marketing-scale fluid typography.

## Layout principles

- Mobile-first validation: answer, threshold, benchmark status, chart, details.
- Visual encodings should carry the story before explanatory copy.
- Price is the primary visual axis for substitution floors.
- Coverage is secondary and should not be the dominant bar length in floor summaries.
- Tables are secondary evidence and should degrade into grouped cards on mobile.

## Components

- Segmented JND selector with visible focus and active states.
- Benchmark status rows showing benchmark, status, floor model, price, gap, and savings multiple.
- Selected benchmark evidence ladder comparing cheap candidates against the frontier anchor.
- Threshold sensitivity matrix for 1, 3, and 5 point JND bands.

## Accessibility

- Do not rely on color alone. Pair state colors with labels.
- Touch targets should be at least 44px.
- Charts need text equivalents in nearby cards.
- No horizontal scrolling as the primary mobile path.
