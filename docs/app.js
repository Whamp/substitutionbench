const state = {
  threshold: 3,
  benchmark: 'MATH-500',
};

const data = window.SUBSTITUTION_BENCH_DATA;
const observations = data.observations;
const benchmarks = Object.keys(data.configs);

function dollars(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 4 })}/M`;
}

function pct(value, digits = 1) {
  return `${Number(value).toFixed(digits)}%`;
}

function params(row) {
  const p = row.active_params_b ?? row.total_params_b;
  return p ? `${p}B${row.active_params_b ? ' active' : ''}` : 'unknown size';
}

function rowsForBenchmark(benchmark) {
  return observations.filter((row) => row.benchmark === benchmark);
}

function equivalent(row, threshold = state.threshold) {
  return row.frontier_score - row.score <= threshold;
}

function cheapestEquivalent(benchmark, threshold = state.threshold) {
  return rowsForBenchmark(benchmark)
    .filter((row) => equivalent(row, threshold) && row.input_price_per_m !== null)
    .sort((a, b) => a.input_price_per_m - b.input_price_per_m)[0] ?? null;
}

function smallestEquivalent(benchmark, threshold = state.threshold) {
  return rowsForBenchmark(benchmark)
    .filter((row) => equivalent(row, threshold) && (row.active_params_b ?? row.total_params_b) !== null)
    .sort((a, b) => (a.active_params_b ?? a.total_params_b) - (b.active_params_b ?? b.total_params_b))[0] ?? null;
}

function svg(width, height, body) {
  return `<svg viewBox="0 0 ${width} ${height}" role="presentation" preserveAspectRatio="xMidYMid meet">${body}</svg>`;
}

function scale(value, inMin, inMax, outMin, outMax) {
  if (inMax === inMin) return (outMin + outMax) / 2;
  return outMin + ((value - inMin) / (inMax - inMin)) * (outMax - outMin);
}

function isSaturatedKind(kind) {
  return kind === 'saturated' || kind === 'near_saturated';
}

function renderKpis() {
  const saturated = benchmarks.filter((b) => isSaturatedKind(data.configs[b].benchmark_kind)).length;
  const floors = benchmarks.map((b) => cheapestEquivalent(b)).filter(Boolean);
  const cheapest = floors.slice().sort((a, b) => a.input_price_per_m - b.input_price_per_m)[0];
  const kpis = [
    { label: 'Benchmarks', value: benchmarks.length, copy: `${saturated} saturated / near-saturated anchors` },
    { label: 'Default JND band', value: `${state.threshold} pts`, copy: 'Configurable in the page controls' },
    { label: 'Cheapest current floor', value: cheapest ? dollars(cheapest.input_price_per_m) : '—', copy: cheapest ? `${cheapest.model} on ${cheapest.benchmark}` : 'No priced floor found' },
  ];
  document.getElementById('kpis').innerHTML = kpis.map((item) => `
    <article class="kpi"><span>${item.label}</span><strong>${item.value}</strong><p>${item.copy}</p></article>
  `).join('');
}

function renderHeadline() {
  const math = cheapestEquivalent('MATH-500');
  const gpqa5 = cheapestEquivalent('GPQA Diamond', 5);
  document.getElementById('headline-floor').textContent = math ? `${math.model} @ ${dollars(math.input_price_per_m)}` : 'No floor yet';
  document.getElementById('headline-copy').textContent = gpqa5
    ? `MATH-500 is saturated at 3 pts; GPQA admits ${gpqa5.model} by 5 pts. SWE-bench does not yet substitute.`
    : 'The useful signal is the cheapest model still inside the saturated capability band.';
}

function renderFloorChart() {
  const width = 920, height = 280;
  const left = 170, right = 220, top = 36, rowH = 62;
  const bars = benchmarks.map((benchmark, index) => {
    const row = cheapestEquivalent(benchmark);
    const y = top + index * rowH;
    const coverage = row ? row.frontier_coverage : 0;
    const w = scale(coverage, 0, 100, 0, width - left - right);
    const fill = row ? '#10b981' : '#62666d';
    const label = row ? `${row.model} · ${dollars(row.input_price_per_m)} · ${pct(row.frontier_coverage)}` : 'No equivalent priced model';
    return `
      <text x="18" y="${y + 26}" class="svg-title">${benchmark}</text>
      <rect x="${left}" y="${y}" width="${w}" height="34" rx="8" fill="${fill}" opacity="0.9"></rect>
      <text x="${left + w + 12}" y="${y + 22}" class="tick-label">${label}</text>
    `;
  }).join('');
  document.getElementById('floor-chart').innerHTML = svg(width, height, `
    <line x1="${left}" y1="${height - 32}" x2="${width - right}" y2="${height - 32}" class="axis"></line>
    ${bars}
    <text x="${left}" y="${height - 10}" class="tick-label">bar length = frontier coverage at selected JND floor</text>
  `);
}

function renderFloorCards() {
  document.getElementById('floor-cards').innerHTML = benchmarks.map((benchmark) => {
    const cheap = cheapestEquivalent(benchmark);
    const small = smallestEquivalent(benchmark);
    const cfg = data.configs[benchmark];
    const saturated = isSaturatedKind(cfg.benchmark_kind);
    return `
      <article class="floor-card">
        <h3>${benchmark}</h3>
        <strong>${cheap ? cheap.model : 'No substitute yet'}</strong>
        <p>${cheap ? `${pct(cheap.frontier_coverage)} frontier coverage at ${dollars(cheap.input_price_per_m)} input.` : 'Only frontier is inside the current band.'}</p>
        <p>${small ? `Smallest known equivalent: ${small.model} (${params(small)}).` : 'No parameter-sized equivalent in current rows.'}</p>
        <span class="badge ${saturated ? 'green' : 'red'}">${saturated ? 'saturation signal' : 'frontier still matters'}</span>
      </article>
    `;
  }).join('');
}

function renderCurve() {
  const benchmark = state.benchmark;
  const rows = rowsForBenchmark(benchmark).filter((row) => row.input_price_per_m !== null).sort((a, b) => a.input_price_per_m - b.input_price_per_m);
  const width = 920, height = 430;
  const left = 70, right = 30, top = 28, bottom = 58;
  const maxPrice = Math.max(...rows.map((row) => row.input_price_per_m));
  const minPrice = Math.min(...rows.map((row) => row.input_price_per_m));
  const minCoverage = Math.max(0, Math.min(...rows.map((row) => row.frontier_coverage)) - 5);
  const bandMin = ((rows[0].frontier_score - state.threshold) / rows[0].frontier_score) * 100;
  const yBand = scale(bandMin, minCoverage, 101, height - bottom, top);
  const points = rows.map((row) => {
    const x = scale(row.input_price_per_m, minPrice, maxPrice, left, width - right);
    const y = scale(row.frontier_coverage, minCoverage, 101, height - bottom, top);
    const ok = equivalent(row);
    const label = `${row.model}: ${row.score}% score, ${pct(row.frontier_coverage)} coverage, ${dollars(row.input_price_per_m)} input`;
    return { row, x, y, ok, label };
  });
  const path = points.map((p) => `${p.x},${p.y}`).join(' ');
  const cheap = cheapestEquivalent(benchmark);
  const circles = points.map((p) => `
    <circle cx="${p.x}" cy="${p.y}" r="6" fill="${p.ok ? '#10b981' : '#f87171'}" stroke="rgba(255,255,255,.7)" stroke-width="1">
      <title>${p.label}</title>
    </circle>
  `).join('');
  const labels = points
    .filter((p) => p.row.model === cheap?.model || p.row.input_price_per_m === maxPrice || p.row.frontier_coverage < bandMin - 8)
    .map((p) => `<text x="${p.x}" y="${p.y - 11}" text-anchor="middle" class="tick-label">${p.row.model.slice(0, 22)}</text>`)
    .join('');
  document.getElementById('curve-chart').innerHTML = svg(width, height, `
    <rect x="${left}" y="${top}" width="${width - left - right}" height="${yBand - top}" fill="rgba(16,185,129,.13)"></rect>
    <line x1="${left}" y1="${yBand}" x2="${width - right}" y2="${yBand}" stroke="rgba(16,185,129,.75)" stroke-dasharray="6 6"></line>
    <line x1="${left}" y1="${height - bottom}" x2="${width - right}" y2="${height - bottom}" class="axis"></line>
    <line x1="${left}" y1="${top}" x2="${left}" y2="${height - bottom}" class="axis"></line>
    <polyline points="${path}" fill="none" stroke="#7170ff" stroke-width="2"></polyline>
    ${circles}
    ${labels}
    <text x="${left}" y="18" class="svg-title">${benchmark}: green points are within ${state.threshold} pts</text>
    <text x="${left}" y="${height - 20}" class="tick-label">Input price, cheapest → expensive</text>
    <text x="18" y="${height / 2}" transform="rotate(-90 18 ${height / 2})" class="tick-label">Frontier coverage</text>
  `);
}

function renderRows() {
  const sorted = observations.slice().sort((a, b) => a.benchmark.localeCompare(b.benchmark) || b.frontier_coverage - a.frontier_coverage);
  document.getElementById('rows').innerHTML = sorted.map((row) => `
    <tr>
      <td>${row.model}</td>
      <td>${row.benchmark}</td>
      <td>${pct(row.score)}</td>
      <td>${pct(row.frontier_coverage)}</td>
      <td>${dollars(row.input_price_per_m)}</td>
      <td>${row.eval_mode}</td>
      <td><a href="${row.source_url}">${row.source_quality}</a></td>
    </tr>
  `).join('');
}

function wireControls() {
  document.querySelectorAll('.threshold').forEach((button) => {
    button.addEventListener('click', () => {
      state.threshold = Number(button.dataset.threshold);
      document.querySelectorAll('.threshold').forEach((b) => b.classList.toggle('active', b === button));
      renderAll();
    });
  });
  const select = document.getElementById('benchmark-select');
  select.innerHTML = benchmarks.map((b) => `<option value="${b}">${b}</option>`).join('');
  select.value = state.benchmark;
  select.addEventListener('change', () => {
    state.benchmark = select.value;
    renderCurve();
  });
}

function renderAll() {
  renderKpis();
  renderHeadline();
  renderFloorChart();
  renderFloorCards();
  renderCurve();
  renderRows();
}

wireControls();
renderAll();
