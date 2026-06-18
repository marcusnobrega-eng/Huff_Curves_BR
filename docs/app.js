const Q_COLORS = {
  1: '#e84d4f',
  2: '#f4b63f',
  3: '#2cb7b0',
  4: '#7c5cff',
  none: '#7f8a91',
};

const state = {
  manifest: null,
  analytics: null,
  stations: [],
  filtered: [],
  selected: null,
  selectedCurves: null,
  activeStormQuartile: null,
  markers: null,
  markerByStation: {},
  charts: {},
  curveCache: {},
};

const map = L.map('map', {
  preferCanvas: true,
  zoomControl: true,
}).setView([-14.5, -52.5], 4);

L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
  attribution: 'CARTO',
  maxZoom: 18,
}).addTo(map);

function byId(id) {
  return document.getElementById(id);
}

function setText(id, value) {
  const node = byId(id);
  if (node) node.textContent = value;
}

function numberValue(value) {
  if (value === null || value === undefined || value === '') return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function fmt(value, digits = 0) {
  const number = numberValue(value);
  if (number === null) return '-';
  return number.toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0,
  });
}

function fmtFixed(value, digits = 2) {
  const number = numberValue(value);
  if (number === null) return '-';
  return number.toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

function fmtPercentFraction(value, digits = 0) {
  const number = numberValue(value);
  if (number === null) return '-';
  return `${fmt(number * 100, digits)}%`;
}

function fmtPercentValue(value, digits = 0) {
  const number = numberValue(value);
  if (number === null) return '-';
  return `${fmt(number, digits)}%`;
}

function quartileLabel(value) {
  const q = numberValue(value);
  return q ? `Q${q}` : '-';
}

function qColor(value) {
  const q = numberValue(value);
  return Q_COLORS[q] || Q_COLORS.none;
}

function statusLabel(status) {
  return status ? String(status).replace(/_/g, ' ') : '-';
}

function stationPlace(station) {
  return [station.municipality_name, station.state_abbrev, station.biome_name].filter(Boolean).join(' · ') || '-';
}

function stationSearchText(station) {
  return [
    station.station_id,
    station.municipality_name,
    station.state_abbrev,
    station.state_name,
    station.region_name,
    station.biome_name,
    station.status,
  ].filter(Boolean).join(' ').toLowerCase();
}

function markerRadius(station) {
  const events = numberValue(station.n_events) || 0;
  return Math.max(4, Math.min(14, 4 + Math.sqrt(events) / 6));
}

function chartTextColor() {
  return getComputedStyle(document.documentElement).getPropertyValue('--muted').trim() || '#aab3b7';
}

function chartGridColor() {
  return 'rgba(255,255,255,0.08)';
}

function destroyChart(id) {
  if (state.charts[id]) {
    state.charts[id].destroy();
    delete state.charts[id];
  }
}

function makeChart(id, config) {
  destroyChart(id);
  const node = byId(id);
  if (!node) return null;
  node.style.width = '100%';
  state.charts[id] = new Chart(node, config);
  return state.charts[id];
}

function baseChartOptions(extra = {}) {
  return Object.assign({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: chartTextColor(),
          boxWidth: 12,
          boxHeight: 12,
        },
      },
      tooltip: {
        intersect: false,
        mode: 'nearest',
      },
    },
    scales: {
      x: {
        ticks: { color: chartTextColor(), maxTicksLimit: 8 },
        grid: { color: chartGridColor() },
      },
      y: {
        ticks: { color: chartTextColor() },
        grid: { color: chartGridColor() },
      },
    },
  }, extra);
}

function populateFilters() {
  const statusFilter = byId('statusFilter');
  const stateFilter = byId('stateFilter');
  const biomeFilter = byId('biomeFilter');

  const statuses = Array.from(new Set(state.stations.map((s) => s.status).filter(Boolean))).sort();
  statuses.forEach((status) => {
    const option = document.createElement('option');
    option.value = status;
    option.textContent = statusLabel(status);
    statusFilter.appendChild(option);
  });

  const states = Array.from(new Set(state.stations.map((s) => s.state_abbrev).filter(Boolean))).sort();
  states.forEach((uf) => {
    const option = document.createElement('option');
    option.value = uf;
    option.textContent = uf;
    stateFilter.appendChild(option);
  });

  const biomes = Array.from(new Set(state.stations.map((s) => s.biome_name).filter(Boolean))).sort();
  biomes.forEach((biome) => {
    const option = document.createElement('option');
    option.value = biome;
    option.textContent = biome;
    biomeFilter.appendChild(option);
  });
}

function renderGlobalStats() {
  const totals = state.analytics.totals || {};
  setText('totalStations', fmt(totals.stations));
  setText('okStations', fmt(totals.ok_stations));
  setText('totalEvents', fmt(totals.events));
  setText('medianYears', fmtFixed(totals.median_years_span, 1));
  setText('medianKge', fmtFixed(totals.median_kge_mean, 3));
  setText('medianMissing', fmtPercentFraction(totals.median_missing_fraction, 1));
  setText('assetStamp', state.manifest.generated_at ? state.manifest.generated_at.slice(0, 10) : '-');
}

function renderLegend() {
  const legend = byId('legendItems');
  legend.innerHTML = '';
  const note = document.createElement('div');
  note.className = 'legend-note';
  note.textContent = 'Color shows dominant quartile. Dot size increases with the number of valid rainfall events.';
  legend.appendChild(note);

  const colorTitle = document.createElement('div');
  colorTitle.className = 'legend-subtitle';
  colorTitle.textContent = 'Color: dominant Huff quartile';
  legend.appendChild(colorTitle);

  [
    ['1', '1st quartile (early peak)'],
    ['2', '2nd quartile'],
    ['3', '3rd quartile'],
    ['4', '4th quartile (late peak)'],
    ['none', 'No dominant quartile'],
  ].forEach(([key, label]) => {
    const item = document.createElement('div');
    item.className = 'legend-item';
    item.innerHTML = `<span><span class="legend-swatch" style="background:${Q_COLORS[key]}"></span> ${label}</span><strong>${key === 'none' ? '-' : key}</strong>`;
    legend.appendChild(item);
  });

  const size = document.createElement('div');
  size.className = 'size-legend';
  size.innerHTML = `
    <span class="size-title">Dot size: event count</span>
    <div class="size-row">
      <span><i class="dot small"></i> low</span>
      <span><i class="dot medium"></i> medium</span>
      <span><i class="dot large"></i> high</span>
    </div>
  `;
  legend.appendChild(size);
}

function stationPassesFilters(station) {
  const query = byId('stationSearch').value.trim().toLowerCase();
  const status = byId('statusFilter').value;
  const quartile = byId('quartileFilter').value;
  const stateFilter = byId('stateFilter').value;
  const biome = byId('biomeFilter').value;
  const minEvents = numberValue(byId('minEventsFilter').value) || 0;
  const minYears = numberValue(byId('minYearsFilter').value) || 0;

  if (query && stationSearchText(station).indexOf(query) < 0) return false;
  if (status !== 'all' && station.status !== status) return false;
  if (quartile !== 'all' && String(station.dominant_quartile || '') !== quartile) return false;
  if (stateFilter !== 'all' && station.state_abbrev !== stateFilter) return false;
  if (biome !== 'all' && station.biome_name !== biome) return false;
  if ((numberValue(station.n_events) || 0) < minEvents) return false;
  if ((numberValue(station.years_span) || 0) < minYears) return false;
  return true;
}

function applyFilters() {
  state.filtered = state.stations.filter(stationPassesFilters);
  renderStationList();
  renderMarkers();
  setText('visibleCount', `${fmt(state.filtered.length)} visible`);
}

function renderStationList() {
  const list = byId('stationList');
  list.innerHTML = '';
  const sorted = state.filtered.slice().sort((a, b) => {
    const aOk = a.status === 'ok' ? 1 : 0;
    const bOk = b.status === 'ok' ? 1 : 0;
    if (aOk !== bOk) return bOk - aOk;
    return (numberValue(b.n_events) || 0) - (numberValue(a.n_events) || 0);
  });

  sorted.slice(0, 320).forEach((station) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `station-item ${state.selected && state.selected.station_id === station.station_id ? 'active' : ''}`;
    button.style.borderLeftColor = qColor(station.dominant_quartile);
    button.innerHTML = `
      <strong>Station ${station.station_id}</strong>
      <span>${stationPlace(station)}</span>
      <div class="pill-row">
        <span class="pill">${statusLabel(station.status)}</span>
        <span class="pill">${quartileLabel(station.dominant_quartile)}</span>
        <span class="pill">${fmt(station.n_events)} events</span>
        <span class="pill">${fmtFixed(station.years_span, 1)} yr</span>
      </div>
    `;
    button.addEventListener('click', () => selectStation(station.station_id, true));
    list.appendChild(button);
  });

  if (sorted.length > 320) {
    const note = document.createElement('div');
    note.className = 'empty-state';
    note.textContent = `Showing 320 of ${fmt(sorted.length)} filtered stations.`;
    list.appendChild(note);
  }

  if (!sorted.length) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.textContent = 'No stations match the filters.';
    list.appendChild(empty);
  }
}

function renderMarkers() {
  if (!state.markers) {
    state.markers = L.layerGroup().addTo(map);
  }
  state.markers.clearLayers();
  state.markerByStation = {};

  state.filtered.forEach((station) => {
    const lat = numberValue(station.lat);
    const lon = numberValue(station.lon);
    if (lat === null || lon === null) return;
    const marker = L.circleMarker([lat, lon], {
      radius: markerRadius(station),
      color: '#101214',
      weight: 1.2,
      opacity: 0.9,
      fillColor: qColor(station.dominant_quartile),
      fillOpacity: station.status === 'ok' ? 0.82 : 0.38,
    });
    marker.bindTooltip(`Station ${station.station_id}<br>${stationPlace(station)}<br>${quartileLabel(station.dominant_quartile)} · ${fmt(station.n_events)} events`);
    marker.on('click', () => selectStation(station.station_id, false));
    marker.addTo(state.markers);
    state.markerByStation[station.station_id] = marker;
  });
}

function fitFiltered() {
  const latLngs = state.filtered
    .map((station) => [numberValue(station.lat), numberValue(station.lon)])
    .filter(([lat, lon]) => lat !== null && lon !== null);
  if (!latLngs.length) return;
  map.fitBounds(latLngs, { padding: [28, 28], maxZoom: 9 });
}

function renderSelectedCard(station) {
  setText('selectedStatus', statusLabel(station.status));
  setText('selectedTitle', `Station ${station.station_id}`);
  setText('selectedSubtitle', stationPlace(station));
  setText('selectedQuartile', quartileLabel(station.dominant_quartile));
  setText('selectedEvents', fmt(station.n_events));
  const maes = [1, 2, 3, 4].map((q) => (station.quartiles?.[String(q)] || {}).mae).filter((v) => v != null);
  const mae_mean = maes.length ? maes.reduce((a, b) => a + b, 0) / maes.length : null;
  setText('selectedKge', fmtFixed(mae_mean, 3));
}

function metadataItems(station) {
  return [
    ['Station ID', station.station_id],
    ['Municipality', station.municipality_name],
    ['State', station.state_name || station.state_abbrev],
    ['Region', station.region_name],
    ['Biome', station.biome_name],
    ['Status', statusLabel(station.status)],
    ['Reason', station.status_reason],
    ['Record span', `${station.first_timestamp || '-'} to ${station.last_timestamp || '-'}`],
    ['Years used', fmtFixed(station.years_span, 2)],
    ['Observations', fmt(station.n_observations)],
    ['Missing', fmtPercentFraction(station.missing_fraction, 1)],
    ['Timestep', `${fmt(station.dt_min)} min`],
    ['Max daily rain', `${fmtFixed(station.max_daily_mm, 1)} mm`],
    ['Median event volume', `${fmtFixed(station.event_volume_median_mm, 1)} mm`],
    ['P90 event duration', `${fmtFixed(station.event_duration_p90_h, 1)} h`],
    ['P95 peak intensity', `${fmtFixed(station.event_peak_intensity_p95_mm_h, 1)} mm/h`],
  ];
}

function renderMetadata(station) {
  const grid = byId('metadataGrid');
  grid.innerHTML = '';
  metadataItems(station).forEach(([label, value]) => {
    const item = document.createElement('div');
    item.innerHTML = `<dt>${label}</dt><dd title="${value || '-'}">${value || '-'}</dd>`;
    grid.appendChild(item);
  });
}

function renderQuartileTable(station) {
  const body = byId('quartileTable');
  body.innerHTML = '';
  for (let q = 1; q <= 4; q += 1) {
    const rec = station.quartiles[String(q)] || {};
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="pill" style="border-color:${Q_COLORS[q]};">${quartileLabel(q)}</span></td>
      <td>${fmt(rec.n_events)} (${fmtPercentValue(rec.percent_events, 1)})</td>
      <td>${fmtFixed(rec.avg_volume_mm, 1)} mm</td>
      <td>${fmtFixed(rec.avg_duration_h, 1)} h</td>
      <td>${fmtFixed(rec.max_intensity_mm_h, 1)} mm/h</td>
      <td>${fmtFixed(rec.mae, 3)}</td>
    `;
    body.appendChild(tr);
  }
}

function renderCoefficientTable(station) {
  const body = byId('coefficientTable');
  body.innerHTML = '';
  for (let q = 1; q <= 4; q += 1) {
    const rec = station.quartiles[String(q)] || {};
    const coeffs = rec.coefficients || [];
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${quartileLabel(q)}</td>${coeffs.map((v) => `<td>${fmtFixed(v, 5)}</td>`).join('')}`;
    body.appendChild(tr);
  }
}

function renderEventBreakdown(station) {
  const counts = [1, 2, 3, 4].map((q) => numberValue((station.quartiles[String(q)] || {}).n_events) || 0);
  const total = counts.reduce((acc, value) => acc + value, 0);
  setText('quartileSummary', `${fmt(total)} events`);
  makeChart('eventBreakdownChart', {
    type: 'doughnut',
    data: {
      labels: ['Q1', 'Q2', 'Q3', 'Q4'],
      datasets: [{
        data: counts,
        backgroundColor: [Q_COLORS[1], Q_COLORS[2], Q_COLORS[3], Q_COLORS[4]],
        borderColor: '#15181b',
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: chartTextColor(), boxWidth: 12 } },
      },
    },
  });
}

async function fetchCurves(station) {
  state.selectedCurves = null;
  if (!station.curve_path) return null;
  if (state.curveCache[station.station_id]) return state.curveCache[station.station_id];
  if (window.HUFF_BOOTSTRAP && window.HUFF_BOOTSTRAP.curves && window.HUFF_BOOTSTRAP.curves[station.station_id]) {
    const embeddedCurves = window.HUFF_BOOTSTRAP.curves[station.station_id];
    state.curveCache[station.station_id] = embeddedCurves;
    return embeddedCurves;
  }
  const response = await fetch(station.curve_path);
  if (!response.ok) throw new Error(`Could not load ${station.curve_path}`);
  const curves = await response.json();
  state.curveCache[station.station_id] = curves;
  return curves;
}

function datasetsForCurves(curves, activeQuartile) {
  const datasets = [];
  for (let q = 1; q <= 4; q += 1) {
    const rec = curves.quartiles[String(q)];
    if (!rec || !rec.tau || !rec.median) continue;
    const data = rec.tau.map((tau, idx) => ({ x: tau, y: rec.median[idx] }));
    datasets.push({
      label: `Q${q} median`,
      data,
      borderColor: Q_COLORS[q],
      backgroundColor: Q_COLORS[q],
      borderWidth: q === activeQuartile ? 3 : 2,
      pointRadius: 0,
      tension: 0,
      spanGaps: true,
    });
  }

  const active = curves.quartiles[String(activeQuartile)];
  if (active && active.p10 && active.p90) {
    datasets.push({
      label: `Q${activeQuartile} p10`,
      data: active.tau.map((tau, idx) => ({ x: tau, y: active.p10[idx] })),
      borderColor: Q_COLORS[activeQuartile],
      borderDash: [5, 5],
      borderWidth: 1,
      pointRadius: 0,
      tension: 0,
      spanGaps: true,
    });
    datasets.push({
      label: `Q${activeQuartile} p90`,
      data: active.tau.map((tau, idx) => ({ x: tau, y: active.p90[idx] })),
      borderColor: Q_COLORS[activeQuartile],
      borderDash: [2, 5],
      borderWidth: 1,
      pointRadius: 0,
      tension: 0,
      spanGaps: true,
    });
  }
  return datasets;
}

function renderCurveChart(curves) {
  const active = state.activeStormQuartile || state.selected.dominant_quartile || 1;
  const datasets = curves ? datasetsForCurves(curves, Number(active)) : [];
  setText('curveStatus', datasets.length ? 'median, p10, p90' : 'no curve');
  makeChart('curveChart', {
    type: 'line',
    data: { datasets },
    options: baseChartOptions({
      parsing: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: chartTextColor(), boxWidth: 12 } },
        tooltip: { intersect: false, mode: 'nearest' },
      },
      scales: {
        x: {
          type: 'linear',
          min: 0,
          max: 1,
          title: { display: true, text: 'Normalized time', color: chartTextColor() },
          ticks: { color: chartTextColor(), maxTicksLimit: 6 },
          grid: { color: chartGridColor() },
        },
        y: {
          min: 0,
          max: 1,
          title: { display: true, text: 'Cumulative rainfall fraction', color: chartTextColor() },
          ticks: { color: chartTextColor() },
          grid: { color: chartGridColor() },
        },
      },
    }),
  });
}

function availableQuartiles(curves) {
  if (!curves) return [];
  return [1, 2, 3, 4].filter((q) => {
    const rec = curves.quartiles[String(q)];
    return rec && rec.median && rec.median.some((value) => numberValue(value) !== null);
  });
}

function setDefaultStormQuartile(station, curves) {
  const available = availableQuartiles(curves);
  const dominant = Number(station.dominant_quartile);
  if (available.indexOf(dominant) >= 0) {
    state.activeStormQuartile = dominant;
  } else {
    state.activeStormQuartile = available[0] || dominant || 1;
  }
}

function renderStormQuartileButtons(curves) {
  const wrap = byId('stormQuartileButtons');
  wrap.innerHTML = '';
  const available = availableQuartiles(curves);
  for (let q = 1; q <= 4; q += 1) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = `Q${q}`;
    button.disabled = available.indexOf(q) < 0;
    button.className = state.activeStormQuartile === q ? 'active' : '';
    if (state.activeStormQuartile === q) {
      button.style.background = Q_COLORS[q];
    }
    button.addEventListener('click', () => {
      state.activeStormQuartile = q;
      renderStormQuartileButtons(state.selectedCurves);
      renderCurveChart(state.selectedCurves);
      renderStormChart();
    });
    wrap.appendChild(button);
  }
}

function interpolateCurve(tauValues, curveValues, targetTau) {
  if (targetTau <= 0) return 0;
  if (targetTau >= 1) return 1;

  let previousTau = 0;
  let previousValue = 0;
  for (let i = 0; i < tauValues.length; i += 1) {
    const tau = numberValue(tauValues[i]);
    const value = numberValue(curveValues[i]);
    if (tau === null || value === null) continue;
    if (tau < targetTau) {
      previousTau = tau;
      previousValue = value;
      continue;
    }
    if (tau === targetTau || tau <= previousTau) return value;
    const weight = (targetTau - previousTau) / (tau - previousTau);
    return previousValue + weight * (value - previousValue);
  }
  return previousValue;
}

function stormRowsForQuartile(quartile) {
  const curves = state.selectedCurves;
  if (!curves || !quartile) return null;
  const rec = curves.quartiles[String(quartile)];
  if (!rec || !rec.tau || !rec.median) return null;

  const duration = Math.max(0.01, numberValue(byId('stormDuration').value) || 24);
  const volume = Math.max(0, numberValue(byId('stormVolume').value) || 100);
  const timestepMinutes = Math.max(1, numberValue(byId('stormTimestep').value) || 10);
  const timestepHours = timestepMinutes / 60;
  const nIntervals = Math.max(1, Math.ceil(duration / timestepHours));
  const rows = [];
  let previous = 0;
  for (let i = 1; i <= nIntervals; i += 1) {
    const hourStart = Math.min((i - 1) * timestepHours, duration);
    const hourEnd = Math.min(i * timestepHours, duration);
    const t0 = hourStart / duration;
    const t1 = hourEnd / duration;
    const c1 = interpolateCurve(rec.tau, rec.median, t1);
    if (t1 <= t0) continue;
    const fraction = Math.max(0, c1 - previous);
    const depth = fraction * volume;
    const intervalHours = hourEnd - hourStart;
    const intensity = intervalHours > 0 ? depth / intervalHours : 0;
    rows.push({
      timestep_min: timestepMinutes,
      tau_start: t0,
      tau_end: t1,
      hour_start: hourStart,
      hour_end: hourEnd,
      midpoint: (t0 + t1) / 2,
      depth_mm: depth,
      intensity_mm_h: intensity,
      cumulative_mm: c1 * volume,
    });
    previous = Math.max(previous, c1);
  }
  return rows;
}

function stormSeries() {
  return stormRowsForQuartile(state.activeStormQuartile);
}

function allStormRows() {
  const curves = state.selectedCurves;
  if (!curves) return [];
  const rows = [];
  availableQuartiles(curves).forEach((quartile) => {
    const qRows = stormRowsForQuartile(quartile) || [];
    qRows.forEach((row, index) => {
      rows.push(Object.assign({ quartile, interval: index + 1 }, row));
    });
  });
  return rows;
}

function renderStormChart() {
  const curves = state.selectedCurves;
  const quartiles = availableQuartiles(curves);
  const activeRows = stormSeries();
  if (!curves || !quartiles.length || !activeRows || !activeRows.length) {
    setText('stormPeak', 'no curve');
    makeChart('stormChart', { type: 'line', data: { datasets: [] }, options: baseChartOptions() });
    return;
  }

  const activePeak = activeRows.reduce((acc, row) => Math.max(acc, row.intensity_mm_h), 0);
  const allPeaks = quartiles.map((quartile) => {
    const qRows = stormRowsForQuartile(quartile) || [];
    return qRows.reduce((acc, row) => Math.max(acc, row.intensity_mm_h), 0);
  });
  const globalPeak = allPeaks.reduce((acc, value) => Math.max(acc, value), 0);
  setText('stormPeak', `Q${state.activeStormQuartile} ${fmtFixed(activePeak, 1)} mm/h · max ${fmtFixed(globalPeak, 1)} mm/h`);

  const intensityDatasets = quartiles.map((quartile) => {
    const qRows = stormRowsForQuartile(quartile) || [];
    return {
      type: 'line',
      label: `Q${quartile} intensity`,
      data: qRows.map((row) => ({ x: row.hour_end, y: row.intensity_mm_h })),
      borderColor: Q_COLORS[quartile],
      backgroundColor: Q_COLORS[quartile],
      borderWidth: quartile === state.activeStormQuartile ? 3 : 1.8,
      pointRadius: 0,
      stepped: 'after',
      tension: 0,
      yAxisID: 'y',
    };
  });

  makeChart('stormChart', {
    type: 'line',
    data: {
      datasets: [
        ...intensityDatasets,
        {
          type: 'line',
          label: `Q${state.activeStormQuartile} cumulative`,
          data: activeRows.map((row) => ({ x: row.hour_end, y: row.cumulative_mm })),
          borderColor: '#f2f4f2',
          backgroundColor: '#f2f4f2',
          borderWidth: 2,
          pointRadius: 0,
          yAxisID: 'y1',
        },
      ],
    },
    options: baseChartOptions({
      parsing: false,
      interaction: { intersect: false, mode: 'nearest' },
      plugins: {
        legend: { position: 'bottom', labels: { color: chartTextColor(), boxWidth: 12 } },
        tooltip: {
          callbacks: {
            label: (context) => {
              const value = context.parsed.y;
              return context.dataset.yAxisID === 'y1'
                ? `Cumulative: ${fmtFixed(value, 1)} mm`
                : `Intensity: ${fmtFixed(value, 1)} mm/h`;
            },
          },
        },
      },
      scales: {
        x: {
          type: 'linear',
          min: 0,
          title: { display: true, text: 'Storm time (h)', color: chartTextColor() },
          ticks: { color: chartTextColor(), maxTicksLimit: 7 },
          grid: { color: chartGridColor() },
        },
        y: {
          beginAtZero: true,
          suggestedMax: globalPeak * 1.08,
          title: { display: true, text: 'Intensity (mm/h)', color: chartTextColor() },
          ticks: { color: chartTextColor() },
          grid: { color: chartGridColor() },
        },
        y1: {
          beginAtZero: true,
          position: 'right',
          title: { display: true, text: 'Cumulative depth (mm)', color: chartTextColor() },
          ticks: { color: chartTextColor() },
          grid: { drawOnChartArea: false },
        },
      },
    }),
  });
}

function stormCsvText(rows) {
  const header = [
    'station_id',
    'quartile',
    'interval',
    'timestep_min',
    'tau_start',
    'tau_end',
    'hour_start',
    'hour_end',
    'depth_mm',
    'intensity_mm_h',
    'cumulative_mm',
  ];
  const lines = [header.join(',')];
  rows.forEach((row, index) => {
    lines.push([
      state.selected.station_id,
      row.quartile || state.activeStormQuartile,
      row.interval || index + 1,
      row.timestep_min,
      row.tau_start.toFixed(4),
      row.tau_end.toFixed(4),
      row.hour_start.toFixed(4),
      row.hour_end.toFixed(4),
      row.depth_mm.toFixed(5),
      row.intensity_mm_h.toFixed(5),
      row.cumulative_mm.toFixed(5),
    ].join(','));
  });
  return lines.join('\n');
}

function downloadStormCsv() {
  const rows = (stormSeries() || []).map((row, index) => Object.assign({
    quartile: state.activeStormQuartile,
    interval: index + 1,
  }, row));
  if (!rows.length || !state.selected) return;
  downloadText(stormCsvText(rows), `station_${state.selected.station_id}_q${state.activeStormQuartile}_hyetograph.csv`, 'text/csv');
}

function downloadAllStormCsv() {
  const rows = allStormRows();
  if (!rows.length || !state.selected) return;
  downloadText(stormCsvText(rows), `station_${state.selected.station_id}_all_quartile_hyetographs.csv`, 'text/csv');
}

function renderStationDetails(station) {
  setText('stationHeading', `Station ${station.station_id}`);
  setText('stationLocation', stationPlace(station));
  renderSelectedCard(station);
  renderMetadata(station);
  renderQuartileTable(station);
  renderCoefficientTable(station);
  renderEventBreakdown(station);
}

async function renderStationCurves(station) {
  setText('curveStatus', station.curve_path ? 'loading' : 'no curve');
  try {
    const curves = await fetchCurves(station);
    if (!state.selected || state.selected.station_id !== station.station_id) return;
    state.selectedCurves = curves;
    if (curves) {
      setDefaultStormQuartile(station, curves);
    }
    renderStormQuartileButtons(curves);
    renderCurveChart(curves);
    renderStormChart();
  } catch (error) {
    setText('curveStatus', 'curve load error');
    console.error(error);
    renderStormQuartileButtons(null);
    renderCurveChart(null);
    renderStormChart();
  }
}

function selectStation(stationId, zoom) {
  const station = state.stations.find((item) => item.station_id === stationId);
  if (!station) return;
  state.selected = station;
  updateUrlState(stationId);
  renderStationDetails(station);
  renderStationList();
  renderStationCurves(station);
  if (zoom) {
    const lat = numberValue(station.lat);
    const lon = numberValue(station.lon);
    if (lat !== null && lon !== null) {
      map.setView([lat, lon], Math.max(map.getZoom(), 8), { animate: true });
    }
  }
}

function renderHistogramChart(id, histogram, color, label) {
  makeChart(id, {
    type: 'bar',
    data: {
      labels: histogram.labels,
      datasets: [{ label, data: histogram.counts, backgroundColor: color, borderWidth: 0 }],
    },
    options: baseChartOptions({
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: chartTextColor(), maxRotation: 0 }, grid: { display: false } },
        y: { beginAtZero: true, ticks: { color: chartTextColor() }, grid: { color: chartGridColor() } },
      },
    }),
  });
}

function renderAnalyticsCharts() {
  const analytics = state.analytics;
  const statusLabels = Object.keys(analytics.status_counts);
  makeChart('statusChart', {
    type: 'bar',
    data: {
      labels: statusLabels.map(statusLabel),
      datasets: [{
        label: 'Stations',
        data: statusLabels.map((label) => analytics.status_counts[label]),
        backgroundColor: ['#62d77b', '#e9bb43', '#f26a6a', '#7f8a91', '#36c5a3'],
        borderWidth: 0,
      }],
    },
    options: baseChartOptions({ plugins: { legend: { display: false } } }),
  });

  makeChart('dominantQuartileChart', {
    type: 'doughnut',
    data: {
      labels: ['Q1', 'Q2', 'Q3', 'Q4'],
      datasets: [{
        data: [1, 2, 3, 4].map((q) => analytics.dominant_quartile_counts[String(q)] || 0),
        backgroundColor: [Q_COLORS[1], Q_COLORS[2], Q_COLORS[3], Q_COLORS[4]],
        borderColor: '#15181b',
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom', labels: { color: chartTextColor(), boxWidth: 12 } } },
    },
  });

  renderHistogramChart('eventsHistogramChart', analytics.event_histogram, '#36c5a3', 'Stations');
  renderHistogramChart('yearsHistogramChart', analytics.years_histogram, '#7c5cff', 'Stations');
  renderSummaryTables();
}

function renderSummaryTable(id, rows, nameKey) {
  const body = byId(id);
  body.innerHTML = '';
  rows.slice(0, 15).forEach((row) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${row[nameKey] || row.name || '-'}</td>
      <td>${fmt(row.n_stations)}</td>
      <td>${fmt(row.n_events)}</td>
      <td>${quartileLabel(row.dominant_quartile)}</td>
      <td>${fmtFixed(row.median_kge_mean, 3)}</td>
    `;
    body.appendChild(tr);
  });
}

function renderSummaryTables() {
  renderSummaryTable('stateSummaryTable', state.analytics.by_state || [], 'name');
  renderSummaryTable('biomeSummaryTable', state.analytics.by_biome || [], 'name');
}

function showPanel(panelId) {
  document.querySelectorAll('.tabbar button').forEach((button) => {
    button.classList.toggle('active', button.dataset.panel === panelId);
  });
  document.querySelectorAll('.panel-view').forEach((panel) => {
    panel.classList.toggle('active', panel.id === panelId);
  });
  requestAnimationFrame(() => {
    Object.values(state.charts).forEach((chart) => chart.resize());
  });
}

function csvEscape(value) {
  if (value === null || value === undefined) return '';
  const text = String(value);
  if (/[",\n]/.test(text)) return `"${text.replace(/"/g, '""')}"`;
  return text;
}

function downloadText(text, filename, type) {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function exportFilteredCsv() {
  const cols = [
    'station_id',
    'lat',
    'lon',
    'status',
    'status_reason',
    'municipality_name',
    'state_abbrev',
    'biome_name',
    'dominant_quartile',
    'n_events',
    'years_span',
    'missing_fraction',
    'mae_mean',
  ];
  const lines = [cols.join(',')];
  state.filtered.forEach((station) => {
    lines.push(cols.map((col) => csvEscape(station[col])).join(','));
  });
  downloadText(lines.join('\n'), 'huff_filtered_stations.csv', 'text/csv');
}

function wireEvents() {
  ['stationSearch', 'statusFilter', 'quartileFilter', 'stateFilter', 'biomeFilter', 'minEventsFilter', 'minYearsFilter'].forEach((id) => {
    byId(id).addEventListener('input', applyFilters);
    byId(id).addEventListener('change', applyFilters);
  });
  byId('fitAllButton').addEventListener('click', fitFiltered);
  byId('exportCsvButton').addEventListener('click', exportFilteredCsv);
  byId('exportReportButton').addEventListener('click', exportStationReport);
  byId('shareButton').addEventListener('click', shareStation);
  byId('helpButton').addEventListener('click', openWelcomeModal);
  byId('downloadStormButton').addEventListener('click', downloadStormCsv);
  byId('downloadAllStormsButton').addEventListener('click', downloadAllStormCsv);
  byId('downloadCurveButton').addEventListener('click', () => {
    const sid = state.selected ? state.selected.station_id : 'station';
    downloadChart('curveChart', `huff_curves_${sid}.png`);
  });
  byId('downloadStormChartButton').addEventListener('click', () => {
    const sid = state.selected ? state.selected.station_id : 'station';
    const q = state.activeStormQuartile || 1;
    downloadChart('stormChart', `design_storm_${sid}_q${q}.png`);
  });
  byId('stormDuration').addEventListener('input', renderStormChart);
  byId('stormVolume').addEventListener('input', renderStormChart);
  byId('stormTimestep').addEventListener('input', renderStormChart);
  document.querySelectorAll('.tabbar button').forEach((button) => {
    button.addEventListener('click', () => showPanel(button.dataset.panel));
  });
}

// ── Info tooltip content ──────────────────────────────────────────────────
const INFO_TIPS = {
  mae: 'Mean Absolute Error (MAE): average absolute deviation between the observed cumulative curve and the Huff reference curve. Lower values indicate a better fit.',
  dominant: 'Dominant quartile: the Q1–Q4 class with the most rainfall events at this station. Q1 = front-loaded (peak early); Q4 = back-loaded (peak late).',
  events: 'Number of independent sub-daily rainfall events extracted after quality control (minimum volume, duration, and inter-event separation thresholds applied).',
  curves: 'Dimensionless cumulative Huff curves. x-axis = fraction of storm duration (0→1); y-axis = fraction of total storm depth (0→1). Dashed band = 10th–90th percentile envelope for the active quartile.',
  storm: 'Apply the local Huff curve to your own design storm: set total depth and duration, choose a quartile, and download the time-distributed hyetograph as CSV.',
};

function initInfoTooltips() {
  const popup = byId('infoTipPopup');
  if (!popup) return;
  let hideTimer = null;
  document.addEventListener('mouseover', (event) => {
    const target = event.target.closest('[data-tip]');
    if (!target) return;
    const text = INFO_TIPS[target.dataset.tip];
    if (!text) return;
    clearTimeout(hideTimer);
    popup.textContent = text;
    popup.classList.add('visible');
    const rect = target.getBoundingClientRect();
    let left = rect.left;
    let top = rect.bottom + 8;
    if (left + 264 > window.innerWidth - 8) left = window.innerWidth - 272;
    if (top + 100 > window.innerHeight) top = rect.top - 108;
    popup.style.left = `${Math.max(8, left)}px`;
    popup.style.top = `${Math.max(8, top)}px`;
  });
  document.addEventListener('mouseout', (event) => {
    if (!event.target.closest('[data-tip]')) return;
    hideTimer = setTimeout(() => popup.classList.remove('visible'), 100);
  });
}

// ── Toast notification ────────────────────────────────────────────────────
function showToast(message, duration = 2200) {
  const toast = byId('toast');
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), duration);
}

// ── URL deep-linking ──────────────────────────────────────────────────────
function updateUrlState(stationId) {
  if (!stationId || !window.history || !window.history.replaceState) return;
  const url = new URL(window.location.href);
  url.searchParams.set('s', String(stationId));
  window.history.replaceState(null, '', url.toString());
}

function getUrlStation() {
  try {
    return new URLSearchParams(window.location.search).get('s') || null;
  } catch (e) {
    return null;
  }
}

// ── Share station link ────────────────────────────────────────────────────
function shareStation() {
  const url = window.location.href;
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(url)
      .then(() => showToast('Link copied!'))
      .catch(() => { try { prompt('Copy this link:', url); } catch (e2) {} });
  } else {
    try { prompt('Copy this link:', url); } catch (e) {}
  }
}

// ── Huff curves SVG generator ─────────────────────────────────────────────
function generateHuffCurvesSVG(curves) {
  const W = 560, H = 320;
  const pL = 52, pR = 20, pT = 16, pB = 52;
  const cW = W - pL - pR;
  const cH = H - pT - pB;
  const QC = { '1': '#e84d4f', '2': '#e0930a', '3': '#1a9a94', '4': '#5a3dcc' };
  const QL = { '1': 'Q1 – 1st quartile', '2': 'Q2 – 2nd quartile', '3': 'Q3 – 3rd quartile', '4': 'Q4 – 4th quartile' };

  const tx = (v) => (pL + v * cW).toFixed(2);
  const ty = (v) => (pT + (1 - v) * cH).toFixed(2);

  function path(tau, vals) {
    if (!tau || !vals) return '';
    return tau.map((t, i) => `${i === 0 ? 'M' : 'L'}${tx(t)},${ty(vals[i])}`).join(' ');
  }

  const lines = [
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">`,
    `<rect width="${W}" height="${H}" fill="#ffffff" rx="4"/>`,
    `<rect x="${pL}" y="${pT}" width="${cW}" height="${cH}" fill="#f9f9f9" stroke="#dddddd" stroke-width="0.5"/>`,
  ];

  // Grid
  for (let i = 0; i <= 10; i++) {
    const gx = (+tx(i / 10)).toFixed(1);
    const gy = (+ty(i / 10)).toFixed(1);
    lines.push(`<line x1="${gx}" y1="${pT}" x2="${gx}" y2="${pT + cH}" stroke="#e0e0e0" stroke-width="0.5"/>`);
    lines.push(`<line x1="${pL}" y1="${gy}" x2="${pL + cW}" y2="${gy}" stroke="#e0e0e0" stroke-width="0.5"/>`);
    if (i % 2 === 0) {
      lines.push(`<text x="${gx}" y="${pT + cH + 14}" text-anchor="middle" fill="#666" font-size="9" font-family="Arial">${(i / 10).toFixed(1)}</text>`);
      lines.push(`<text x="${pL - 6}" y="${(+ty(i / 10) + 3).toFixed(1)}" text-anchor="end" fill="#666" font-size="9" font-family="Arial">${(i / 10).toFixed(1)}</text>`);
    }
  }

  // 1:1 diagonal
  lines.push(`<line x1="${tx(0)}" y1="${ty(0)}" x2="${tx(1)}" y2="${ty(1)}" stroke="#cccccc" stroke-width="1" stroke-dasharray="4,3"/>`);

  // Curves
  for (let q = 1; q <= 4; q++) {
    const rec = curves.quartiles?.[String(q)];
    if (!rec?.tau || !rec?.median) continue;
    lines.push(`<path d="${path(rec.tau, rec.median)}" fill="none" stroke="${QC[String(q)]}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>`);
  }

  // Axes
  lines.push(`<line x1="${pL}" y1="${pT}" x2="${pL}" y2="${pT + cH}" stroke="#333" stroke-width="1.2"/>`);
  lines.push(`<line x1="${pL}" y1="${pT + cH}" x2="${pL + cW}" y2="${pT + cH}" stroke="#333" stroke-width="1.2"/>`);

  // Axis labels
  lines.push(`<text x="${(pL + cW / 2).toFixed(1)}" y="${H - 6}" text-anchor="middle" fill="#333" font-size="11" font-family="Arial">Normalized time (t / T)</text>`);
  lines.push(`<text x="11" y="${(pT + cH / 2).toFixed(1)}" text-anchor="middle" fill="#333" font-size="11" font-family="Arial" transform="rotate(-90 11 ${(pT + cH / 2).toFixed(1)})">Normalized precipitation (P / Pᵀ)</text>`);

  // Legend (right side, inside chart area)
  const legX = pL + cW - 130;
  const legY = pT + 12;
  lines.push(`<rect x="${legX - 4}" y="${legY - 10}" width="126" height="${4 * 20 + 4}" fill="white" fill-opacity="0.85" rx="3" stroke="#ddd" stroke-width="0.5"/>`);
  for (let q = 1; q <= 4; q++) {
    const ly = legY + (q - 1) * 20;
    lines.push(`<line x1="${legX}" y1="${ly}" x2="${legX + 20}" y2="${ly}" stroke="${QC[String(q)]}" stroke-width="2"/>`);
    lines.push(`<text x="${legX + 25}" y="${ly + 4}" fill="#333" font-size="10" font-family="Arial">${QL[String(q)]}</text>`);
  }

  lines.push('</svg>');
  return lines.join('\n');
}

// ── Station report export (.docx) ─────────────────────────────────────────
async function exportStationReport() {
  const station = state.selected;
  if (!station) { showToast('Select a station first.'); return; }
  if (!window.docx) { showToast('Report library not loaded yet — try again shortly.'); return; }

  showToast('Building report…');

  const {
    Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
    ImageRun, AlignmentType, BorderStyle, WidthType, ShadingType,
    HeadingLevel, Footer, PageNumber,
  } = window.docx;

  // A4, 1-inch margins
  const PAGE_W = 11906;
  const PAGE_H = 16838;
  const MARGIN = 1440;
  const CW = PAGE_W - 2 * MARGIN; // 9026 DXA content width

  const Q_HEX = { '1': 'E84D4F', '2': 'F4B63F', '3': '2CB7B0', '4': '7C5CFF' };
  const Q_LABEL = { '1': '1st Quartile', '2': '2nd Quartile', '3': '3rd Quartile', '4': '4th Quartile' };
  const BORDER = { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' };
  const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };
  const CM = { top: 80, bottom: 80, left: 120, right: 120 };

  function hCell(text, w, opts = {}) {
    const { align = AlignmentType.CENTER, fill = 'EEEEEE' } = opts;
    return new TableCell({
      width: { size: w, type: WidthType.DXA }, borders: BORDERS,
      shading: { fill, type: ShadingType.CLEAR }, margins: CM,
      children: [new Paragraph({
        alignment: align,
        children: [new TextRun({ text, bold: true, font: 'Arial', size: 18 })],
      })],
    });
  }

  function dCell(text, w, opts = {}) {
    const { align = AlignmentType.CENTER, fill = null, color = '000000', bold = false } = opts;
    const cell = new TableCell({
      width: { size: w, type: WidthType.DXA }, borders: BORDERS, margins: CM,
      children: [new Paragraph({
        alignment: align,
        children: [new TextRun({ text: String(text ?? '-'), font: 'Arial', size: 18, color, bold })],
      })],
    });
    if (fill) cell.properties = { shading: { fill, type: ShadingType.CLEAR } };
    return cell;
  }

  function qCell(q, w) {
    return new TableCell({
      width: { size: w, type: WidthType.DXA }, borders: BORDERS,
      shading: { fill: Q_HEX[String(q)], type: ShadingType.CLEAR }, margins: CM,
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: Q_LABEL[String(q)], bold: true, font: 'Arial', size: 18, color: 'FFFFFF' })],
      })],
    });
  }

  function sp(n = 200) { return new Paragraph({ spacing: { after: n }, children: [] }); }

  function bodyText(text) {
    return new Paragraph({
      spacing: { after: 120 },
      children: [new TextRun({ text, font: 'Arial', size: 20 })],
    });
  }

  function h1(text) {
    return new Paragraph({
      heading: HeadingLevel.HEADING_1,
      spacing: { before: 400, after: 160 },
      children: [new TextRun({ text, font: 'Arial', bold: true, size: 28, color: '111111' })],
    });
  }

  // Huff curves PNG at ~300 DPI (SVG rendered to high-res canvas)
  let chartImage = null;
  if (state.selectedCurves) {
    try {
      const svgStr = generateHuffCurvesSVG(state.selectedCurves);
      // SVG viewBox is 560×320; scale ×4 ≈ 300 DPI at 500pt print width
      const scale = 4;
      const svgW = 560, svgH = 320;
      const pngBytes = await new Promise((resolve, reject) => {
        const blob = new Blob([svgStr], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          canvas.width = svgW * scale;
          canvas.height = svgH * scale;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          URL.revokeObjectURL(url);
          const b64 = canvas.toDataURL('image/png').split(',')[1];
          const bin = atob(b64);
          const buf = new Uint8Array(bin.length);
          for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
          resolve(buf.buffer);
        };
        img.onerror = (e) => { URL.revokeObjectURL(url); reject(e); };
        img.src = url;
      });
      chartImage = new ImageRun({
        type: 'png', data: pngBytes,
        transformation: { width: 500, height: 286 },
        altText: { title: 'Huff Curves', description: 'Normalized cumulative Huff curves', name: 'huffcurves' },
      });
    } catch (e) { console.error('Chart image generation failed:', e); }
  }

  // Metadata table (2 cols: 3000 | 6026)
  const META_W = [3000, CW - 3000];
  const metaItems = metadataItems(station).filter(([, v]) => v != null && String(v) !== '-');
  const metaTable = new Table({
    width: { size: CW, type: WidthType.DXA },
    columnWidths: META_W,
    rows: [
      new TableRow({ children: [hCell('Property', META_W[0], { align: AlignmentType.LEFT }), hCell('Value', META_W[1], { align: AlignmentType.LEFT })] }),
      ...metaItems.map(([label, value]) => new TableRow({
        children: [
          dCell(label, META_W[0], { align: AlignmentType.LEFT }),
          dCell(String(value), META_W[1], { align: AlignmentType.LEFT }),
        ],
      })),
    ],
  });

  // Quartile stats table (6 cols: 1402 | 1525×4 | 1524)
  const STAT_W = [1402, 1525, 1525, 1525, 1525, 1524];
  const statsTable = new Table({
    width: { size: CW, type: WidthType.DXA },
    columnWidths: STAT_W,
    rows: [
      new TableRow({ children: [
        hCell('Quartile', STAT_W[0]),
        hCell('Events (share)', STAT_W[1]),
        hCell('Avg. Volume (mm)', STAT_W[2]),
        hCell('Avg. Duration (h)', STAT_W[3]),
        hCell('Peak intensity (mm/h)', STAT_W[4]),
        hCell('MAE', STAT_W[5]),
      ] }),
      ...[1, 2, 3, 4].map((q) => {
        const rec = (station.quartiles && station.quartiles[String(q)]) || {};
        return new TableRow({ children: [
          qCell(q, STAT_W[0]),
          dCell(rec.n_events != null ? `${fmt(rec.n_events)} (${fmtPercentValue(rec.percent_events, 1)}%)` : '-', STAT_W[1]),
          dCell(rec.avg_volume_mm != null ? `${fmtFixed(rec.avg_volume_mm, 1)}` : '-', STAT_W[2]),
          dCell(rec.avg_duration_h != null ? `${fmtFixed(rec.avg_duration_h, 1)}` : '-', STAT_W[3]),
          dCell(rec.max_intensity_mm_h != null ? `${fmtFixed(rec.max_intensity_mm_h, 1)}` : '-', STAT_W[4]),
          dCell(rec.mae != null ? fmtFixed(rec.mae, 3) : '-', STAT_W[5]),
        ] });
      }),
    ],
  });

  // Coefficient table (9 cols: 1402 | 953×8)
  const COEF_W = [1402, ...Array(8).fill(953)]; // 1402 + 953*8 = 9026
  const coeffTable = new Table({
    width: { size: CW, type: WidthType.DXA },
    columnWidths: COEF_W,
    rows: [
      new TableRow({ children: [
        hCell('Quartile', COEF_W[0]),
        ...[1, 2, 3, 4, 5, 6, 7, 8].map((i) => hCell(`c${i}`, COEF_W[i])),
      ] }),
      ...[1, 2, 3, 4].map((q) => {
        const rec = (station.quartiles && station.quartiles[String(q)]) || {};
        const coeffs = rec.coefficients || Array(8).fill(null);
        return new TableRow({ children: [
          qCell(q, COEF_W[0]),
          ...coeffs.slice(0, 8).map((c, i) => dCell(c != null ? c.toFixed(6) : '-', COEF_W[i + 1])),
        ] });
      }),
    ],
  });

  const domQ = station.dominant_quartile;
  const domDesc = { 1: 'front-loaded (peak in the first quarter)', 2: 'early front-loaded (peak in the second quarter)', 3: 'late back-loaded (peak in the third quarter)', 4: 'back-loaded (peak in the final quarter)' };
  const dateStr = new Date().toISOString().split('T')[0];

  const doc = new Document({
    styles: {
      default: { document: { run: { font: 'Arial', size: 20 } } },
      paragraphStyles: [
        { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
          run: { size: 28, bold: true, font: 'Arial', color: '111111' },
          paragraph: { spacing: { before: 400, after: 160 }, outlineLevel: 0 } },
      ],
    },
    sections: [{
      properties: {
        page: { size: { width: PAGE_W, height: PAGE_H }, margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN } },
      },
      footers: {
        default: new Footer({ children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: `Huff Curves BR Atlas  |  Station ${station.station_id}  |  Page `, font: 'Arial', size: 16, color: '888888' }),
            new TextRun({ children: [PageNumber.CURRENT], font: 'Arial', size: 16, color: '888888' }),
          ],
        })] }),
      },
      children: [
        // Title block
        new Paragraph({
          spacing: { after: 80 },
          children: [new TextRun({ text: 'HUFF CURVES STATION REPORT', font: 'Arial', size: 40, bold: true, color: '36C5A3' })],
        }),
        new Paragraph({
          spacing: { after: 60 },
          children: [new TextRun({ text: `Station ${station.station_id}`, font: 'Arial', size: 32, bold: true }), new TextRun({ text: `  —  ${station.municipality_name || ''}, ${station.state_name || station.state_abbrev || ''}`, font: 'Arial', size: 28 })],
        }),
        new Paragraph({
          spacing: { after: 280 },
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: '36C5A3', space: 1 } },
          children: [new TextRun({ text: `${station.biome_name || ''}   |   ${station.region_name || ''}   |   Generated: ${dateStr}`, font: 'Arial', size: 18, color: '888888' })],
        }),

        // 1. Station Metadata
        h1('1. Station Metadata'),
        metaTable,
        sp(300),

        // 2. Quartile Statistics
        h1('2. Quartile Statistics'),
        bodyText(`The dominant quartile at this station is ${Q_LABEL[String(domQ)] || `Q${domQ}`}, meaning the majority of rainfall events exhibit a ${domDesc[domQ] || ''} temporal distribution.`),
        sp(120),
        statsTable,
        sp(300),

        // 3. Normalized Huff Curves
        h1('3. Normalized Huff Curves'),
        bodyText('The figure below shows the dimensionless cumulative Huff curves for each quartile (Q1–Q4), computed as the bootstrap median of all classified storm events at this station. The dashed band represents the 10th–90th percentile envelope of the dominant quartile. The x-axis represents normalized storm time (t / T) and the y-axis represents the cumulative rainfall fraction (P / Pᵀ).'),
        sp(80),
        ...(chartImage
          ? [new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [chartImage] })]
          : [bodyText('[Curves chart not available — ensure the station curves are loaded before exporting.]')]),
        sp(300),

        // 4. Polynomial Coefficients
        h1('4. Polynomial Coefficients'),
        bodyText('Each Huff curve is approximated by an 8th-degree polynomial that maps normalized storm time t ∈ [0, 1] to cumulative rainfall fraction:'),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 100, after: 100 },
          children: [new TextRun({ text: 'P / Pᵀ = c₁ t⁷ + c₂ t⁶ + c₃ t⁵ + c₄ t⁴ + c₅ t³ + c₆ t² + c₇ t + c₈', font: 'Arial', size: 20, italics: true })],
        }),
        bodyText('Coefficients for each quartile, fitted to the bootstrap median curve, are given in the table below.'),
        sp(80),
        coeffTable,
        sp(300),

        // 5. Methodology
        h1('5. Methodology'),
        bodyText('Huff curves are dimensionless cumulative mass curves that characterize the temporal distribution of rainfall within a storm event. Each event is classified into one of four quartiles (Q1–Q4) according to the normalized time at which peak intensity occurs: Q1 events concentrate the majority of rainfall in the first quarter of the storm duration (front-loaded), while Q4 events release most rainfall near the end (back-loaded).'),
        sp(80),
        bodyText('Storm events were extracted from sub-daily rainfall records using an inter-event time definition (IETD) criterion, with minimum thresholds applied for event volume and duration to ensure data quality. For each station, events were classified by quartile, and the bootstrap median of the normalized cumulative mass curves was computed across 1000 resamples to obtain a robust central estimate along with 10th–90th percentile uncertainty bounds.'),
        sp(80),
        bodyText('The Mean Absolute Error (MAE) measures the average absolute deviation between the observed cumulative curve and the fitted Huff reference curve, where lower values indicate better agreement.'),
        sp(300),

        // 6. Design Storm Timeseries
        ...(() => {
          const duration = Math.max(0.01, numberValue(byId('stormDuration').value) || 24);
          const volume = Math.max(0, numberValue(byId('stormVolume').value) || 100);
          const timestep = Math.max(1, numberValue(byId('stormTimestep').value) || 10);
          const rows1 = stormRowsForQuartile(1) || [];
          const rows2 = stormRowsForQuartile(2) || [];
          const rows3 = stormRowsForQuartile(3) || [];
          const rows4 = stormRowsForQuartile(4) || [];
          const nRows = Math.max(rows1.length, rows2.length, rows3.length, rows4.length);

          if (!nRows) return [];

          // 6 columns: Step | Period (h) | Q1 (mm) | Q2 (mm) | Q3 (mm) | Q4 (mm)
          const SW = [800, 1500, 1682, 1682, 1682, 1680];

          const stormTable = new Table({
            width: { size: CW, type: WidthType.DXA },
            columnWidths: SW,
            rows: [
              new TableRow({ children: [
                hCell('Step', SW[0]),
                hCell('Period (h)', SW[1]),
                hCell('Q1 depth (mm)', SW[2]),
                hCell('Q2 depth (mm)', SW[3]),
                hCell('Q3 depth (mm)', SW[4]),
                hCell('Q4 depth (mm)', SW[5]),
              ] }),
              ...Array.from({ length: nRows }, (_, i) => {
                const r1 = rows1[i]; const r2 = rows2[i]; const r3 = rows3[i]; const r4 = rows4[i];
                const ref = r1 || r2 || r3 || r4;
                return new TableRow({ children: [
                  dCell(String(i + 1), SW[0]),
                  dCell(ref ? `${fmtFixed(ref.hour_start, 2)} – ${fmtFixed(ref.hour_end, 2)}` : '-', SW[1]),
                  dCell(r1 ? fmtFixed(r1.depth_mm, 3) : '-', SW[2]),
                  dCell(r2 ? fmtFixed(r2.depth_mm, 3) : '-', SW[3]),
                  dCell(r3 ? fmtFixed(r3.depth_mm, 3) : '-', SW[4]),
                  dCell(r4 ? fmtFixed(r4.depth_mm, 3) : '-', SW[5]),
                ] });
              }),
            ],
          });

          return [
            h1('6. Design Storm Timeseries'),
            bodyText(`Incremental rainfall depth (mm) per time step for the design storm configuration: duration = ${fmtFixed(duration, 2)} h, total volume = ${fmtFixed(volume, 1)} mm, time step = ${fmt(timestep)} min. Each column represents the depth distribued according to the local Huff curve for that quartile.`),
            sp(80),
            stormTable,
            sp(300),
          ];
        })(),

        // Citation
        new Paragraph({
          spacing: { after: 60 },
          border: { top: { style: BorderStyle.SINGLE, size: 2, color: 'CCCCCC', space: 1 } },
          children: [new TextRun({ text: 'Reference: Gomes Junior, M.N. et al. (in prep.). Regional Huff curves for Brazil derived from high-density rain gauge networks. Journal of Hydrology.', font: 'Arial', size: 18, italics: true, color: '666666' })],
        }),
        new Paragraph({
          children: [new TextRun({ text: `Generated by Huff Curves BR Atlas  |  ${dateStr}  |  https://github.com/mngomes/Huff_Curves_BR`, font: 'Arial', size: 16, color: 'AAAAAA' })],
        }),
      ],
    }],
  });

  try {
    const blob = await Packer.toBlob(doc);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `huff_station_${station.station_id}.docx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast('Report downloaded.');
  } catch (err) {
    console.error('DOCX export failed:', err);
    showToast('Export failed — see browser console for details.');
  }
}

// ── Chart PNG download ────────────────────────────────────────────────────
function downloadChart(chartKey, filename) {
  const chart = state.charts[chartKey];
  if (!chart) { showToast('No chart to download.'); return; }
  const dataUrl = chart.canvas.toDataURL('image/png');
  const link = document.createElement('a');
  link.href = dataUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
}

// ── Welcome modal ─────────────────────────────────────────────────────────
const WELCOME_KEY = 'huffbr_v1_welcomed';
let _modalStep = 0;
const _MODAL_STEPS = 3;

function _gotoModalStep(index) {
  _modalStep = Math.max(0, Math.min(_MODAL_STEPS - 1, index));
  ['welcomeStep0', 'welcomeStep1', 'welcomeStep2'].forEach((id, i) => {
    const el = byId(id);
    if (el) el.hidden = i !== _modalStep;
  });
  document.querySelectorAll('.modal-dot').forEach((dot, i) => {
    dot.classList.toggle('active', i === _modalStep);
  });
  const prev = byId('modalPrev');
  const next = byId('modalNext');
  if (prev) prev.style.visibility = _modalStep === 0 ? 'hidden' : '';
  if (next) next.textContent = _modalStep === _MODAL_STEPS - 1 ? 'Done' : 'Next';
}

function openWelcomeModal() {
  const overlay = byId('welcomeModal');
  if (overlay) overlay.classList.remove('hidden');
  _gotoModalStep(0);
}

function closeWelcomeModal() {
  const overlay = byId('welcomeModal');
  if (!overlay) return;
  const cb = byId('modalDontShow');
  if (cb && cb.checked) {
    try { localStorage.setItem(WELCOME_KEY, '1'); } catch (e) {}
  }
  overlay.classList.add('hidden');
}

function initWelcomeModal() {
  const overlay = byId('welcomeModal');
  if (!overlay) return;

  byId('modalPrev').addEventListener('click', () => _gotoModalStep(_modalStep - 1));
  byId('modalNext').addEventListener('click', () => {
    if (_modalStep === _MODAL_STEPS - 1) closeWelcomeModal();
    else _gotoModalStep(_modalStep + 1);
  });
  byId('modalClose').addEventListener('click', closeWelcomeModal);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) closeWelcomeModal(); });
  document.querySelectorAll('.modal-dot').forEach((dot) => {
    dot.addEventListener('click', () => _gotoModalStep(Number(dot.dataset.go)));
  });

  _gotoModalStep(0);

  let firstVisit = true;
  try { firstVisit = !localStorage.getItem(WELCOME_KEY); } catch (e) {}
  if (firstVisit) overlay.classList.remove('hidden');
}

// ── Keyboard shortcuts ────────────────────────────────────────────────────
function initKeyboard() {
  document.addEventListener('keydown', (event) => {
    const tag = (document.activeElement || {}).tagName || '';
    const inField = /^(INPUT|TEXTAREA|SELECT)$/i.test(tag);
    const modalOpen = byId('welcomeModal') && !byId('welcomeModal').classList.contains('hidden');

    if (event.key === 'Escape' && modalOpen) { closeWelcomeModal(); return; }
    if (inField) return;

    if (event.key === '?' || event.key === 'h') { openWelcomeModal(); return; }

    if (event.key === '/') {
      event.preventDefault();
      const search = byId('stationSearch');
      if (search) { search.focus(); search.select(); }
      return;
    }

    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      if (!state.filtered.length) return;
      const sorted = state.filtered.slice().sort((a, b) => {
        const aOk = a.status === 'ok' ? 1 : 0;
        const bOk = b.status === 'ok' ? 1 : 0;
        if (aOk !== bOk) return bOk - aOk;
        return (numberValue(b.n_events) || 0) - (numberValue(a.n_events) || 0);
      });
      const cur = state.selected
        ? sorted.findIndex((s) => s.station_id === state.selected.station_id)
        : -1;
      const next = Math.max(0, Math.min(sorted.length - 1,
        event.key === 'ArrowDown' ? cur + 1 : cur - 1));
      selectStation(sorted[next].station_id, true);
    }
  });
}

async function init() {
  let manifest;
  let analytics;
  let stations;
  if (window.HUFF_BOOTSTRAP) {
    manifest = window.HUFF_BOOTSTRAP.manifest;
    analytics = window.HUFF_BOOTSTRAP.analytics;
    stations = window.HUFF_BOOTSTRAP.stations;
  } else {
    [manifest, analytics, stations] = await Promise.all([
      fetch('data/manifest.json').then((response) => response.json()),
      fetch('data/analytics.json').then((response) => response.json()),
      fetch('data/stations.json').then((response) => response.json()),
    ]);
  }

  state.manifest = manifest;
  state.analytics = analytics;
  state.stations = stations;

  populateFilters();
  renderGlobalStats();
  renderLegend();
  renderAnalyticsCharts();
  wireEvents();
  initWelcomeModal();
  initInfoTooltips();
  initKeyboard();
  applyFilters();
  fitFiltered();

  // Pre-select from URL (?s=stationId) or fall back to best-data station
  const urlId = getUrlStation();
  let first = urlId ? state.stations.find((s) => s.station_id === urlId) : null;
  if (!first) {
    first = state.stations
      .filter((s) => s.status === 'ok')
      .sort((a, b) => (numberValue(b.n_events) || 0) - (numberValue(a.n_events) || 0))[0]
      || state.stations[0];
  }
  if (first) selectStation(first.station_id, false);
}

init().catch((error) => {
  console.error(error);
  setText('selectedTitle', 'Could not load web assets');
  setText('selectedSubtitle', error.message || String(error));
});
