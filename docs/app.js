const data = window.SUBSTITUTION_BENCH_DATA;

const state = {
  activeIndex: data.default_index,
  threshold: data.default_threshold,
};

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function pct(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'unknown';
  return `${(Number(value) * 100).toFixed(digits)}%`;
}

function money(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'unknown';
  return `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function priceLabel(model) {
  if (model.price_state === 'unknown_zero') return 'price reported as zero — review needed';
  if (model.price_state !== 'valid') return 'price unknown';
  return `${money(model.estimated_task_cost)} / task`;
}

function activeIndex() {
  return data.indexes.find((index) => index.key === state.activeIndex) ?? data.indexes[0];
}

function modelsWithQuality(index = activeIndex()) {
  return index.models.filter((model) => model.frontier_ratio !== null && model.coverage_state === 'complete');
}

function thresholdModels(index = activeIndex()) {
  return modelsWithQuality(index).filter((model) => model.frontier_ratio >= state.threshold);
}

function heroChartLimit() {
  if (typeof window !== 'undefined' && typeof window.matchMedia === 'function' && window.matchMedia('(max-width: 820px)').matches) {
    return 30;
  }
  return 12;
}

function classifyForThreshold(model, index = activeIndex()) {
  if (model.frontier_ratio === null) return 'unknown';
  const qualityModels = modelsWithQuality(index);
  if (!qualityModels.length) return 'unknown';
  const maxRatio = Math.max(...qualityModels.map((item) => item.frontier_ratio));
  if (Math.abs(model.frontier_ratio - maxRatio) < 1e-9) return 'frontier';
  if (model.frontier_ratio < state.threshold) return 'below_cutoff';
  if (model.price_state === 'valid' && model.estimated_task_cost !== null) {
    const frontierCosts = qualityModels
      .filter((item) => Math.abs(item.frontier_ratio - maxRatio) < 1e-9 && item.estimated_task_cost !== null)
      .map((item) => item.estimated_task_cost);
    const frontierCost = frontierCosts.length ? Math.min(...frontierCosts) : null;
    if (frontierCost !== null && model.estimated_task_cost < frontierCost) return 'substitute';
  }
  return 'quality_expensive';
}

function summaryForThreshold(index = activeIndex()) {
  const completeModels = modelsWithQuality(index);
  const classified = index.models.map((model) => classifyForThreshold(model, index));
  return {
    complete: completeModels.length,
    partial: index.models.filter((model) => model.coverage_state === 'partial').length,
    unknown: index.models.filter((model) => model.coverage_state === 'unknown').length,
    qualifying: completeModels.filter((model) => model.frontier_ratio >= state.threshold).length,
    substitutes: classified.filter((item) => item === 'substitute').length,
  };
}

function stateLabel(stateName) {
  return {
    frontier: 'Frontier context',
    substitute: 'Substitute',
    quality_expensive: 'Quality yes, economics no',
    below_cutoff: 'Below cutoff',
    unknown: 'Unknown / stale coverage',
  }[stateName] ?? stateName;
}

function stateTone(stateName) {
  return {
    frontier: 'violet',
    substitute: 'green',
    quality_expensive: 'amber',
    below_cutoff: 'gray',
    unknown: 'gray',
  }[stateName] ?? 'gray';
}

function renderIndexSelector() {
  const select = document.getElementById('index-selector');
  select.innerHTML = data.indexes.map((index) => `
    <option value="${escapeHtml(index.key)}" ${index.key === state.activeIndex ? 'selected' : ''}>${escapeHtml(index.label)}</option>
  `).join('');
  select.onchange = () => {
    state.activeIndex = select.value;
    renderAll();
  };
}

function renderThresholdControl() {
  const slider = document.getElementById('threshold-slider');
  const value = document.getElementById('threshold-value');
  slider.value = String(state.threshold);
  value.textContent = pct(state.threshold, 0);
  slider.oninput = () => {
    state.threshold = Number(slider.value);
    value.textContent = pct(state.threshold, 0);
    renderAll(false);
  };
}

function renderHeadline() {
  const index = activeIndex();
  const candidates = index.models
    .map((model) => ({ ...model, live_state: classifyForThreshold(model, index) }))
    .filter((model) => model.live_state === 'substitute')
    .sort((a, b) => a.estimated_task_cost - b.estimated_task_cost);
  const best = candidates[0];
  const summary = summaryForThreshold(index);
  const complete = summary.complete;
  const qualifying = summary.qualifying;
  document.getElementById('headline-price').textContent = best ? money(best.estimated_task_cost) : 'No substitute yet';
  document.getElementById('headline-model').textContent = best
    ? `${best.model} clears ${pct(state.threshold, 0)} on ${index.label}`
    : `${index.label} is frontier-bound at ${pct(state.threshold, 0)}.`;
  document.getElementById('headline-chips').innerHTML = [
    `<span class="chip ${best ? 'green' : 'red'}">${candidates.length} substitutes</span>`,
    `<span class="chip violet">${qualifying}/${complete} qualify</span>`,
    `<span class="chip">${index.substitution_summary.partial} partial coverage</span>`,
  ].join('');
}

function renderNoSubstituteState() {
  const index = activeIndex();
  const substitutes = index.models.filter((model) => classifyForThreshold(model, index) === 'substitute');
  const callout = document.getElementById('no-substitute-state');
  callout.hidden = substitutes.length > 0;
  if (!substitutes.length) {
    callout.innerHTML = `
      <strong>No substitute yet</strong>
      <span>${escapeHtml(index.label)} has no cheaper non-frontier model above ${pct(state.threshold, 0)}. Keep the chart: frontier-bound is useful signal.</span>
    `;
  }
}

function renderIndexHeroChart() {
  const index = activeIndex();
  const complete = modelsWithQuality(index).slice(0, heroChartLimit());
  const qualifyingCount = complete.filter((model) => model.frontier_ratio >= state.threshold).length;
  const maxRatio = Math.max(...complete.map((model) => model.frontier_ratio), 1);
  const bars = complete.map((model, position) => {
    const liveState = classifyForThreshold(model, index);
    const height = Math.max(8, (model.frontier_ratio / maxRatio) * 100);
    const separator = position === qualifyingCount ? '<div class="vertical-separator" aria-label="Quality cutoff separator"></div>' : '';
    return `
      ${separator}
      <article class="index-bar-card ${stateTone(liveState)}" title="${escapeHtml(model.model)} ${pct(model.frontier_ratio)}">
        <div class="bar-shell"><div class="index-bar" style="--bar-size:${height}%; height:${height}%"></div></div>
        <strong>${escapeHtml(shortName(model.model))}</strong>
        <span class="mono">${pct(model.frontier_ratio)}</span>
        <span class="state-text">${escapeHtml(stateLabel(liveState))}</span>
      </article>
    `;
  }).join('');
  document.getElementById('index-hero-chart').innerHTML = bars || '<p class="empty">No complete resolved scores for this index yet.</p>';
}

function shortName(name) {
  return String(name)
    .replace('Claude ', '')
    .replace('Gemini ', '')
    .replace('Preview', '')
    .replace('Adaptive Reasoning, Max Effort', 'Max')
    .replace('Reasoning', 'reason')
    .trim();
}

function renderMetricStrip() {
  const index = activeIndex();
  const summary = summaryForThreshold(index);
  const complete = summary.complete;
  const qualifying = summary.qualifying;
  const conflicts = index.models.reduce((sum, model) => sum + Number(model.conflict_count || 0), 0);
  document.getElementById('metric-strip').innerHTML = [
    { label: 'Active index', value: index.label, copy: 'One selected denominator for the hero chart' },
    { label: 'Quality-qualified', value: `${qualifying}/${complete}`, copy: `At ${pct(state.threshold, 0)} of frontier` },
    { label: 'Source conflicts', value: conflicts, copy: 'Preserved observations, resolved for charting' },
  ].map((card) => `
    <article class="metric-card">
      <span class="label">${escapeHtml(card.label)}</span>
      <strong>${escapeHtml(card.value)}</strong>
      <p>${escapeHtml(card.copy)}</p>
    </article>
  `).join('');
}

function renderCostRanking() {
  const index = activeIndex();
  const candidates = index.models
    .map((model) => ({ ...model, live_state: classifyForThreshold(model, index) }))
    .filter((model) => model.live_state === 'substitute')
    .sort((a, b) => (a.estimated_task_cost ?? Number.POSITIVE_INFINITY) - (b.estimated_task_cost ?? Number.POSITIVE_INFINITY))
    .slice(0, 12);
  document.getElementById('cost-ranking').innerHTML = candidates.map((model) => `
    <article class="cost-row ${stateTone(model.live_state)}">
      <div>
        <strong>${escapeHtml(model.model)}</strong>
        <span>${pct(model.frontier_ratio)} frontier · ${escapeHtml(stateLabel(model.live_state))}</span>
      </div>
      <div class="cost-value">
        <strong>${escapeHtml(priceLabel(model))}</strong>
        <span>${escapeHtml(model.price_state)}</span>
      </div>
    </article>
  `).join('') || '<p class="empty">No quality-qualified economic candidates at this cutoff.</p>';
}

function renderComponentDrilldown() {
  const index = activeIndex();
  const topModel = index.models.find((model) => model.coverage_state === 'complete') ?? index.models[0];
  document.getElementById('component-drilldown').innerHTML = (topModel?.components ?? index.components).map((component) => `
    <article class="component-card">
      <span class="label">${escapeHtml(component.label)}</span>
      <strong>${component.frontier_ratio === null || component.frontier_ratio === undefined ? 'unknown' : pct(component.frontier_ratio)}</strong>
      <p>${escapeHtml(component.coverage_state ?? 'component')} · weight ${component.weight ?? 0.25}</p>
      <div class="mini-list">
        ${(component.benchmarks ?? []).map((benchmark) => `
          <span>${escapeHtml(benchmark.label ?? benchmark)}${benchmark.source ? ` · ${escapeHtml(benchmark.source)}` : ''}</span>
        `).join('')}
      </div>
    </article>
  `).join('');
}

function renderSourceTransparency() {
  const index = activeIndex();
  const partialExamples = index.models.filter((model) => model.coverage_state !== 'complete').slice(0, 6);
  const sources = data.source_summary.map((source) => `
    <article class="source-card">
      <strong>${escapeHtml(source.source)}</strong>
      <span>${escapeHtml(source.trust_tier)} · ${source.observations} observations · ${source.fetch_runs} fetch run(s)</span>
      <span>latest: ${escapeHtml(source.latest_fetch ?? 'unknown')}</span>
    </article>
  `).join('');
  const coverage = partialExamples.map((model) => `
    <article class="coverage-card">
      <strong>${escapeHtml(model.model)}</strong>
      <span>${escapeHtml(model.coverage_state)} coverage — saturated or unrefreshed rows stay unknown, not failed.</span>
    </article>
  `).join('');
  const conflicts = (data.conflict_examples ?? []).slice(0, 6).map((item) => `
    <article class="coverage-card conflict-card">
      <strong>${escapeHtml(item.model)} · ${escapeHtml(item.benchmark_label)}</strong>
      <span>resolved: ${escapeHtml(item.winning_source)} at ${escapeHtml(item.resolved_score)} · ${escapeHtml(item.freshness_label)}</span>
      <span>${escapeHtml(item.conflict_count)} alternate observation(s): ${(item.observations ?? []).map((obs) => `${escapeHtml(obs.source)} ${escapeHtml(obs.score)}`).join(' / ')}</span>
      <span>${escapeHtml(item.resolution_reason)}</span>
    </article>
  `).join('');
  document.getElementById('source-transparency').innerHTML = `
    <div class="transparency-grid">
      <section>
        <h3>Cache freshness</h3>
        <p>${escapeHtml(data.cache_freshness.policy)}</p>
        <p class="mono">latest fetch: ${escapeHtml(data.cache_freshness.latest_fetch ?? 'unknown')}</p>
      </section>
      <section>
        <h3>Source mix</h3>
        <div class="stack">${sources}</div>
      </section>
      <section>
        <h3>Resolved conflicts</h3>
        <div class="stack">${conflicts || '<p class="empty">No source conflicts in this generated payload.</p>'}</div>
      </section>
      <section>
        <h3>Missing / stale coverage</h3>
        <div class="stack">${coverage || '<p class="empty">No partial coverage examples in this selected index.</p>'}</div>
      </section>
    </div>
  `;
}

function renderAll(resetControls = true) {
  if (resetControls) {
    renderIndexSelector();
    renderThresholdControl();
  }
  renderHeadline();
  renderNoSubstituteState();
  renderIndexHeroChart();
  renderMetricStrip();
  renderCostRanking();
  renderComponentDrilldown();
  renderSourceTransparency();
}

if (typeof window !== 'undefined') {
  window.__SUBSTITUTION_BENCH_TEST__ = {
    activeIndex,
    classifyForThreshold,
    renderHeadline,
    renderMetricStrip,
    state,
    summaryForThreshold,
  };
}

renderAll();
