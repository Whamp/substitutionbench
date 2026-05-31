const state = {
  threshold: 3,
  benchmark: 'MATH-500',
};

const data = window.SUBSTITUTION_BENCH_DATA;
const observations = data.observations;
const benchmarks = Object.keys(data.configs);
const thresholds = data.thresholds;

const benchmarkMeta = {
  'MATH-500': {
    plain: 'High-school competition math: algebra, geometry, number theory, precalculus, and counting problems with exact answers.',
    example: 'Example shape: convert coordinates, count divisors, solve a geometry volume problem, or reduce a finite/infinite algebra expression.',
    substitution: 'Good for tasks where the answer is checkable and the reasoning path is mostly mathematical.',
    source: '500-problem MATH subset used by OpenAI in Let\u2019s Verify Step by Step.',
  },
  'GPQA Diamond': {
    plain: 'Graduate-level, Google-proof science multiple choice across biology, chemistry, and physics.',
    example: 'Example shape: choose the correct mechanism, physical relationship, or experimental implication when surface web search is not enough.',
    substitution: 'Good for hard expert science QA, not ordinary trivia or broad web lookup.',
    source: '198-question Diamond split from GPQA, written by domain experts.',
  },
  'SWE-bench Verified': {
    plain: 'Real GitHub software issues where the model must edit a repository and produce a patch that passes tests.',
    example: 'Example shape: given a bug report and codebase, change Python code so the failing behavior is fixed without breaking tests.',
    substitution: 'Good for agentic coding and repo repair. This is where frontier models still buy capability in the MVP data.',
    source: '500 SWE-bench tasks confirmed by software engineers as solvable.',
  },
};

const sourceLabels = {
  independent: 'independent eval',
  aggregator: 'aggregator row',
  vendor: 'vendor row',
  provider: 'provider row',
};

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function dollars(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'unknown';
  return `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 4 })}/M`;
}

function pct(value, digits = 1) {
  return `${Number(value).toFixed(digits)}%`;
}

function points(value) {
  return `${Number(value).toFixed(Number(value) % 1 === 0 ? 0 : 1)} pts`;
}

function params(row) {
  const p = row.active_params_b ?? row.total_params_b;
  return p ? `${p}B${row.active_params_b ? ' active' : ''}` : 'unknown size';
}

function shortModel(model) {
  return String(model)
    .replace('Thinking', 'think')
    .replace('non-thinking', 'base')
    .replace('Verified', '')
    .replace('Preview', '')
    .trim();
}

function rowsForBenchmark(benchmark) {
  return observations.filter((row) => row.benchmark === benchmark);
}

function equivalent(row, threshold = state.threshold) {
  return row.frontier_score - row.score <= threshold;
}

function pricedRows(benchmark) {
  return rowsForBenchmark(benchmark).filter((row) => row.input_price_per_m !== null);
}

function uniqueModels(rows = observations) {
  return Array.from(new Set(rows.map((row) => row.model))).sort((a, b) => a.localeCompare(b));
}

function countBy(rows, key) {
  return rows.reduce((acc, row) => {
    const value = row[key] || 'unknown';
    acc[value] = (acc[value] ?? 0) + 1;
    return acc;
  }, {});
}

function qualificationLine(benchmark, threshold = state.threshold) {
  const frontier = frontierRow(benchmark);
  if (!frontier) return `A ${threshold} pt JND band means a model may score ${threshold} points below the frontier and still qualify.`;
  const cutoff = frontier.frontier_score - threshold;
  return `JND, or just-noticeable difference, means how much worse a cheaper model can score and still count as equivalent. At ${threshold} pts on ${benchmark}, frontier scores ${pct(frontier.frontier_score)}; any model at ${pct(cutoff)} or higher is in band.`;
}

function cheapestEquivalent(benchmark, threshold = state.threshold) {
  return pricedRows(benchmark)
    .filter((row) => equivalent(row, threshold))
    .sort((a, b) => a.input_price_per_m - b.input_price_per_m || b.score - a.score)[0] ?? null;
}

function smallestEquivalent(benchmark, threshold = state.threshold) {
  return rowsForBenchmark(benchmark)
    .filter((row) => equivalent(row, threshold) && (row.active_params_b ?? row.total_params_b) !== null)
    .sort((a, b) => (a.active_params_b ?? a.total_params_b) - (b.active_params_b ?? b.total_params_b))[0] ?? null;
}

function frontierRow(benchmark) {
  const cfg = data.configs[benchmark];
  return rowsForBenchmark(benchmark).find((row) => row.model === cfg.frontier_model)
    ?? rowsForBenchmark(benchmark).slice().sort((a, b) => b.score - a.score)[0]
    ?? null;
}

function isSaturatedKind(kind) {
  return kind === 'saturated' || kind === 'near_saturated';
}

function substitutionStatus(benchmark, threshold = state.threshold) {
  const floor = cheapestEquivalent(benchmark, threshold);
  const frontier = frontierRow(benchmark);
  const cfg = data.configs[benchmark];
  if (!floor) {
    return { benchmark, label: 'No priced floor', tone: 'red', action: 'frontier', copy: 'Missing priced candidate rows', floor, frontier, cfg };
  }
  const sameAsFrontier = frontier && floor.model === frontier.model;
  if (sameAsFrontier || !isSaturatedKind(cfg.benchmark_kind)) {
    return { benchmark, label: 'Frontier-bound', tone: 'red', action: 'frontier', copy: 'Frontier still matters', floor, frontier, cfg };
  }
  return { benchmark, label: 'Substitutable', tone: 'green', action: 'substitute', copy: 'Cheaper model is in band', floor, frontier, cfg };
}

function savingsMultiple(floor, frontier) {
  if (!floor?.input_price_per_m || !frontier?.input_price_per_m) return null;
  return frontier.input_price_per_m / floor.input_price_per_m;
}

function renderThresholdButtons() {
  const markup = thresholds.map((threshold) => `
    <button class="threshold ${threshold === state.threshold ? 'active' : ''}" data-threshold="${threshold}">${threshold} pt${threshold > 1 ? 's' : ''}</button>
  `).join('');
  document.querySelectorAll('.threshold-control').forEach((control) => { control.innerHTML = markup; });
  document.querySelector('.mobile-threshold').innerHTML = markup;
  document.querySelectorAll('.threshold').forEach((button) => {
    button.addEventListener('click', () => {
      state.threshold = Number(button.dataset.threshold);
      renderAll();
    });
  });
}

function renderHeadline() {
  const floors = benchmarks.map((benchmark) => ({ benchmark, ...substitutionStatus(benchmark) }));
  const substitutable = floors.filter((item) => item.action === 'substitute');
  const cheapest = substitutable
    .map((item) => ({ ...item, price: item.floor.input_price_per_m }))
    .sort((a, b) => a.price - b.price)[0]
    ?? floors.map((item) => ({ ...item, price: item.floor?.input_price_per_m ?? Infinity })).sort((a, b) => a.price - b.price)[0];

  document.getElementById('headline-price').textContent = cheapest?.floor ? dollars(cheapest.floor.input_price_per_m) : 'No floor';
  document.getElementById('headline-model').textContent = cheapest?.floor
    ? `${cheapest.floor.model} on ${cheapest.benchmark}`
    : 'No qualifying priced rows yet.';
  document.getElementById('headline-chips').innerHTML = [
    `<span class="chip ${substitutable.length ? 'green' : 'red'}">${substitutable.length}/${benchmarks.length} substitutable</span>`,
    `<span class="chip violet">${state.threshold} pt JND</span>`,
    `<span class="chip">${floors.filter((item) => item.action === 'frontier').length} frontier-bound</span>`,
  ].join('');
}

function renderJndExplainer() {
  const cheapest = benchmarks
    .map((benchmark) => ({ benchmark, status: substitutionStatus(benchmark) }))
    .filter((item) => item.status.action === 'substitute')
    .sort((a, b) => a.status.floor.input_price_per_m - b.status.floor.input_price_per_m)[0];
  const benchmark = cheapest?.benchmark ?? state.benchmark;
  document.getElementById('jnd-explainer').textContent = qualificationLine(benchmark);
}

function renderMetricStrip() {
  const statuses = benchmarks.map((benchmark) => substitutionStatus(benchmark));
  const substitutable = statuses.filter((status) => status.action === 'substitute');
  const frontierBound = statuses.filter((status) => status.action === 'frontier');
  const cheapest = substitutable.slice().sort((a, b) => a.floor.input_price_per_m - b.floor.input_price_per_m)[0];
  const biggestSavings = substitutable
    .map((status) => ({ status, multiple: savingsMultiple(status.floor, status.frontier) ?? 0 }))
    .sort((a, b) => b.multiple - a.multiple)[0];

  const cards = [
    { label: 'Saturated enough', value: `${substitutable.length}/${benchmarks.length}`, copy: 'Benchmarks with a cheaper in-band floor' },
    { label: 'Cheapest floor', value: cheapest ? dollars(cheapest.floor.input_price_per_m) : 'none', copy: cheapest ? `${shortModel(cheapest.floor.model)} · ${cheapest.benchmark}` : 'No substitutable floor' },
    { label: 'Largest price drop', value: biggestSavings?.multiple ? `${biggestSavings.multiple.toFixed(biggestSavings.multiple >= 10 ? 0 : 1)}×` : 'none', copy: biggestSavings?.multiple ? `${biggestSavings.status.benchmark} vs frontier anchor` : `${frontierBound.length} benchmark remains frontier-bound` },
  ];

  document.getElementById('metric-strip').innerHTML = cards.map((card) => `
    <article class="metric-card">
      <span class="label">${escapeHtml(card.label)}</span>
      <strong>${escapeHtml(card.value)}</strong>
      <p>${escapeHtml(card.copy)}</p>
    </article>
  `).join('');
}

function renderStatusBoard() {
  document.getElementById('status-board').innerHTML = benchmarks.map((benchmark) => {
    const status = substitutionStatus(benchmark);
    const floor = status.floor;
    const small = smallestEquivalent(benchmark);
    const multiple = savingsMultiple(floor, status.frontier);
    const actionText = status.action === 'substitute' ? 'Use floor' : 'Use frontier';
    return `
      <article class="status-row" data-action="${status.action}">
        <div class="status-main">
          <strong>${escapeHtml(benchmark)}</strong>
          <span>${escapeHtml(status.cfg.benchmark_kind.replace('_', ' '))}</span>
        </div>
        <div class="floor-model">
          <span class="chip ${status.tone}">${escapeHtml(status.label)}</span>
          <strong title="${escapeHtml(floor?.model ?? '')}">${escapeHtml(floor ? shortModel(floor.model) : 'No floor')}</strong>
          <span class="muted">${floor ? `${pct(floor.frontier_coverage)} coverage · ${points(floor.score_gap)} gap` : 'No qualifying row'}</span>
        </div>
        <div class="price-stack">
          <span class="price">${floor ? dollars(floor.input_price_per_m) : 'unknown'}</span>
          <span class="price-caption">${multiple && multiple > 1.05 ? `${multiple.toFixed(multiple >= 10 ? 0 : 1)}× cheaper than frontier` : small ? params(small) : 'frontier anchor'}</span>
        </div>
        <span class="chip ${status.tone} action-badge">${actionText}</span>
      </article>
    `;
  }).join('');
}

function renderPriceFloorChart() {
  const statuses = benchmarks.map((benchmark) => ({ benchmark, ...substitutionStatus(benchmark) }));
  const maxPrice = Math.max(...statuses.flatMap((status) => [status.floor?.input_price_per_m ?? 0, status.frontier?.input_price_per_m ?? 0]), 1);
  const minPrice = Math.min(...statuses.flatMap((status) => [status.floor?.input_price_per_m, status.frontier?.input_price_per_m].filter(Boolean)), 0.01);
  const logMin = Math.log10(minPrice);
  const logMax = Math.log10(maxPrice);
  const scale = (value) => {
    if (!value || logMax === logMin) return 4;
    return 4 + ((Math.log10(value) - logMin) / (logMax - logMin)) * 92;
  };

  document.getElementById('price-floor-chart').innerHTML = statuses.map((status) => {
    const floorWidth = scale(status.floor?.input_price_per_m);
    const frontierLeft = scale(status.frontier?.input_price_per_m);
    const multiple = savingsMultiple(status.floor, status.frontier);
    return `
      <div class="price-row">
        <div class="price-row-label">
          <strong>${escapeHtml(status.benchmark)}</strong>
          <span>${escapeHtml(status.label)}</span>
        </div>
        <div>
          <div class="price-track" aria-label="${escapeHtml(status.benchmark)} floor ${dollars(status.floor?.input_price_per_m)} frontier ${dollars(status.frontier?.input_price_per_m)}">
            <span class="price-fill" style="width: ${floorWidth}%"></span>
            <span class="frontier-tick" style="left: ${frontierLeft}%"></span>
          </div>
          <div class="price-legend"><span>floor ${dollars(status.floor?.input_price_per_m)}</span><span>frontier ${dollars(status.frontier?.input_price_per_m)}</span></div>
        </div>
        <div class="savings">${multiple && multiple > 1.05 ? `${multiple.toFixed(multiple >= 10 ? 0 : 1)}× cheaper` : 'no discount'}</div>
      </div>
    `;
  }).join('');
}

function renderThresholdMatrix() {
  const header = ['<div class="matrix-head">Benchmark</div>', ...thresholds.map((threshold) => `<div class="matrix-head">${threshold} pt</div>`)].join('');
  const rows = benchmarks.map((benchmark) => {
    const cells = thresholds.map((threshold) => {
      const status = substitutionStatus(benchmark, threshold);
      const floor = status.floor;
      const cls = status.action === 'substitute' ? 'in-band' : 'frontier-only';
      return `
        <div class="matrix-cell ${cls} ${threshold === state.threshold ? 'active-threshold' : ''}" data-threshold-label="${threshold} pt JND">
          <span class="chip ${status.tone}">${escapeHtml(status.label)}</span>
          <strong>${floor ? dollars(floor.input_price_per_m) : 'none'}</strong>
          <span>${floor ? escapeHtml(shortModel(floor.model)) : 'No priced candidate'}</span>
        </div>
      `;
    }).join('');
    return `<div class="matrix-benchmark">${escapeHtml(benchmark)}</div>${cells}`;
  }).join('');
  document.getElementById('threshold-matrix').innerHTML = header + rows;
}

function renderBenchmarkGuide() {
  document.getElementById('benchmark-guide').innerHTML = benchmarks.map((benchmark) => {
    const meta = benchmarkMeta[benchmark];
    const rows = rowsForBenchmark(benchmark);
    const status = substitutionStatus(benchmark);
    return `
      <article class="benchmark-card">
        <div class="benchmark-card-top">
          <h3>${escapeHtml(benchmark)}</h3>
          <span class="chip ${status.tone}">${escapeHtml(status.label)}</span>
        </div>
        <p>${escapeHtml(meta.plain)}</p>
        <div class="example-box">
          <span class="label">Example question shape</span>
          <p>${escapeHtml(meta.example)}</p>
        </div>
        <p class="muted">${escapeHtml(meta.substitution)}</p>
        <div class="chip-row">
          <span class="chip mono">${rows.length} rows</span>
          <span class="chip mono">${uniqueModels(rows).length} models</span>
          <span class="chip">${escapeHtml(meta.source)}</span>
        </div>
      </article>
    `;
  }).join('');
}

function renderBenchmarkSelect() {
  const select = document.getElementById('benchmark-select');
  select.innerHTML = benchmarks.map((benchmark) => `<option value="${escapeHtml(benchmark)}">${escapeHtml(benchmark)}</option>`).join('');
  select.value = state.benchmark;
  select.onchange = () => {
    state.benchmark = select.value;
    renderSelectedBenchmark();
  };
}

function renderCurveSummary() {
  const status = substitutionStatus(state.benchmark);
  const floor = status.floor;
  const frontier = status.frontier;
  const multiple = savingsMultiple(floor, frontier);
  const cutoff = frontier ? frontier.frontier_score - state.threshold : null;
  const rows = pricedRows(state.benchmark);
  const cards = [
    { label: 'Chart order', value: 'Cheap → costly', copy: `${rows.length} priced models shown` },
    { label: 'JND cutoff', value: cutoff !== null ? `≥${pct(cutoff)}` : 'none', copy: `${state.threshold} pts below frontier qualifies` },
    { label: 'Cheapest in band', value: floor ? dollars(floor.input_price_per_m) : 'none', copy: floor ? `${shortModel(floor.model)}${multiple && multiple > 1.05 ? ` · ${multiple.toFixed(multiple >= 10 ? 0 : 1)}× cheaper` : ''}` : 'No candidate' },
  ];
  document.getElementById('curve-summary').innerHTML = cards.map((card) => `
    <article class="summary-card">
      <span class="label">${escapeHtml(card.label)}</span>
      <strong>${escapeHtml(card.value)}</strong>
      <span class="muted">${escapeHtml(card.copy)}</span>
    </article>
  `).join('');
}

function renderSubstitutionCurve() {
  const rows = pricedRows(state.benchmark).slice().sort((a, b) => a.input_price_per_m - b.input_price_per_m || b.score - a.score);
  const frontier = frontierRow(state.benchmark);
  const cutoff = frontier ? frontier.frontier_score - state.threshold : 0;
  const minScore = Math.min(...rows.map((row) => row.score), cutoff);
  const domainMin = Math.max(0, Math.floor((minScore - 5) / 5) * 5);
  const scaleScore = (score) => Math.max(0, Math.min(100, ((score - domainMin) / (100 - domainMin)) * 100));
  const cutoffLeft = scaleScore(cutoff);
  const cheapest = cheapestEquivalent(state.benchmark);

  const bars = rows.map((row, index) => {
    const ok = equivalent(row);
    const isFrontier = row.model === frontier?.model;
    const isFloor = row.model === cheapest?.model;
    const tone = isFrontier ? 'frontier' : ok ? 'in-band' : 'out-band';
    return `
      <article class="curve-row ${tone} ${isFloor ? 'floor' : ''}">
        <div class="curve-rank">${index + 1}</div>
        <div class="curve-model">
          <strong title="${escapeHtml(row.model)}">${escapeHtml(shortModel(row.model))}</strong>
          <span>${dollars(row.input_price_per_m)} input · ${points(row.score_gap)} gap</span>
        </div>
        <div class="curve-bar-wrap" aria-label="${escapeHtml(row.model)} score ${pct(row.score)} cutoff ${pct(cutoff)}">
          <span class="curve-jnd-zone" style="left:${cutoffLeft}%"></span>
          <span class="curve-cutoff ${cutoffLeft > 80 ? 'label-left' : ''}" style="left:${cutoffLeft}%"><span>${pct(cutoff)} cutoff</span></span>
          <span class="curve-bar" style="width:${scaleScore(row.score)}%"></span>
        </div>
        <div class="curve-score">
          <strong>${pct(row.score)}</strong>
          <span class="chip ${ok ? 'green' : 'red'}">${isFrontier ? 'Frontier' : isFloor ? 'Floor' : ok ? 'In band' : 'Below band'}</span>
        </div>
      </article>
    `;
  }).join('');

  document.getElementById('substitution-curve').innerHTML = `
    <div class="curve-toolbar">
      <div class="chip-row">
        <span class="chip mono">${rows.length} of ${rows.length} models</span>
        <span class="chip violet">zoomed ${pct(domainMin, 0)}–100%</span>
        <span class="chip green">green = substitute</span>
      </div>
      <div class="curve-axis"><span>${pct(domainMin, 0)}</span><span>Benchmark score</span><span>100%</span></div>
    </div>
    <div class="curve-list">${bars}</div>
  `;
}

function renderObservationCards() {
  const rows = rowsForBenchmark(state.benchmark).slice().sort((a, b) => a.score_gap - b.score_gap || (a.input_price_per_m ?? Infinity) - (b.input_price_per_m ?? Infinity));
  document.getElementById('observation-cards').innerHTML = rows.map((row) => {
    const ok = equivalent(row);
    return `
      <article class="observation-card">
        <div>
          <strong>${escapeHtml(row.model)}</strong>
          <div class="observation-meta">
            <span class="chip ${ok ? 'green' : 'red'}">${ok ? 'In band' : 'Outside band'}</span>
            <span class="chip mono">${pct(row.score)} score</span>
            <span class="chip mono">${points(row.score_gap)} gap</span>
            <span class="chip mono">${dollars(row.input_price_per_m)}</span>
          </div>
        </div>
        <a class="chip" href="${escapeHtml(row.source_url)}">${escapeHtml(row.source_quality)}</a>
      </article>
    `;
  }).join('');
}

function renderModelUniverse() {
  const allModels = uniqueModels();
  const sourceCounts = countBy(observations, 'source_quality');
  const sourceChips = Object.entries(sourceCounts)
    .sort((a, b) => b[1] - a[1])
    .map(([source, count]) => `<span class="chip mono">${count} ${escapeHtml(sourceLabels[source] ?? source)}</span>`)
    .join('');

  const benchmarkBlocks = benchmarks.map((benchmark) => {
    const rows = rowsForBenchmark(benchmark);
    const models = uniqueModels(rows);
    const sourceMix = Object.entries(countBy(rows, 'source_quality'))
      .sort((a, b) => b[1] - a[1])
      .map(([source, count]) => `${count} ${source}`)
      .join(' · ');
    return `
      <article class="universe-benchmark">
        <div class="benchmark-card-top">
          <h3>${escapeHtml(benchmark)}</h3>
          <span class="chip mono">${models.length} models</span>
        </div>
        <p class="muted">${escapeHtml(sourceMix)}</p>
        <div class="model-list">${models.map((model) => `<span>${escapeHtml(shortModel(model))}</span>`).join('')}</div>
      </article>
    `;
  }).join('');

  document.getElementById('model-universe').innerHTML = `
    <div class="universe-summary">
      <article class="summary-card"><span class="label">Observation rows</span><strong>${observations.length}</strong><span class="muted">One model score on one benchmark</span></article>
      <article class="summary-card"><span class="label">Unique models</span><strong>${allModels.length}</strong><span class="muted">Across all MVP benchmarks</span></article>
      <article class="summary-card"><span class="label">Scope warning</span><strong>MVP only</strong><span class="muted">Conclusions apply only to these included rows, not every model in market.</span></article>
    </div>
    <div class="chip-row source-row">${sourceChips}</div>
    <div class="universe-grid">${benchmarkBlocks}</div>
  `;
}

function renderSelectedBenchmark() {
  renderCurveSummary();
  renderSubstitutionCurve();
  renderObservationCards();
}

function renderAll() {
  renderThresholdButtons();
  renderHeadline();
  renderJndExplainer();
  renderMetricStrip();
  renderStatusBoard();
  renderPriceFloorChart();
  renderThresholdMatrix();
  renderBenchmarkGuide();
  renderBenchmarkSelect();
  renderModelUniverse();
  renderSelectedBenchmark();
}

renderAll();
