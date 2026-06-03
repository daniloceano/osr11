'use client';

import { useState, useCallback, useMemo, useRef } from 'react';

/* ── Types ─────────────────────────────────────────────────────────────── */

export interface GridPoint {
  lat: number;
  lon: number;
  thr_hs: number;
  thr_ssh: number;
  hs_only_count_total: number;
  hs_only_count_annual_mean: number;
  ssh_only_count_total: number;
  ssh_only_count_annual_mean: number;
  compound_count_total: number;
  compound_count_annual_mean: number;
  hs_only_mean_peak: number | null;
  hs_only_p95_peak: number | null;
  hs_only_max_peak: number | null;
  ssh_only_mean_peak: number | null;
  ssh_only_p95_peak: number | null;
  ssh_only_max_peak: number | null;
  compound_mean_intensity_norm: number | null;
  compound_p95_intensity_norm: number | null;
  compound_max_intensity_norm: number | null;
  compound_mean_hs_peak_norm: number | null;
  compound_mean_ssh_peak_norm: number | null;
  compound_mean_peak_hs: number | null;
  compound_mean_peak_ssh_total: number | null;
  // zos diagnostic layer (no tide)
  zos_raw_thr: number | null;
  zos_raw_count_total: number;
  zos_raw_count_annual_mean: number;
  zos_raw_mean_peak: number | null;
  zos_raw_p95_peak: number | null;
  zos_raw_max_peak: number | null;
}

export interface StormMapsData {
  metadata: {
    period: string;
    n_years: number;
    n_grid_points: number;
    compound_definition: string;
    hs_only_definition: string;
    ssh_only_definition: string;
    compound_intensity_definition: string;
    compound_intensity_normalization?: {
      hs_ref_low: number;
      hs_ref_high: number;
      ssh_ref_low: number;
      ssh_ref_high: number;
    };
    n_hs_only_total: number;
    n_ssh_only_total: number;
    n_compound_total: number;
    zos_raw_definition?: string;
    n_zos_raw_total?: number;
  };
  grid_points: GridPoint[];
}

type EventClass = 'hs_only' | 'ssh_only' | 'compound' | 'zos_raw';
type MetricGroup = 'occurrence' | 'intensity';

interface MetricDef {
  key: string;
  label: string;
  unit: string;
  field: keyof GridPoint;
}

/* ── Metric definitions ────────────────────────────────────────────────── */

const OCCURRENCE_METRICS: Record<EventClass, MetricDef[]> = {
  hs_only: [
    { key: 'total', label: 'Total count', unit: 'storms', field: 'hs_only_count_total' },
    { key: 'annual', label: 'Annual mean', unit: 'storms yr⁻¹', field: 'hs_only_count_annual_mean' },
  ],
  ssh_only: [
    { key: 'total', label: 'Total count', unit: 'storms', field: 'ssh_only_count_total' },
    { key: 'annual', label: 'Annual mean', unit: 'storms yr⁻¹', field: 'ssh_only_count_annual_mean' },
  ],
  compound: [
    { key: 'total', label: 'Total count', unit: 'events', field: 'compound_count_total' },
    { key: 'annual', label: 'Annual mean', unit: 'events yr⁻¹', field: 'compound_count_annual_mean' },
  ],
  zos_raw: [
    { key: 'total', label: 'Total count', unit: 'storms', field: 'zos_raw_count_total' },
    { key: 'annual', label: 'Annual mean', unit: 'storms yr⁻¹', field: 'zos_raw_count_annual_mean' },
  ],
};

const INTENSITY_METRICS: Record<EventClass, MetricDef[]> = {
  hs_only: [
    { key: 'mean', label: 'Mean peak Hₛ', unit: 'm', field: 'hs_only_mean_peak' },
    { key: 'p95', label: '95th-pctl peak Hₛ', unit: 'm', field: 'hs_only_p95_peak' },
    { key: 'max', label: 'Maximum peak Hₛ', unit: 'm', field: 'hs_only_max_peak' },
  ],
  ssh_only: [
    { key: 'mean', label: 'Mean peak SSH_total', unit: 'm', field: 'ssh_only_mean_peak' },
    { key: 'p95', label: '95th-pctl peak SSH_total', unit: 'm', field: 'ssh_only_p95_peak' },
    { key: 'max', label: 'Maximum peak SSH_total', unit: 'm', field: 'ssh_only_max_peak' },
  ],
  compound: [
    { key: 'mean_norm', label: 'Mean normalized intensity', unit: '[0–1]', field: 'compound_mean_intensity_norm' },
    { key: 'p95_norm', label: '95th-pctl normalized intensity', unit: '[0–1]', field: 'compound_p95_intensity_norm' },
    { key: 'max_norm', label: 'Max normalized intensity', unit: '[0–1]', field: 'compound_max_intensity_norm' },
    { key: 'mean_hs_norm', label: 'Mean Hₛ component (norm)', unit: '[0–1]', field: 'compound_mean_hs_peak_norm' },
    { key: 'mean_ssh_norm', label: 'Mean SSH component (norm)', unit: '[0–1]', field: 'compound_mean_ssh_peak_norm' },
  ],
  zos_raw: [
    { key: 'mean', label: 'Mean peak zos', unit: 'm', field: 'zos_raw_mean_peak' },
    { key: 'p95', label: '95th-pctl peak zos', unit: 'm', field: 'zos_raw_p95_peak' },
    { key: 'max', label: 'Maximum peak zos', unit: 'm', field: 'zos_raw_max_peak' },
  ],
};

/* ── Color scales ──────────────────────────────────────────────────────── */

/* Color ramps keyed by metric type, not event class */
const COLOR_RAMPS: Record<MetricGroup, string[]> = {
  occurrence: [
    '#ffffcc','#ffeda0','#fed976','#feb24c','#fd8d3c',
    '#fc4e2a','#e31a1c','#bd0026','#800026','#4a0066',
  ],
  intensity: [
    '#E6F7FF','#A6DEF7','#4CBFE6','#0099D1','#007AB8',
    '#1AA64C','#8CCC00','#E6CC00','#FF8000','#D90000',
  ],
};

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

/* ── Projection (Equirectangular) ──────────────────────────────────────── */

const MAP_BOUNDS = { lonMin: -56, lonMax: -27, latMin: -36, latMax: 7 };
const ASPECT = (MAP_BOUNDS.lonMax - MAP_BOUNDS.lonMin) / (MAP_BOUNDS.latMax - MAP_BOUNDS.latMin);

function project(lon: number, lat: number, width: number, height: number) {
  const x = ((lon - MAP_BOUNDS.lonMin) / (MAP_BOUNDS.lonMax - MAP_BOUNDS.lonMin)) * width;
  const y = ((MAP_BOUNDS.latMax - lat) / (MAP_BOUNDS.latMax - MAP_BOUNDS.latMin)) * height;
  return { x, y };
}

/* ── Class labels ──────────────────────────────────────────────────────── */

const CLASS_LABELS: Record<EventClass, string> = {
  hs_only: 'Hₛ only',
  ssh_only: 'SSH_total only',
  compound: 'Compound',
  zos_raw: 'zos (no tide)',
};

const CLASS_COLORS: Record<EventClass, string> = {
  hs_only: '#3182bd',
  ssh_only: '#2ca25f',
  compound: '#756bb1',
  zos_raw: '#d95f02',
};

/* ── Component ─────────────────────────────────────────────────────────── */

interface Props {
  data: StormMapsData;
  coastline: number[][][];
}

export default function CoastalStormMap({ data, coastline }: Props) {
  const [eventClass, setEventClass] = useState<EventClass>('compound');
  const [metricGroup, setMetricGroup] = useState<MetricGroup>('occurrence');
  const [metricIdx, setMetricIdx] = useState(0);
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [svgClientWidth, setSvgClientWidth] = useState(600);
  const svgRef = useRef<SVGSVGElement>(null);

  const metrics = metricGroup === 'occurrence'
    ? OCCURRENCE_METRICS[eventClass]
    : INTENSITY_METRICS[eventClass];

  const currentMetric = metrics[metricIdx] || metrics[0];

  // Compute values and color range
  const { values, vMin, vMax, ramp } = useMemo(() => {
    const vals = data.grid_points.map(gp => {
      const v = gp[currentMetric.field];
      return typeof v === 'number' ? v : null;
    });
    const valid = vals.filter((v): v is number => v !== null);
    const mn = valid.length > 0 ? Math.min(...valid) : 0;
    const mx = valid.length > 0 ? Math.max(...valid) : 1;
    return { values: vals, vMin: mn, vMax: mx, ramp: COLOR_RAMPS[metricGroup] };
  }, [data.grid_points, currentMetric.field, metricGroup]);

  // SVG dimensions (responsive)
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
      {/* ── Controls ──────────────────────────────────────────────────── */}
      <div className="grid gap-4 md:grid-cols-3">
        {/* Event class selector */}
        <div>
          <label className="mb-1.5 block text-xs font-semibold text-gray-500 uppercase tracking-wide">
            Event Class
          </label>
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            {(['hs_only', 'ssh_only', 'compound'] as EventClass[]).map(cls => (
              <button
                key={cls}
                onClick={() => {
                  setEventClass(cls);
                  setMetricIdx(0);
                }}
                className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${
                  eventClass === cls
                    ? 'text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
                style={eventClass === cls ? { backgroundColor: CLASS_COLORS[cls] } : undefined}
              >
                {CLASS_LABELS[cls]}
              </button>
            ))}
            <div className="w-px bg-gray-300" />
            <button
              onClick={() => {
                setEventClass('zos_raw');
                setMetricIdx(0);
              }}
              className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${
                eventClass === 'zos_raw'
                  ? 'text-white'
                  : 'bg-gray-50 text-gray-500 hover:bg-gray-100'
              }`}
              style={eventClass === 'zos_raw' ? { backgroundColor: CLASS_COLORS.zos_raw } : undefined}
              title="Diagnostic layer — not the canonical sea-level analysis"
            >
              {CLASS_LABELS.zos_raw}
              <span className="ml-1 text-[8px] opacity-70">diag.</span>
            </button>
          </div>
        </div>

        {/* Metric group selector */}
        <div>
          <label className="mb-1.5 block text-xs font-semibold text-gray-500 uppercase tracking-wide">
            Metric Type
          </label>
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            {(['occurrence', 'intensity'] as MetricGroup[]).map(mg => (
              <button
                key={mg}
                onClick={() => {
                  setMetricGroup(mg);
                  setMetricIdx(0);
                }}
                className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${
                  metricGroup === mg
                    ? 'bg-gray-900 text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                {mg.charAt(0).toUpperCase() + mg.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Specific metric selector */}
        <div>
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
          {/* Ocean background */}
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
            className="pointer-events-none absolute z-10 min-w-[200px] rounded-lg border border-gray-200 bg-white p-3 shadow-lg"
            style={{
              left: Math.max(8, Math.min(tooltipPos.x + 12, svgClientWidth - 220)),
              top: tooltipPos.y - 10,
              transform: 'translateY(-100%)',
            }}
          >
            <div className="mb-1.5 text-[10px] font-semibold text-gray-400 uppercase tracking-wide">
              {hoveredPoint.lat.toFixed(2)}°{hoveredPoint.lat < 0 ? 'S' : 'N'},{' '}
              {Math.abs(hoveredPoint.lon).toFixed(2)}°W
            </div>
            <div className="space-y-1 text-xs text-gray-700">
              <div className="flex items-center gap-1.5">
                <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: CLASS_COLORS[eventClass] }} />
                <span className="font-medium">{CLASS_LABELS[eventClass]}</span>
              </div>
              <div className="border-t border-gray-100 pt-1">
                <span className="font-medium">{currentMetric.label}:</span>{' '}
                <span className="font-mono">
                  {values[hoveredIdx] !== null ? formatValue(values[hoveredIdx]!, currentMetric.unit) : 'N/A'}
                </span>
              </div>
              {/* Always show counts summary */}
              <div className="border-t border-gray-100 pt-1 text-[10px] text-gray-500 space-y-0.5">
                <div>Hₛ only: {hoveredPoint.hs_only_count_total} storms ({hoveredPoint.hs_only_count_annual_mean}/yr)</div>
                <div>SSH only: {hoveredPoint.ssh_only_count_total} storms ({hoveredPoint.ssh_only_count_annual_mean}/yr)</div>
                <div>Compound: {hoveredPoint.compound_count_total} events ({hoveredPoint.compound_count_annual_mean}/yr)</div>
                <div className="border-t border-dashed border-gray-200 mt-0.5 pt-0.5 italic text-gray-400">
                  zos (no tide): {hoveredPoint.zos_raw_count_total} storms ({hoveredPoint.zos_raw_count_annual_mean}/yr)
                </div>
              </div>
              <div className="text-[10px] text-gray-400">
                Thr: Hₛ = {hoveredPoint.thr_hs.toFixed(2)} m | SSH = {hoveredPoint.thr_ssh.toFixed(3)} m
                {hoveredPoint.zos_raw_thr != null && ` | zos = ${hoveredPoint.zos_raw_thr.toFixed(3)} m`}
              </div>
            </div>
          </div>
        )}

        {/* Color legend */}
        <div className="absolute bottom-4 right-4 rounded-lg border border-gray-200 bg-white/95 backdrop-blur-sm px-3 py-2">
          <div className="mb-1 text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
            {currentMetric.label}
          </div>
          <div className="flex items-center gap-1">
            <span className="text-[10px] text-gray-500 font-mono w-10 text-right">
              {formatValue(vMin, currentMetric.unit)}
            </span>
            <div
              className="h-3 w-24 rounded-sm"
              style={{
                background: `linear-gradient(to right, ${ramp.join(', ')})`,
              }}
            />
            <span className="text-[10px] text-gray-500 font-mono w-10">
              {formatValue(vMax, currentMetric.unit)}
            </span>
          </div>
          <div className="mt-0.5 text-center text-[9px] text-gray-400">{currentMetric.unit}</div>
        </div>
      </div>

      {/* ── Summary stats ─────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {(['hs_only', 'ssh_only', 'compound', 'zos_raw'] as EventClass[]).map(cls => {
          const totalKey = cls === 'hs_only' ? 'n_hs_only_total'
            : cls === 'ssh_only' ? 'n_ssh_only_total'
            : cls === 'zos_raw' ? 'n_zos_raw_total'
            : 'n_compound_total';
          const total = (data.metadata[totalKey as keyof typeof data.metadata] as number) ?? 0;
          return (
            <div
              key={cls}
              className={`rounded-lg border p-4 transition-colors ${
                eventClass === cls ? 'border-gray-400 bg-white shadow-sm' : 'border-gray-200 bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: CLASS_COLORS[cls] }} />
                <span className="text-xs font-semibold text-gray-600">{CLASS_LABELS[cls]}</span>
              </div>
              <div className="text-2xl font-bold text-gray-900">{total.toLocaleString()}</div>
              <div className="text-[10px] text-gray-500">
                total {cls === 'compound' ? 'events' : 'storms'} · {data.metadata.n_grid_points} grid points
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function formatValue(v: number, unit: string): string {
  if (unit.includes('yr')) return v.toFixed(1);
  if (unit === 'm') return v.toFixed(2);
  if (unit === '[0–1]') return v.toFixed(3);
  if (unit === 'storms' || unit === 'events') return Math.round(v).toString();
  return v.toFixed(2);
}
