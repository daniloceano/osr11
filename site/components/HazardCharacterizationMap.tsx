'use client';

import { useCallback, useMemo, useRef, useState } from 'react';
import {
  DiscreteLegend,
  MAP_COLORS,
  MONTH_NAMES,
  MapFrame,
  StatCard,
  buildBasemapPaths,
  classIndex,
  decimalsFor,
  extentFromArray,
  formatValue,
  makeProjection,
  niceBreaks,
  symmetricBreaks,
} from './coastalMap';
import type {
  CoastalBasemap,
  CoastalHazardGeoJson,
  CoastalHazardMetadata,
} from './CoastalHazardMap';

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

const METRICS: Record<AnalysisTab, MetricDef[]> = {
  compound: [
    { key: 'count', label: 'Compound count (total)', unit: 'events', field: 'compound_count_total' },
    { key: 'annual', label: 'Compound count (annual mean)', unit: 'events yr⁻¹', field: 'compound_count_annual_mean' },
    { key: 'intensity', label: 'Mean normalized intensity', unit: 'dimensionless', field: 'compound_mean_intensity_norm' },
    { key: 'p95_int', label: 'P95 normalized intensity', unit: 'dimensionless', field: 'compound_p95_intensity_norm' },
    { key: 'overlap', label: 'Mean overlap duration', unit: 'days', field: 'compound_mean_overlap_duration' },
    { key: 'lag', label: 'Mean peak lag (Hₛ − SSH)', unit: 'days', field: 'compound_mean_peak_lag_days', description: 'Mean of (Hₛ peak date − SSH_total peak date): positive = Hₛ peaks after SSH_total (lags); negative = Hₛ peaks first' },
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
    { key: 'tau', label: "Kendall's τ", unit: 'dimensionless', field: 'tau', description: 'Rank correlation between Hₛ and SSH peaks in compound events' },
    { key: 'rho', label: "Spearman's ρ", unit: 'dimensionless', field: 'rho' },
    { key: 'chi', label: 'Extremal χ', unit: 'dimensionless', field: 'chi', description: 'Asymptotic tail dependence: χ > 0 means extremes tend to co-occur in the limit' },
    { key: 'chi_bar', label: 'Extremal χ̄', unit: 'dimensionless', field: 'chi_bar', description: 'Sub-asymptotic association: informative when χ ≈ 0; higher χ̄ = stronger residual tail dependence' },
    { key: 'n_pairs', label: 'Compound pairs', unit: 'events', field: 'n_compound_pairs' },
  ],
};

const CLASS_COUNT = 8;

function isDiverging(field: string): boolean {
  return field.includes('slope') || field.includes('lag');
}

function isMonth(field: string): boolean {
  return field.includes('peak_month');
}

function significanceField(field: string): string | null {
  const match = field.match(/^(.+)_slope$/);
  return match ? `${match[1]}_significant` : null;
}

/* ── Component ─────────────────────────────────────────────────────────── */

interface Props {
  data: HazardData;
  segments: CoastalHazardGeoJson;
  coastalMetadata: CoastalHazardMetadata;
  basemap: CoastalBasemap;
}

export default function HazardCharacterizationMap({
  data,
  segments,
  coastalMetadata,
  basemap,
}: Props) {
  const [tab, setTab] = useState<AnalysisTab>('compound');
  const [metricIdx, setMetricIdx] = useState(0);
  const [showSigOnly, setShowSigOnly] = useState(false);
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [containerWidth, setContainerWidth] = useState(460);
  const mapRef = useRef<HTMLDivElement>(null);

  const metrics = METRICS[tab];
  const metric = metrics[metricIdx] ?? metrics[0];
  const sigField = significanceField(metric.field);
  const palettes = coastalMetadata.palettes;

  const projection = useMemo(
    () => makeProjection(extentFromArray(coastalMetadata.map_extent), 420),
    [coastalMetadata.map_extent],
  );
  const basemapPaths = useMemo(
    () => buildBasemapPaths(basemap, projection),
    [basemap, projection],
  );
  const segmentPaths = useMemo(
    () => segments.features.map((feature) => projection.lineToPath(feature.geometry.coordinates)),
    [segments.features, projection],
  );

  /** Value of the selected metric at the grid point behind each coast segment. */
  const segmentValues = useMemo(
    () =>
      segments.features.map((feature) => {
        const point = data.grid_points[feature.properties.metrics_index];
        const value = point?.[metric.field];
        return typeof value === 'number' && Number.isFinite(value) ? value : null;
      }),
    [segments.features, data.grid_points, metric.field],
  );

  const segmentSignificant = useMemo(() => {
    if (!sigField) return null;
    return segments.features.map((feature) => {
      const point = data.grid_points[feature.properties.metrics_index];
      return point?.[sigField] === true;
    });
  }, [segments.features, data.grid_points, sigField]);

  const scale = useMemo(() => {
    const values = segmentValues.filter((value): value is number => value !== null);
    const min = values.length ? Math.min(...values) : 0;
    const max = values.length ? Math.max(...values) : 1;
    if (isMonth(metric.field)) {
      return {
        boundaries: Array.from({ length: 13 }, (_, index) => index + 1),
        colors: palettes.month,
        decimals: 0,
        monthLabels: true,
      };
    }
    if (isDiverging(metric.field)) {
      const boundaries = symmetricBreaks(min, max, CLASS_COUNT);
      return {
        boundaries,
        colors: palettes.diverging.slice(0, boundaries.length - 1),
        decimals: decimalsFor(boundaries),
        monthLabels: false,
      };
    }
    const boundaries = niceBreaks(min, max, CLASS_COUNT);
    const colors = boundaries.length - 1 <= palettes.sequential.length
      ? palettes.sequential.slice(0, boundaries.length - 1)
      : palettes.sequential;
    return {
      boundaries: boundaries.slice(0, colors.length + 1),
      colors,
      decimals: decimalsFor(boundaries),
      monthLabels: false,
    };
  }, [segmentValues, metric.field, palettes]);

  const stats = useMemo(() => {
    const values = segmentValues
      .filter((value): value is number => value !== null)
      .sort((a, b) => a - b);
    if (!values.length) return { count: 0, min: null, max: null, mean: null, median: null };
    const mid = Math.floor(values.length / 2);
    return {
      count: values.length,
      min: values[0],
      max: values[values.length - 1],
      mean: values.reduce((sum, value) => sum + value, 0) / values.length,
      median: values.length % 2 ? values[mid] : (values[mid - 1] + values[mid]) / 2,
    };
  }, [segmentValues]);

  const handleMouseMove = useCallback((event: React.MouseEvent) => {
    if (!mapRef.current) return;
    const rect = mapRef.current.getBoundingClientRect();
    setContainerWidth(rect.width);
    setTooltipPos({ x: event.clientX - rect.left, y: event.clientY - rect.top });
  }, []);

  const hoveredFeature = hoveredIdx !== null ? segments.features[hoveredIdx] : null;
  const hoveredPoint = hoveredFeature ? data.grid_points[hoveredFeature.properties.metrics_index] : null;

  const formatMetric = (value: unknown, unit: string, decimals: number) => {
    if (typeof value !== 'number' || !Number.isFinite(value)) return 'No data';
    if (unit === 'month') return MONTH_NAMES[Math.round(value) - 1] ?? '?';
    if (unit === 'events' || unit === 'storms') return Math.round(value).toLocaleString();
    if (unit.includes('yr⁻¹ yr⁻¹')) return value.toExponential(2);
    return formatValue(value, decimals);
  };

  return (
    <div className="space-y-5">
      {/* ── Analysis tabs ─────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-1 rounded-lg border border-gray-200 bg-gray-50 p-1">
        {(Object.keys(TAB_LABELS) as AnalysisTab[]).map((entry) => (
          <button
            key={entry}
            type="button"
            onClick={() => {
              setTab(entry);
              setMetricIdx(0);
              setShowSigOnly(false);
              setHoveredIdx(null);
            }}
            aria-pressed={tab === entry}
            className={`rounded-md px-3 py-2 text-xs font-medium transition-colors ${
              tab === entry ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
            style={tab === entry ? { borderBottom: '2px solid #2563eb' } : undefined}
          >
            {TAB_LABELS[entry]}
          </button>
        ))}
      </div>

      {/* ── Metric selector ───────────────────────────────────────────── */}
      <div className="flex flex-wrap items-end gap-4">
        <div className="min-w-[220px] flex-1">
          <label
            htmlFor="hazard-metric"
            className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-gray-500"
          >
            Metric
          </label>
          <select
            id="hazard-metric"
            value={metricIdx}
            onChange={(event) => setMetricIdx(Number(event.target.value))}
            className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-700"
          >
            {metrics.map((entry, index) => (
              <option key={entry.key} value={index}>
                {entry.label} ({entry.unit})
              </option>
            ))}
          </select>
        </div>
        {sigField && (
          <label className="flex cursor-pointer items-center gap-2 pb-1">
            <input
              type="checkbox"
              checked={showSigOnly}
              onChange={(event) => setShowSigOnly(event.target.checked)}
              className="rounded border-gray-300 text-blue-600"
            />
            <span className="text-xs text-gray-600">Show significant only (α = 0.05)</span>
          </label>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,460px)_minmax(0,1fr)]">
        {/* ── Map ───────────────────────────────────────────────────── */}
        <div
          ref={mapRef}
          className="relative mx-auto w-full max-w-[460px] self-start overflow-hidden rounded-xl border border-gray-200"
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoveredIdx(null)}
        >
          <MapFrame
            projection={projection}
            basemapPaths={basemapPaths}
            ariaLabel={`${metric.label} along the Brazilian coast, in ${metric.unit}`}
            overlay={
              <>
                {segments.features.map((feature, index) => {
                  const value = segmentValues[index];
                  if (value === null) return null;
                  if (showSigOnly && segmentSignificant && !segmentSignificant[index]) return null;
                  const color = scale.colors[classIndex(value, scale.boundaries)];
                  const isHovered = hoveredIdx === index;
                  return (
                    <path
                      key={`${feature.properties.source_grid_index}-${index}`}
                      d={segmentPaths[index]}
                      fill="none"
                      stroke={isHovered ? MAP_COLORS.highlight : color}
                      strokeWidth={isHovered ? 4.4 : 3}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      onMouseEnter={() => setHoveredIdx(index)}
                      style={{ cursor: 'pointer' }}
                    />
                  );
                })}
              </>
            }
          />

          {hoveredFeature && hoveredPoint && (
            <div
              className="pointer-events-none absolute z-10 w-[250px] rounded-lg border border-gray-200 bg-white p-3 shadow-lg"
              style={{
                left: Math.max(6, Math.min(tooltipPos.x + 12, containerWidth - 260)),
                top: tooltipPos.y - 10,
                transform: 'translateY(-100%)',
              }}
            >
              <div className="mb-1.5 text-[11px] font-bold text-gray-900">
                {hoveredFeature.properties.municipality_name ?? 'Municipality not identified'}
                {hoveredFeature.properties.municipality_state
                  ? ` · ${hoveredFeature.properties.municipality_state}`
                  : ''}
              </div>
              <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-gray-400">
                Grid point {Math.abs(hoveredFeature.properties.source_latitude).toFixed(2)}°
                {hoveredFeature.properties.source_latitude < 0 ? 'S' : 'N'},{' '}
                {Math.abs(hoveredFeature.properties.source_longitude).toFixed(2)}°W
              </div>
              <div className="space-y-0.5 border-t border-gray-100 pt-1 text-xs text-gray-700">
                {metrics.map((entry) => (
                  <div key={entry.key} className={entry.key === metric.key ? 'font-semibold' : ''}>
                    {entry.label}:{' '}
                    <span className="font-mono">
                      {formatMetric(hoveredPoint[entry.field], entry.unit, 2)}
                    </span>
                    {entry.unit !== 'month' && (
                      <> <span className="text-gray-400">{entry.unit}</span></>
                    )}
                  </div>
                ))}
                {sigField && segmentSignificant && (
                  <div className="border-t border-gray-100 pt-1 text-[10px]">
                    Trend significant (α = 0.05):{' '}
                    <span
                      className={
                        segmentSignificant[hoveredIdx as number]
                          ? 'font-semibold text-green-600'
                          : 'text-gray-400'
                      }
                    >
                      {segmentSignificant[hoveredIdx as number] ? 'Yes' : 'No'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* ── Legend and context ────────────────────────────────────── */}
        <div className="min-w-0 space-y-4">
          <DiscreteLegend
            title={metric.label}
            unit={metric.unit}
            boundaries={scale.boundaries}
            colors={scale.colors}
            decimals={scale.decimals}
            monthLabels={scale.monthLabels}
            note={
              <>
                {metric.description && (
                  <p className="mt-3 text-[11px] leading-relaxed text-gray-500">
                    {metric.description}
                  </p>
                )}
                <p className="mt-2 text-[11px] leading-relaxed text-gray-500">
                  Class limits are rounded to cover the observed range of this metric across the
                  coast. The values themselves come straight from the Step 3 catalog at the native
                  ocean grid point behind each coastal segment.
                </p>
              </>
            }
          />

          <div>
            <p className="mb-2 text-[11px] text-gray-500">
              Statistics over the {stats.count.toLocaleString()} coastal polylines, in{' '}
              <span className="font-semibold text-gray-700">{metric.unit}</span>.
            </p>
            <div className="grid grid-cols-2 gap-3">
              <StatCard label="Minimum" value={formatMetric(stats.min, metric.unit, scale.decimals)} />
              <StatCard label="Maximum" value={formatMetric(stats.max, metric.unit, scale.decimals)} />
              <StatCard label="Median" value={formatMetric(stats.median, metric.unit, scale.decimals)} />
              <StatCard label="Mean" value={formatMetric(stats.mean, metric.unit, scale.decimals)} />
            </div>
          </div>

          <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 text-[11px] leading-relaxed text-gray-600">
            <p>
              <strong className="text-gray-800">Same coastal transposition.</strong> These metrics
              are calculated at the {data.metadata.n_grid_points} native ocean grid points, exactly
              like the Hazard Index above, and are drawn on the coast with the same rule: the
              Natural Earth coastline is split into segments of at most{' '}
              {(coastalMetadata.coastal_projection.maximum_segment_length_m / 1000).toFixed(0)} km
              and each segment shows the value of its nearest grid point. Nothing is interpolated
              or recalculated along the coast.
            </p>
            <p className="mt-2">
              Hovering a segment reports its nearest coastal municipality — the unit that receives
              these metrics in the risk integration — together with every metric of the selected
              group at that grid point.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
