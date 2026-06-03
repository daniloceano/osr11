'use client';

import { useState, useMemo, useRef, useCallback } from 'react';

/* ── Types ─────────────────────────────────────────────────────────────── */

interface GridPoint {
  lat: number;
  lon: number;
  municipality: string | null;
  [key: string]: unknown;
}

export interface HazardData {
  metadata: {
    generated_at: string;
    period: string;
    n_years: number;
    n_grid_points: number;
    modules_included: string[];
    thr_hs_pct: number;
    thr_ssh_pct: number;
  };
  grid_points: GridPoint[];
}

type AnalysisTab =
  | 'compound'
  | 'duration'
  | 'seasonality'
  | 'trends'
  | 'eva'
  | 'dependence';

interface MetricDef {
  key: string;
  label: string;
  unit: string;
  field: string;
  description?: string;
}

/* ── Metric catalogue ──────────────────────────────────────────────────── */

const TAB_LABELS: Record<AnalysisTab, string> = {
  compound: 'Compound',
  duration: 'Duration',
  seasonality: 'Seasonality',
  trends: 'Trends',
  eva: 'Return Levels',
  dependence: 'Dependence',
};

const TAB_COLORS: Record<AnalysisTab, string> = {
  compound: '#756bb1',
  duration: '#2171b5',
  seasonality: '#238b45',
  trends: '#d94801',
  eva: '#cb181d',
  dependence: '#6a51a3',
};

const METRICS: Record<AnalysisTab, MetricDef[]> = {
  compound: [
    { key: 'count', label: 'Compound count (total)', unit: 'events', field: 'compound_count_total' },
    { key: 'annual', label: 'Compound count (annual mean)', unit: 'events yr⁻¹', field: 'compound_count_annual_mean' },
    { key: 'intensity', label: 'Mean normalized intensity', unit: '[0–1]', field: 'compound_mean_intensity_norm' },
    { key: 'p95_int', label: 'P95 normalized intensity', unit: '[0–1]', field: 'compound_p95_intensity_norm' },
    { key: 'overlap', label: 'Mean overlap duration', unit: 'days', field: 'compound_mean_overlap_duration' },
    { key: 'lag', label: 'Mean peak lag (Hₛ→SSH)', unit: 'days', field: 'compound_mean_peak_lag_days' },
  ],
  duration: [
    { key: 'hs_mean', label: 'Hₛ mean storm duration', unit: 'days', field: 'hs_mean_duration_days' },
    { key: 'hs_p95', label: 'Hₛ P95 storm duration', unit: 'days', field: 'hs_p95_duration_days' },
    { key: 'ssh_mean', label: 'SSH mean storm duration', unit: 'days', field: 'ssh_total_mean_duration_days' },
    { key: 'ssh_p95', label: 'SSH P95 storm duration', unit: 'days', field: 'ssh_total_p95_duration_days' },
    { key: 'hs_count', label: 'Hₛ storm count (annual)', unit: 'storms yr⁻¹', field: 'hs_storm_count_annual_mean' },
    { key: 'ssh_count', label: 'SSH storm count (annual)', unit: 'storms yr⁻¹', field: 'ssh_total_storm_count_annual_mean' },
    { key: 'hs_iet', label: 'Hₛ mean inter-event time', unit: 'days', field: 'hs_mean_interevent_time_days' },
    { key: 'ssh_iet', label: 'SSH mean inter-event time', unit: 'days', field: 'ssh_total_mean_interevent_time_days' },
  ],
  seasonality: [
    { key: 'hs_peak', label: 'Hₛ peak month', unit: 'month', field: 'hs_peak_month' },
    { key: 'ssh_peak', label: 'SSH peak month', unit: 'month', field: 'ssh_total_peak_month' },
    { key: 'comp_peak', label: 'Compound peak month', unit: 'month', field: 'compound_peak_month' },
  ],
  trends: [
    { key: 'hs_count_slope', label: 'Hₛ count trend (slope)', unit: 'events yr⁻¹ yr⁻¹', field: 'annual_hs_count_slope', description: 'Sen slope of annual Hₛ storm count' },
    { key: 'ssh_count_slope', label: 'SSH count trend (slope)', unit: 'events yr⁻¹ yr⁻¹', field: 'annual_ssh_total_count_slope' },
    { key: 'comp_count_slope', label: 'Compound count trend', unit: 'events yr⁻¹ yr⁻¹', field: 'annual_compound_count_slope' },
    { key: 'hs_peak_slope', label: 'Hₛ mean peak trend', unit: 'm yr⁻¹', field: 'annual_mean_hs_peak_slope' },
    { key: 'ssh_peak_slope', label: 'SSH mean peak trend', unit: 'm yr⁻¹', field: 'annual_mean_ssh_total_peak_slope' },
    { key: 'hs_dur_slope', label: 'Hₛ duration trend', unit: 'days yr⁻¹', field: 'annual_mean_hs_duration_slope' },
  ],
  eva: [
    { key: 'hs_rl2', label: 'Hₛ 2-yr return level', unit: 'm', field: 'hs_rl_2yr' },
    { key: 'hs_rl10', label: 'Hₛ 10-yr return level', unit: 'm', field: 'hs_rl_10yr' },
    { key: 'hs_rl50', label: 'Hₛ 50-yr return level', unit: 'm', field: 'hs_rl_50yr' },
    { key: 'ssh_rl2', label: 'SSH 2-yr return level', unit: 'm', field: 'ssh_total_rl_2yr' },
    { key: 'ssh_rl10', label: 'SSH 10-yr return level', unit: 'm', field: 'ssh_total_rl_10yr' },
    { key: 'ssh_rl50', label: 'SSH 50-yr return level', unit: 'm', field: 'ssh_total_rl_50yr' },
  ],
  dependence: [
    { key: 'tau', label: "Kendall's τ", unit: '–', field: 'tau', description: 'Rank correlation between Hₛ and SSH peaks in compound events' },
    { key: 'rho', label: "Spearman's ρ", unit: '–', field: 'rho' },
    { key: 'chi', label: 'Extremal χ', unit: '–', field: 'chi', description: 'Asymptotic tail dependence: χ > 0 means extremes tend to co-occur in the limit' },
    { key: 'chi_bar', label: 'Extremal χ̄', unit: '–', field: 'chi_bar', description: 'Sub-asymptotic association: informative when χ ≈ 0; higher χ̄ = stronger residual tail dependence' },
    { key: 'n_pairs', label: 'Compound pairs', unit: 'events', field: 'n_compound_pairs' },
  ],
};

/* ── Color scales ──────────────────────────────────────────────────────── */

const RAMP_SEQUENTIAL = [
  '#ffffcc', '#ffeda0', '#fed976', '#feb24c', '#fd8d3c',
  '#fc4e2a', '#e31a1c', '#bd0026', '#800026',
];

const RAMP_DIVERGING = [
  '#2166ac', '#4393c3', '#92c5de', '#d1e5f0', '#f7f7f7',
  '#fddbc7', '#f4a582', '#d6604d', '#b2182b',
];

// Cyclic seasonal ramp: DJF=red, MAM=yellow, JJA=blue, SON=green, Dec→red
const RAMP_MONTH = [
  '#d73027', '#fc8d59',   // Jan, Feb  — DJF (red)
  '#fec44f', '#fee090',   // Mar, Apr  — MAM (yellow)
  '#d9ef8b',              // May       — MAM→JJA transition
  '#91bfdb', '#4575b4',   // Jun, Jul  — JJA (blue)
  '#313695',              // Aug       — JJA (deep blue)
  '#1a9850', '#66bd63',   // Sep, Oct  — SON (green)
  '#a6d96a',              // Nov       — SON→DJF transition
  '#a50026',              // Dec       — DJF (dark red, closing cycle)
];

function getRamp(tab: AnalysisTab, field: string): string[] {
  if (field.includes('peak_month')) return RAMP_MONTH;
  if (field.includes('slope') || field.includes('lag')) return RAMP_DIVERGING;
  return RAMP_SEQUENTIAL;
}

function interpolateColor(ramp: string[], t: number): string {
  const clamped = Math.max(0, Math.min(1, t));
  const idx = clamped * (ramp.length - 1);
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  if (lo === hi) return ramp[lo];
  const frac = idx - lo;
  const c1 = hexToRgb(ramp[lo]);
  const c2 = hexToRgb(ramp[hi]);
  const r = Math.round(c1.r + (c2.r - c1.r) * frac);
  const g = Math.round(c1.g + (c2.g - c1.g) * frac);
  const b = Math.round(c1.b + (c2.b - c1.b) * frac);
  return `rgb(${r},${g},${b})`;
}

function hexToRgb(hex: string) {
  const n = parseInt(hex.slice(1), 16);
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
}

/* ── Map projection ────────────────────────────────────────────────────── */

const MAP_BOUNDS = { lonMin: -56, lonMax: -27, latMin: -36, latMax: 7 };
const ASPECT = (MAP_BOUNDS.lonMax - MAP_BOUNDS.lonMin) / (MAP_BOUNDS.latMax - MAP_BOUNDS.latMin);

function project(lon: number, lat: number, width: number, height: number) {
  const x = ((lon - MAP_BOUNDS.lonMin) / (MAP_BOUNDS.lonMax - MAP_BOUNDS.lonMin)) * width;
  const y = ((MAP_BOUNDS.latMax - lat) / (MAP_BOUNDS.latMax - MAP_BOUNDS.latMin)) * height;
  return { x, y };
}

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/* ── Format helpers ────────────────────────────────────────────────────── */

function fmtVal(v: number | null | undefined, unit: string): string {
  if (v === null || v === undefined) return 'N/A';
  if (unit === 'month') return MONTH_NAMES[(v as number) - 1] ?? '?';
  if (unit === 'events' || unit === 'storms') return Math.round(v).toLocaleString();
  if (unit === '[0–1]' || unit === '–') return v.toFixed(3);
  if (unit.includes('yr⁻¹ yr⁻¹')) return v.toExponential(2);
  if (unit === 'm') return v.toFixed(2);
  if (unit.includes('yr⁻¹')) return v.toFixed(1);
  return v.toFixed(2);
}

/* ── Significance overlay for trends ───────────────────────────────────── */

function getSigField(field: string): string | null {
  const m = field.match(/^(.+)_slope$/);
  if (m) return `${m[1]}_significant`;
  return null;
}

/* ── Component ─────────────────────────────────────────────────────────── */

interface Props {
  data: HazardData;
  coastline: number[][][];
}

export default function HazardCharacterizationMap({ data, coastline }: Props) {
  const [tab, setTab] = useState<AnalysisTab>('compound');
  const [metricIdx, setMetricIdx] = useState(0);
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [svgClientWidth, setSvgClientWidth] = useState(600);
  const [showSigOnly, setShowSigOnly] = useState(false);
  const svgRef = useRef<SVGSVGElement>(null);

  const metrics = METRICS[tab];
  const metric = metrics[metricIdx] || metrics[0];
  const ramp = getRamp(tab, metric.field);
  const sigField = getSigField(metric.field);

  const { values, sig, vMin, vMax, isMonth, isDiverging } = useMemo(() => {
    const isM = metric.unit === 'month';
    const isDiv = ramp === RAMP_DIVERGING;
    const vals = data.grid_points.map(gp => {
      const v = gp[metric.field];
      return typeof v === 'number' ? v : null;
    });
    const sigVals = sigField ? data.grid_points.map(gp => gp[sigField] === true) : null;
    const valid = vals.filter((v): v is number => v !== null);
    let mn = valid.length > 0 ? Math.min(...valid) : 0;
    let mx = valid.length > 0 ? Math.max(...valid) : 1;
    if (isM) { mn = 1; mx = 12; }
    if (isDiv && mn < 0 && mx > 0) {
      const abs = Math.max(Math.abs(mn), Math.abs(mx));
      mn = -abs; mx = abs;
    }
    return { values: vals, sig: sigVals, vMin: mn, vMax: mx, isMonth: isM, isDiverging: isDiv };
  }, [data.grid_points, metric.field, sigField, ramp, metric.unit]);

  const svgWidth = 600;
  const svgHeight = svgWidth / ASPECT;

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    setSvgClientWidth(rect.width);
    setTooltipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  }, []);

  const coastlinePaths = useMemo(() => {
    return coastline.map(seg => {
      const points = seg.map(([lon, lat]) => {
        const { x, y } = project(lon, lat, svgWidth, svgHeight);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      });
      return `M${points.join('L')}`;
    }).join(' ');
  }, [svgWidth, svgHeight, coastline]);

  const hoveredPoint = hoveredIdx !== null ? data.grid_points[hoveredIdx] : null;

  return (
    <div className="space-y-6">
      {/* ── Analysis tabs ─────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-1 rounded-lg border border-gray-200 bg-gray-50 p-1">
        {(Object.keys(TAB_LABELS) as AnalysisTab[]).map(t => (
          <button
            key={t}
            onClick={() => {
              setTab(t);
              setMetricIdx(0);
              setShowSigOnly(false);
            }}
            className={`rounded-md px-3 py-2 text-xs font-medium transition-colors ${
              tab === t
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            style={tab === t ? { borderBottom: `2px solid ${TAB_COLORS[t]}` } : undefined}
          >
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      {/* ── Metric selector + significance toggle ─────────────────────── */}
      <div className="flex flex-wrap items-end gap-4">
        <div className="flex-1 min-w-[200px]">
          <label className="mb-1.5 block text-xs font-semibold text-gray-500 uppercase tracking-wide">
            Layer
          </label>
          <select
            value={metricIdx}
            onChange={e => setMetricIdx(Number(e.target.value))}
            className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-700"
          >
            {metrics.map((m, i) => (
              <option key={m.key} value={i}>
                {m.label} ({m.unit})
              </option>
            ))}
          </select>
        </div>
        {sigField && (
          <label className="flex items-center gap-2 pb-1 cursor-pointer">
            <input
              type="checkbox"
              checked={showSigOnly}
              onChange={e => setShowSigOnly(e.target.checked)}
              className="rounded border-gray-300 text-blue-600"
            />
            <span className="text-xs text-gray-600">Show significant only (α=0.05)</span>
          </label>
        )}
      </div>

      {/* ── Map ───────────────────────────────────────────────────────── */}
      <div className="relative rounded-xl border border-gray-200 bg-gray-50 overflow-hidden">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full"
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoveredIdx(null)}
        >
          <rect width={svgWidth} height={svgHeight} fill="#f8fafc" />

          {/* Graticule */}
          {Array.from({ length: 7 }, (_, i) => MAP_BOUNDS.lonMin + 5 + i * 5)
            .filter(lon => lon < MAP_BOUNDS.lonMax)
            .map(lon => {
              const { x: x1 } = project(lon, MAP_BOUNDS.latMax, svgWidth, svgHeight);
              return (
                <g key={`grat-lon-${lon}`}>
                  <line x1={x1} y1={0} x2={x1} y2={svgHeight} stroke="#e2e8f0" strokeWidth={0.5} />
                  <text x={x1} y={svgHeight - 4} textAnchor="middle" className="fill-gray-400" style={{ fontSize: '8px' }}>
                    {lon}°W
                  </text>
                </g>
              );
            })}
          {Array.from({ length: 9 }, (_, i) => MAP_BOUNDS.latMin + 5 + i * 5)
            .filter(lat => lat < MAP_BOUNDS.latMax)
            .map(lat => {
              const { y: y1 } = project(MAP_BOUNDS.lonMin, lat, svgWidth, svgHeight);
              return (
                <g key={`grat-lat-${lat}`}>
                  <line x1={0} y1={y1} x2={svgWidth} y2={y1} stroke="#e2e8f0" strokeWidth={0.5} />
                  <text x={4} y={y1 - 3} className="fill-gray-400" style={{ fontSize: '8px' }}>
                    {Math.abs(lat)}°{lat < 0 ? 'S' : 'N'}
                  </text>
                </g>
              );
            })}

          {/* Coastline */}
          <path d={coastlinePaths} fill="none" stroke="#94a3b8" strokeWidth={0.8} />

          {/* Grid points */}
          {data.grid_points.map((gp, i) => {
            const val = values[i];
            if (val === null) return null;
            if (showSigOnly && sig && !sig[i]) return null;
            const { x, y } = project(gp.lon, gp.lat, svgWidth, svgHeight);
            const t = vMax > vMin ? (val - vMin) / (vMax - vMin) : 0.5;
            const color = interpolateColor(ramp, t);
            const isHovered = hoveredIdx === i;
            return (
              <circle
                key={i}
                cx={x}
                cy={y}
                r={isHovered ? 5 : 3.2}
                fill={color}
                stroke={isHovered ? '#1e293b' : '#ffffff'}
                strokeWidth={isHovered ? 1.5 : 0.5}
                opacity={0.9}
                onMouseEnter={() => setHoveredIdx(i)}
                style={{ cursor: 'pointer', transition: 'r 0.1s' }}
              />
            );
          })}
        </svg>

        {/* Tooltip */}
        {hoveredPoint && hoveredIdx !== null && (
          <div
            className="pointer-events-none absolute z-10 min-w-[220px] rounded-lg border border-gray-200 bg-white p-3 shadow-lg"
            style={{
              left: Math.max(8, Math.min(tooltipPos.x + 12, svgClientWidth - 240)),
              top: tooltipPos.y - 10,
              transform: 'translateY(-100%)',
            }}
          >
            <div className="mb-1.5 text-[10px] font-semibold text-gray-400 uppercase tracking-wide">
              {hoveredPoint.lat.toFixed(2)}°{(hoveredPoint.lat as number) < 0 ? 'S' : 'N'},{' '}
              {Math.abs(hoveredPoint.lon as number).toFixed(2)}°W
              {hoveredPoint.municipality && (
                <span className="ml-1 normal-case text-gray-500"> · {hoveredPoint.municipality as string}</span>
              )}
            </div>
            <div className="space-y-1 text-xs text-gray-700">
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: TAB_COLORS[tab] }} />
                <span className="font-medium">{TAB_LABELS[tab]}</span>
              </div>
              <div className="border-t border-gray-100 pt-1 space-y-0.5">
                {metrics.map(m => {
                  const v = hoveredPoint[m.field];
                  return (
                    <div key={m.key} className={m.key === metric.key ? 'font-semibold' : ''}>
                      {m.label}: <span className="font-mono">{fmtVal(v as number | null, m.unit)}</span>
                      {m.unit !== 'month' && m.unit !== '–' && m.unit !== 'events' && m.unit !== 'storms' && (
                        <span className="text-gray-400 ml-0.5">{m.unit}</span>
                      )}
                    </div>
                  );
                })}
              </div>
              {sigField && sig && (
                <div className="border-t border-gray-100 pt-1 text-[10px]">
                  Trend significant (α=0.05): <span className={sig[hoveredIdx] ? 'text-green-600 font-semibold' : 'text-gray-400'}>{sig[hoveredIdx] ? 'Yes' : 'No'}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Color legend */}
        <div className="absolute bottom-4 right-4 rounded-lg border border-gray-200 bg-white/95 backdrop-blur-sm px-3 py-2">
          <div className="mb-1 text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
            {metric.label}
          </div>
          {isMonth ? (
            <>
              <div
                className="h-3 w-full rounded-sm"
                style={{ background: `linear-gradient(to right, ${ramp.join(', ')})` }}
              />
              <div className="mt-1 flex justify-between text-[9px] text-gray-500 font-medium">
                <span style={{ color: '#d73027' }}>DJF</span>
                <span style={{ color: '#fec44f' }}>MAM</span>
                <span style={{ color: '#4575b4' }}>JJA</span>
                <span style={{ color: '#1a9850' }}>SON</span>
                <span style={{ color: '#a50026' }}>D</span>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center gap-1">
                <span className="text-[10px] text-gray-500 font-mono w-12 text-right">
                  {fmtVal(vMin, metric.unit)}
                </span>
                <div
                  className="h-3 w-24 rounded-sm"
                  style={{ background: `linear-gradient(to right, ${ramp.join(', ')})` }}
                />
                <span className="text-[10px] text-gray-500 font-mono w-12">
                  {fmtVal(vMax, metric.unit)}
                </span>
              </div>
              {isDiverging && (
                <div className="mt-0.5 text-center text-[9px] text-gray-400">← decrease · increase →</div>
              )}
            </>
          )}
        </div>
      </div>

      {/* ── Summary stats bar ─────────────────────────────────────────── */}
      {tab === 'compound' && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label="Total compound events" value={sumField(data.grid_points, 'compound_count_total').toLocaleString()} />
          <StatCard label="Mean annual rate" value={(avgField(data.grid_points, 'compound_count_annual_mean')).toFixed(1) + ' yr⁻¹'} />
          <StatCard label="Mean overlap" value={(avgField(data.grid_points, 'compound_mean_overlap_duration')).toFixed(1) + ' days'} />
          <StatCard label="Mean intensity (norm)" value={(avgField(data.grid_points, 'compound_mean_intensity_norm')).toFixed(3)} />
        </div>
      )}
      {tab === 'eva' && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <StatCard label="Hₛ 10-yr RL (median)" value={medianField(data.grid_points, 'hs_rl_10yr').toFixed(2) + ' m'} />
          <StatCard label="Hₛ 50-yr RL (median)" value={medianField(data.grid_points, 'hs_rl_50yr').toFixed(2) + ' m'} />
          <StatCard label="SSH 10-yr RL (median)" value={medianField(data.grid_points, 'ssh_total_rl_10yr').toFixed(2) + ' m'} />
        </div>
      )}
      {tab === 'dependence' && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatCard label="Median τ" value={medianField(data.grid_points, 'tau').toFixed(3)} />
          <StatCard label="Median ρ" value={medianField(data.grid_points, 'rho').toFixed(3)} />
          <StatCard label="Median χ" value={medianField(data.grid_points, 'chi').toFixed(3)} />
          <StatCard label="Median χ̄" value={medianField(data.grid_points, 'chi_bar').toFixed(3)} />
        </div>
      )}
      {tab === 'trends' && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {(() => {
            const sigFieldForCount = 'annual_hs_count_significant';
            const nSig = data.grid_points.filter(g => g[sigFieldForCount] === true).length;
            const nSigSsh = data.grid_points.filter(g => g['annual_ssh_total_count_significant'] === true).length;
            const nSigComp = data.grid_points.filter(g => g['annual_compound_count_significant'] === true).length;
            return (
              <>
                <StatCard label="Hₛ count — significant" value={`${nSig} / ${data.grid_points.length}`} />
                <StatCard label="SSH count — significant" value={`${nSigSsh} / ${data.grid_points.length}`} />
                <StatCard label="Compound count — significant" value={`${nSigComp} / ${data.grid_points.length}`} />
              </>
            );
          })()}
        </div>
      )}

      {/* ── Description ───────────────────────────────────────────────── */}
      {metric.description && (
        <p className="text-xs text-gray-500 italic">{metric.description}</p>
      )}
    </div>
  );
}

/* ── Small helpers ─────────────────────────────────────────────────────── */

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3">
      <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-wide mb-1">
        {label}
      </div>
      <div className="text-lg font-bold text-gray-900">{value}</div>
    </div>
  );
}

function sumField(gps: GridPoint[], field: string): number {
  return gps.reduce((s, g) => s + (typeof g[field] === 'number' ? (g[field] as number) : 0), 0);
}

function avgField(gps: GridPoint[], field: string): number {
  const vals = gps.map(g => g[field]).filter((v): v is number => typeof v === 'number');
  return vals.length > 0 ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
}

function medianField(gps: GridPoint[], field: string): number {
  const vals = gps.map(g => g[field]).filter((v): v is number => typeof v === 'number').sort((a, b) => a - b);
  if (vals.length === 0) return 0;
  const mid = Math.floor(vals.length / 2);
  return vals.length % 2 !== 0 ? vals[mid] : (vals[mid - 1] + vals[mid]) / 2;
}
