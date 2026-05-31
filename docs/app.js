const state = {
  threshold: 3,
  benchmark: 'MATH-500',
};

const data = window.SUBSTITUTION_BENCH_DATA;
const observations = data.observations;
const benchmarks = Object.keys(data.configs);
const thresholds = data.thresholds;

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

function renderBenchmarkSelect() {
  const select = document.getElementById('benchmark-select');
  select.innerHTML = benchmarks.map((benchmark) => `<option value="${escapeHtml(benchmark)}">${escapeHtml(benchmark)}</option>`).join('');
  select.value = state.benchmark;
  select.onchange = () => {
    state.benchmark = select.value;
    renderSelectedBenchmark();
  };
}

function renderLadderSummary() {
  const status = substitutionStatus(state.benchmark);
  const floor = status.floor;
  const frontier = status.frontier;
  const multiple = savingsMultiple(floor, frontier);
  const cards = [
    { label: 'Cheapest in band', value: floor ? dollars(floor.input_price_per_m) : 'none', copy: floor ? shortModel(floor.model) : 'No candidate' },
    { label: 'Score gap', value: floor ? points(floor.score_gap) : 'none', copy: `${state.threshold} pt band selected` },
    { label: 'Price delta', value: multiple && multiple > 1.05 ? `${multiple.toFixed(multiple >= 10 ? 0 : 1)}×` : '0×', copy: frontier ? `Frontier: ${shortModel(frontier.model)}` : 'No frontier row' },
  ];
  document.getElementById('ladder-summary').innerHTML = cards.map((card) => `
    <article class="summary-card">
      <span class="label">${escapeHtml(card.label)}</span>
      <strong>${escapeHtml(card.value)}</strong>
      <span class="muted">${escapeHtml(card.copy)}</span>
    </article>
  `).join('');
}

function renderEvidenceLadder() {
  const rows = pricedRows(state.benchmark).slice().sort((a, b) => a.input_price_per_m - b.input_price_per_m || b.score - a.score);
  const maxGap = Math.max(state.threshold * 2.2, ...rows.map((row) => row.score_gap), 1);
  const bandWidth = Math.min(100, (state.threshold / maxGap) * 100);
  const frontier = frontierRow(state.benchmark);
  const scale = (gap) => Math.min(100, Math.max(0, (gap / maxGap) * 100));

  const ladderRows = rows.map((row) => {
    const ok = equivalent(row);
    const isFrontier = row.model === frontier?.model;
    return `
      <article class="ladder-row ${ok ? 'in-band' : ''} ${isFrontier ? 'frontier' : ''}">
        <div class="model-cell">
          <strong title="${escapeHtml(row.model)}">${escapeHtml(shortModel(row.model))}</strong>
          <span>${dollars(row.input_price_per_m)} · ${pct(row.score)} score</span>
        </div>
        <div class="gap-track" aria-label="${escapeHtml(row.model)} score gap ${points(row.score_gap)}">
          <span class="gap-band" style="width: ${bandWidth}%"></span>
          <span class="gap-marker ${ok ? 'in-band' : ''} ${isFrontier ? 'frontier' : ''}" style="left: ${scale(row.score_gap)}%"></span>
        </div>
        <div class="gap-value">${points(row.score_gap)}</div>
      </article>
    `;
  }).join('');

  document.getElementById('evidence-ladder').innerHTML = `
    <div class="ladder-scale"><span>model</span><span>green zone: inside ${state.threshold} pts</span><span>gap</span></div>
    ${ladderRows}
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

function renderSelectedBenchmark() {
  renderLadderSummary();
  renderEvidenceLadder();
  renderObservationCards();
}

function renderAll() {
  renderThresholdButtons();
  renderHeadline();
  renderMetricStrip();
  renderStatusBoard();
  renderPriceFloorChart();
  renderThresholdMatrix();
  renderBenchmarkSelect();
  renderSelectedBenchmark();
}

renderAll();
