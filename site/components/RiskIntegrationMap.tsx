'use client';

import { useCallback, useMemo, useRef, useState } from 'react';
import {
  DiscreteLegend,
  MAP_COLORS,
  MapFrame,
  StatCard,
  buildBasemapPaths,
  classIndex,
  extentFromArray,
  formatValue,
  makeProjection,
  type CoastalBasemap,
  type Position,
} from './coastalMap';

/* ── Types ─────────────────────────────────────────────────────────────── */

interface PolygonGeometry {
  type: 'Polygon';
  coordinates: Position[][];
}

interface MultiPolygonGeometry {
  type: 'MultiPolygon';
  coordinates: Position[][][];
}

interface RiskProperties {
  municipality_code?: string | null;
  municipality_name?: string | null;
  state?: string | null;
  state_name?: string | null;
  compound_c?: number | null;
  mean_overl?: number | null;
  mean_compo?: number | null;
  [key: string]: string | number | null | undefined;
}

interface RiskFeature {
  type: 'Feature';
  geometry: PolygonGeometry | MultiPolygonGeometry;
  properties: RiskProperties;
}

export interface RiskGeoJson {
  type: 'FeatureCollection';
  features: RiskFeature[];
}

interface LayerStats {
  count: number;
  min: number | null;
  max: number | null;
  mean: number | null;
  median: number | null;
}

interface RiskLayerMeta {
  key: string;
  label: string;
  short_label: string;
  unit: string;
  stage: 'normalized' | 'raw' | 'component' | 'input';
  group: string;
  description: string;
  actual_field: string;
  decimals: number;
  boundaries: number[];
  colors: string[];
  palette_source: string;
  stats: LayerStats;
}

export interface RiskMetadata {
  generated_at: string;
  source_path: string;
  source_crs: string;
  output_crs: string;
  scope?: string;
  feature_count: number;
  source_feature_count: number;
  map_extent: number[];
  available_layers: RiskLayerMeta[];
  audit_fields?: { note: string; fields: string[] };
  simplification?: {
    enabled: boolean;
    tolerance_degrees: number;
  };
}

interface Props {
  data: RiskGeoJson;
  metadata: RiskMetadata;
  basemap: CoastalBasemap;
}

const STAGE_BADGES: Record<RiskLayerMeta['stage'], { label: string; className: string }> = {
  normalized: { label: 'after normalization', className: 'border-blue-200 bg-blue-50 text-blue-700' },
  raw: { label: 'before normalization', className: 'border-amber-200 bg-amber-50 text-amber-800' },
  component: { label: 'hazard component', className: 'border-gray-200 bg-gray-50 text-gray-600' },
  input: { label: 'input layer', className: 'border-gray-200 bg-gray-50 text-gray-600' },
};

const DETAIL_FIELDS: { key: string; label: string; decimals: number }[] = [
  { key: 'SVI_Coast_2022', label: 'SVI_Coast_2022 (0–100)', decimals: 1 },
  { key: 'Hazard_Frequency', label: 'Hazard_Frequency (0–1)', decimals: 3 },
  { key: 'Hazard_Duration', label: 'Hazard_Duration (0–1)', decimals: 3 },
  { key: 'Hazard_Intensity', label: 'Hazard_Intensity (0–1)', decimals: 3 },
  { key: 'Hazard_Index_raw', label: 'Hazard_Index_raw (mean of the three)', decimals: 3 },
  { key: 'Hazard_Index', label: 'Hazard_Index (0–1)', decimals: 3 },
  { key: 'Risk_Hazard_raw', label: 'Risk_Hazard_raw (SVI × hazard)', decimals: 3 },
  { key: 'Risk_Hazard', label: 'Risk_Hazard (0–1)', decimals: 3 },
  { key: 'compound_c', label: 'compound_c (events)', decimals: 0 },
  { key: 'mean_overl', label: 'mean_overl (days)', decimals: 2 },
  { key: 'mean_compo', label: 'mean_compo (dimensionless)', decimals: 3 },
];

function numericValue(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

/* ── Component ─────────────────────────────────────────────────────────── */

export default function RiskIntegrationMap({ data, metadata, basemap }: Props) {
  const layers = metadata.available_layers;
  const [selectedKey, setSelectedKey] = useState<string>(
    layers.find((layer) => layer.key === 'Risk_Hazard')?.key ?? layers[0]?.key ?? '',
  );
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [containerWidth, setContainerWidth] = useState(460);
  const mapRef = useRef<HTMLDivElement>(null);

  const layer = layers.find((entry) => entry.key === selectedKey) ?? layers[0];

  const projection = useMemo(
    () => makeProjection(extentFromArray(metadata.map_extent), 420),
    [metadata.map_extent],
  );
  const basemapPaths = useMemo(
    () => buildBasemapPaths(basemap, projection),
    [basemap, projection],
  );
  const featurePaths = useMemo(
    () =>
      data.features.map((feature) => {
        const { geometry } = feature;
        if (geometry.type === 'Polygon') {
          return geometry.coordinates.map((ring) => projection.ringToPath(ring)).join(' ');
        }
        return geometry.coordinates
          .flatMap((polygon) => polygon.map((ring) => projection.ringToPath(ring)))
          .join(' ');
      }),
    [data.features, projection],
  );

  const handleMouseMove = useCallback((event: React.MouseEvent) => {
    if (!mapRef.current) return;
    const rect = mapRef.current.getBoundingClientRect();
    setContainerWidth(rect.width);
    setTooltipPos({ x: event.clientX - rect.left, y: event.clientY - rect.top });
  }, []);

  const ranked = useMemo(() => {
    if (!layer) return [];
    return data.features
      .map((feature, index) => ({ feature, index, value: numericValue(feature.properties[layer.key]) }))
      .filter((entry): entry is { feature: RiskFeature; index: number; value: number } => entry.value !== null)
      .sort((a, b) => b.value - a.value);
  }, [data.features, layer]);

  const activeIdx = hoveredIdx ?? selectedIdx;
  const activeFeature = activeIdx !== null ? data.features[activeIdx] : null;

  if (!layer) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-6 text-center text-sm text-amber-800">
        No risk layers were found in the metadata.
      </div>
    );
  }

  const groups = [...new Set(layers.map((entry) => entry.group))];
  const badge = STAGE_BADGES[layer.stage];

  return (
    <div className="space-y-6">
      {/* ── Layer selector, grouped by stage ────────────────────────── */}
      <div>
        <label
          htmlFor="risk-layer"
          className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-gray-500"
        >
          Municipal layer
        </label>
        <div className="hidden gap-3 sm:flex sm:flex-wrap">
          {groups.map((group) => (
            <div key={group} className="rounded-lg border border-gray-200 bg-gray-50 p-1">
              <p className="px-2 pt-1 text-[10px] font-semibold uppercase tracking-wide text-gray-400">
                {group}
              </p>
              <div className="flex flex-wrap gap-1">
                {layers
                  .filter((entry) => entry.group === group)
                  .map((entry) => (
                    <button
                      key={entry.key}
                      type="button"
                      onClick={() => setSelectedKey(entry.key)}
                      aria-pressed={entry.key === layer.key}
                      className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                        entry.key === layer.key
                          ? 'bg-white text-gray-900 shadow-sm'
                          : 'text-gray-500 hover:text-gray-700'
                      }`}
                      style={
                        entry.key === layer.key ? { borderBottom: '2px solid #2563eb' } : undefined
                      }
                    >
                      {entry.short_label}
                    </button>
                  ))}
              </div>
            </div>
          ))}
        </div>
        <select
          id="risk-layer"
          value={layer.key}
          onChange={(event) => setSelectedKey(event.target.value)}
          className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-700 sm:hidden"
        >
          {layers.map((entry) => (
            <option key={entry.key} value={entry.key}>
              {entry.label} ({entry.unit})
            </option>
          ))}
        </select>
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
            ariaLabel={`${layer.label} by coastal municipality, in ${layer.unit}`}
          >
            {data.features.map((feature, index) => {
              const value = numericValue(feature.properties[layer.key]);
              const color =
                value === null
                  ? MAP_COLORS.noData
                  : layer.colors[classIndex(value, layer.boundaries)];
              const isActive = activeIdx === index;
              return (
                <path
                  key={feature.properties.municipality_code ?? index}
                  d={featurePaths[index]}
                  fill={color}
                  fillRule="evenodd"
                  stroke={isActive ? MAP_COLORS.highlight : MAP_COLORS.municipalBorder}
                  strokeWidth={isActive ? 1.1 : 0.3}
                  role="button"
                  tabIndex={0}
                  aria-label={`${feature.properties.municipality_name ?? 'Municipality'} ${
                    feature.properties.state ?? ''
                  } ${layer.label} ${formatValue(value, layer.decimals)}`}
                  onMouseEnter={() => setHoveredIdx(index)}
                  onFocus={() => setHoveredIdx(index)}
                  onBlur={() => setHoveredIdx(null)}
                  onClick={() => setSelectedIdx(selectedIdx === index ? null : index)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      setSelectedIdx(selectedIdx === index ? null : index);
                    }
                  }}
                  style={{ cursor: 'pointer' }}
                />
              );
            })}
          </MapFrame>

          {activeFeature && (
            <div
              className="pointer-events-none absolute z-10 w-[250px] rounded-lg border border-gray-200 bg-white p-3 shadow-lg"
              style={{
                left: Math.max(6, Math.min(tooltipPos.x + 12, containerWidth - 260)),
                top: tooltipPos.y - 10,
                transform: 'translateY(-100%)',
              }}
            >
              <div className="mb-1.5 text-[11px] font-bold text-gray-900">
                {activeFeature.properties.municipality_name ?? 'Municipality'}
                {activeFeature.properties.state ? ` · ${activeFeature.properties.state}` : ''}
              </div>
              <div className="space-y-0.5 border-t border-gray-100 pt-1.5 text-xs text-gray-700">
                {DETAIL_FIELDS.map((field) => {
                  if (!(field.key in activeFeature.properties)) return null;
                  return (
                    <div
                      key={field.key}
                      className={field.key === layer.key ? 'font-semibold' : ''}
                    >
                      {field.label}:{' '}
                      <span className="font-mono">
                        {formatValue(numericValue(activeFeature.properties[field.key]), field.decimals)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* ── Legend and context ────────────────────────────────────── */}
        <div className="min-w-0 space-y-4">
          <DiscreteLegend
            title={layer.label}
            unit={layer.unit}
            boundaries={layer.boundaries}
            colors={layer.colors}
            decimals={layer.decimals}
            note={
              <>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${badge.className}`}
                  >
                    {badge.label}
                  </span>
                  <span className="max-w-full break-all rounded border border-gray-200 bg-gray-50 px-2 py-0.5 font-mono text-[10px] text-gray-500">
                    {layer.actual_field}
                  </span>
                  <span className="inline-flex items-center gap-1 text-[10px] text-gray-400">
                    <span
                      className="inline-block h-2 w-2 rounded-sm border border-gray-300"
                      style={{ backgroundColor: MAP_COLORS.noData }}
                    />
                    No data
                  </span>
                </div>
                <p className="mt-2 text-[11px] leading-relaxed text-gray-500">
                  {layer.description}
                </p>
              </>
            }
          />

          <div>
            <p className="mb-2 text-[11px] text-gray-500">
              Statistics over {layer.stats.count} of {data.features.length} municipalities, in{' '}
              <span className="font-semibold text-gray-700">{layer.unit}</span>.
            </p>
            <div className="grid grid-cols-2 gap-3">
              <StatCard label="Minimum" value={formatValue(layer.stats.min, layer.decimals)} />
              <StatCard label="Maximum" value={formatValue(layer.stats.max, layer.decimals)} />
              <StatCard label="Median" value={formatValue(layer.stats.median, layer.decimals)} />
              <StatCard label="Mean" value={formatValue(layer.stats.mean, layer.decimals)} />
            </div>
          </div>

          <section className="rounded-xl border border-gray-200 bg-white p-4">
            <div className="mb-3 flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                  Ranking
                </p>
                <h3 className="text-sm font-bold text-gray-900">Top municipalities</h3>
              </div>
              <span className="rounded border border-gray-200 bg-gray-50 px-2 py-1 font-mono text-[10px] text-gray-500">
                {layer.key}
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[320px] text-left text-xs">
                <thead className="border-b border-gray-200 text-[10px] uppercase tracking-wide text-gray-500">
                  <tr>
                    <th className="py-2 pr-3 font-semibold">#</th>
                    <th className="py-2 pr-3 font-semibold">Municipality</th>
                    <th className="py-2 pr-3 font-semibold">UF</th>
                    <th className="py-2 text-right font-semibold">{layer.short_label}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {ranked.slice(0, 10).map((entry, rank) => (
                    <tr
                      key={entry.feature.properties.municipality_code ?? rank}
                      className="cursor-pointer hover:bg-blue-50/60"
                      onMouseEnter={() => setHoveredIdx(entry.index)}
                      onMouseLeave={() => setHoveredIdx(null)}
                      onClick={() => setSelectedIdx(entry.index)}
                    >
                      <td className="py-2 pr-3 font-mono text-gray-500">{rank + 1}</td>
                      <td className="py-2 pr-3 font-medium text-gray-800">
                        {entry.feature.properties.municipality_name ?? 'N/A'}
                      </td>
                      <td className="py-2 pr-3 text-gray-500">
                        {entry.feature.properties.state ?? 'N/A'}
                      </td>
                      <td className="py-2 text-right font-mono text-gray-800">
                        {formatValue(entry.value, layer.decimals)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 text-[11px] leading-relaxed text-gray-600">
            <p>
              <strong className="text-gray-800">Raw and normalized stages.</strong> Layers marked
              <em> before normalization</em> show the quantity as it comes out of the formula;
              layers marked <em>after normalization</em> show it after the Min–Max rescaling.
              Comparing the two makes the effect of each rescaling step explicit — and shows that
              the ranking of municipalities is unchanged by it.
            </p>
            <p className="mt-2">
              Source CRS {metadata.source_crs}, exported as {metadata.output_crs}; geometry
              simplified with a {metadata.simplification?.tolerance_degrees}° tolerance preserving
              topology. {metadata.feature_count.toLocaleString()} municipalities carry at least one
              populated index.
              {metadata.audit_fields
                ? ` Audit fields (${metadata.audit_fields.fields.join(', ')}) remain in the data file for reproducibility but are not published as map layers.`
                : ''}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
