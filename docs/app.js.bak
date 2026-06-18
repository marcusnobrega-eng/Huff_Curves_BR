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
  setText('selectedKge', fmtFixed(station.kge_mean, 3));
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
      <td>${fmtFixed(rec.kge, 3)}</td>
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
    'kge_mean',
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
  byId('downloadStormButton').addEventListener('click', downloadStormCsv);
  byId('downloadAllStormsButton').addEventListener('click', downloadAllStormCsv);
  byId('stormDuration').addEventListener('input', renderStormChart);
  byId('stormVolume').addEventListener('input', renderStormChart);
  byId('stormTimestep').addEventListener('input', renderStormChart);
  document.querySelectorAll('.tabbar button').forEach((button) => {
    button.addEventListener('click', () => showPanel(button.dataset.panel));
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
  applyFilters();
  fitFiltered();

  const first = state.stations
    .filter((station) => station.status === 'ok')
    .sort((a, b) => (numberValue(b.n_events) || 0) - (numberValue(a.n_events) || 0))[0] || state.stations[0];
  if (first) selectStation(first.station_id, false);
}

init().catch((error) => {
  console.error(error);
  setText('selectedTitle', 'Could not load web assets');
  setText('selectedSubtitle', error.message || String(error));
});
