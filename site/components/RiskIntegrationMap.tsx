'use client';

import { useCallback, useMemo, useRef, useState } from 'react';

type RiskLayerKey = string;
type Position = [number, number];

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
  key: RiskLayerKey;
  label: string;
  unit: string;
  description: string;
  actual_field: string;
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
  bbox: number[];
  available_layers: RiskLayerMeta[];
  missing_expected_layers: string[];
  field_aliases: {
    layers: Record<string, string | null | undefined>;
    support: Record<string, string>;
  };
  legacy_outputs?: {
    geojson: string;
    metadata: string;
  };
  simplification?: {
    enabled: boolean;
    tolerance_degrees: number;
    preserve_topology: boolean;
    coordinates_before: number;
    coordinates_after: number;
  };
  numeric_stats?: Record<string, LayerStats>;
}

interface Props {
  data: RiskGeoJson;
  metadata: RiskMetadata;
}

const EXPECTED_LAYER_ORDER: RiskLayerKey[] = ['Risk_Hazard', 'Hazard_Index', 'SVI_Coast_2022', 'Risk_Comp'];

const DETAIL_FIELDS: { key: string; label: string }[] = [
  { key: 'SVI_Coast_2022', label: 'SVI_Coast_2022' },
  { key: 'Hazard_Index', label: 'Current Hazard_Index' },
  { key: 'Risk_Hazard', label: 'Current Risk_Hazard' },
  { key: 'Risk_Comp', label: 'Frequency risk' },
  { key: 'compound_c', label: 'compound_c' },
  { key: 'mean_overl', label: 'mean_overl (diagnostic)' },
  { key: 'mean_compo', label: 'mean_compo (diagnostic)' },
  { key: 'Legacy_Hazard_Index', label: 'Legacy Hazard_Index' },
  { key: 'Legacy_Risk_Hazard', label: 'Legacy Risk_Hazard' },
  { key: 'Legacy_Risk_Comp', label: 'Legacy Risk_Comp' },
];

const RAMP_SEQUENTIAL = [
  '#ffffcc',
  '#ffeda0',
  '#fed976',
  '#feb24c',
  '#fd8d3c',
  '#fc4e2a',
  '#e31a1c',
  '#bd0026',
  '#800026',
];

const NO_DATA_COLOR = '#e5e7eb';
const MAP_BOUNDS = { lonMin: -56, lonMax: -27, latMin: -36, latMax: 7 };
const ASPECT = (MAP_BOUNDS.lonMax - MAP_BOUNDS.lonMin) / (MAP_BOUNDS.latMax - MAP_BOUNDS.latMin);

function project(lon: number, lat: number, width: number, height: number) {
  const x = ((lon - MAP_BOUNDS.lonMin) / (MAP_BOUNDS.lonMax - MAP_BOUNDS.lonMin)) * width;
  const y = ((MAP_BOUNDS.latMax - lat) / (MAP_BOUNDS.latMax - MAP_BOUNDS.latMin)) * height;
  return { x, y };
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

function ringToPath(ring: Position[], width: number, height: number): string {
  if (ring.length === 0) return '';
  const points = ring.map(([lon, lat]) => {
    const { x, y } = project(lon, lat, width, height);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  return `M${points.join('L')}Z`;
}

function geometryToPath(geometry: PolygonGeometry | MultiPolygonGeometry, width: number, height: number): string {
  if (geometry.type === 'Polygon') {
    return geometry.coordinates.map((ring) => ringToPath(ring, width, height)).join(' ');
  }
  return geometry.coordinates
    .flatMap((polygon) => polygon.map((ring) => ringToPath(ring, width, height)))
    .join(' ');
}

function numericValue(value: unknown): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function formatValue(value: number | null | undefined, key: string): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return 'No data';
  if (key === 'SVI_Coast_2022') return value.toFixed(1);
  if (key === 'compound_c') return Math.round(value).toLocaleString();
  if (key === 'mean_overl') return value.toFixed(2);
  if (key === 'mean_compo') return value.toFixed(3);
  return value.toFixed(3);
}

function detailLabel(field: { key: string; label: string }, isLegacyScope: boolean): string {
  if (!isLegacyScope) return field.label;
  if (field.key === 'Hazard_Index') return 'Legacy Hazard_Index';
  if (field.key === 'Risk_Hazard') return 'Legacy Risk_Hazard';
  if (field.key === 'Risk_Comp') return 'Legacy Risk_Comp';
  if (field.key === 'mean_overl') return 'mean_overl';
  if (field.key === 'mean_compo') return 'mean_compo';
  return field.label;
}

function median(values: number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

export default function RiskIntegrationMap({ data, metadata }: Props) {
  const layers = useMemo(() => {
    const byKey = new Map(metadata.available_layers.map((layer) => [layer.key, layer]));
    const ordered = EXPECTED_LAYER_ORDER.map((key) => byKey.get(key)).filter((layer): layer is RiskLayerMeta => Boolean(layer));
    const remaining = metadata.available_layers.filter((layer) => !EXPECTED_LAYER_ORDER.includes(layer.key));
    return [...ordered, ...remaining];
  }, [metadata.available_layers]);

  const defaultLayerKey = layers.find((layer) => layer.key === 'Risk_Hazard')?.key ?? layers[0]?.key ?? 'SVI_Coast_2022';
  const [selectedLayerKey, setSelectedLayerKey] = useState<RiskLayerKey | null>(null);
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [svgClientWidth, setSvgClientWidth] = useState(640);
  const svgRef = useRef<SVGSVGElement>(null);

  const selectedLayer = layers.find((layer) => layer.key === (selectedLayerKey ?? defaultLayerKey)) ?? layers[0];
  const isLegacyScope = metadata.scope === 'legacy_multimetric';
  const scopeLabel = isLegacyScope ? 'Legacy multi-metric product' : 'Current compound-count-only product';
  const selectedKey = selectedLayer?.key ?? '';
  const svgWidth = 640;
  const svgHeight = svgWidth / ASPECT;

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    setSvgClientWidth(rect.width);
    setTooltipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  }, []);

  const featurePaths = useMemo(() => {
    return data.features.map((feature) => geometryToPath(feature.geometry, svgWidth, svgHeight));
  }, [data.features, svgHeight]);

  const layerEntries = useMemo(() => {
    if (!selectedKey) return [];
    return data.features
      .map((feature, index) => ({
        feature,
        index,
        value: numericValue(feature.properties[selectedKey]),
      }))
      .filter((entry): entry is { feature: RiskFeature; index: number; value: number } => entry.value !== null)
      .sort((a, b) => b.value - a.value);
  }, [data.features, selectedKey]);

  const layerValues = layerEntries.map((entry) => entry.value);
  const vMin = layerValues.length > 0 ? Math.min(...layerValues) : 0;
  const vMax = layerValues.length > 0 ? Math.max(...layerValues) : 1;
  const vMean = layerValues.length > 0 ? layerValues.reduce((a, b) => a + b, 0) / layerValues.length : null;
  const vMedian = median(layerValues);
  const topEntry = layerEntries[0] ?? null;
  const activeIdx = hoveredIdx ?? selectedIdx;
  const activeFeature = activeIdx !== null ? data.features[activeIdx] : null;

  if (!selectedLayer) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-6 text-center text-sm text-amber-800">
        No risk layers were found in the metadata.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-1 rounded-lg border border-gray-200 bg-gray-50 p-1">
        {layers.map((layer) => (
          <button
            key={layer.key}
            onClick={() => setSelectedLayerKey(layer.key)}
            aria-pressed={selectedKey === layer.key}
            className={`rounded-md px-3 py-2 text-xs font-medium transition-colors ${
              selectedKey === layer.key
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            style={selectedKey === layer.key ? { borderBottom: '2px solid #2563eb' } : undefined}
          >
            {layer.label}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap items-end gap-4">
        <div className="min-w-[220px] flex-1">
          <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-gray-500">
            Layer
          </label>
          <select
            value={selectedKey}
            onChange={(e) => setSelectedLayerKey(e.target.value as RiskLayerKey)}
            className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-medium text-gray-700"
          >
            {layers.map((layer) => (
              <option key={layer.key} value={layer.key}>
                {layer.label}
              </option>
            ))}
          </select>
        </div>
        <div className="text-xs text-gray-500">
          <span className="font-semibold text-gray-700">{selectedLayer.key}</span>:{' '}
          <span className="font-semibold text-gray-700">{selectedLayer.actual_field}</span>.
        </div>
      </div>

      <div className="relative overflow-hidden rounded-xl border border-gray-200 bg-gray-50">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full"
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoveredIdx(null)}
        >
          <rect width={svgWidth} height={svgHeight} fill="#f8fafc" />

          {Array.from({ length: 7 }, (_, i) => MAP_BOUNDS.lonMin + 5 + i * 5)
            .filter((lon) => lon < MAP_BOUNDS.lonMax)
            .map((lon) => {
              const { x } = project(lon, MAP_BOUNDS.latMax, svgWidth, svgHeight);
              return (
                <g key={`grat-lon-${lon}`}>
                  <line x1={x} y1={0} x2={x} y2={svgHeight} stroke="#e2e8f0" strokeWidth={0.5} />
                  <text x={x} y={svgHeight - 4} textAnchor="middle" className="fill-gray-400" style={{ fontSize: '8px' }}>
                    {Math.abs(lon)}W
                  </text>
                </g>
              );
            })}
          {Array.from({ length: 9 }, (_, i) => MAP_BOUNDS.latMin + 5 + i * 5)
            .filter((lat) => lat < MAP_BOUNDS.latMax)
            .map((lat) => {
              const { y } = project(MAP_BOUNDS.lonMin, lat, svgWidth, svgHeight);
              return (
                <g key={`grat-lat-${lat}`}>
                  <line x1={0} y1={y} x2={svgWidth} y2={y} stroke="#e2e8f0" strokeWidth={0.5} />
                  <text x={4} y={y - 3} className="fill-gray-400" style={{ fontSize: '8px' }}>
                    {Math.abs(lat)}{lat < 0 ? 'S' : 'N'}
                  </text>
                </g>
              );
            })}

          {data.features.map((feature, index) => {
            const value = numericValue(feature.properties[selectedKey]);
            const t = value !== null && vMax > vMin ? (value - vMin) / (vMax - vMin) : 0.5;
            const color = value === null ? NO_DATA_COLOR : interpolateColor(RAMP_SEQUENTIAL, t);
            const isActive = activeIdx === index;
            return (
              <path
                key={feature.properties.municipality_code ?? index}
                d={featurePaths[index]}
                fill={color}
                fillRule="evenodd"
                role="button"
                tabIndex={0}
                aria-label={`${feature.properties.municipality_name ?? 'Municipality'} ${feature.properties.state ?? ''} ${selectedLayer.label} ${formatValue(value, selectedKey)}`}
                stroke={isActive ? '#1e293b' : '#ffffff'}
                strokeWidth={isActive ? 1.1 : 0.35}
                opacity={value === null ? 0.65 : 0.92}
                onMouseEnter={() => setHoveredIdx(index)}
                onFocus={() => setHoveredIdx(index)}
                onBlur={() => setHoveredIdx(null)}
                onClick={(e) => {
                  if (!svgRef.current) return;
                  const rect = svgRef.current.getBoundingClientRect();
                  setSvgClientWidth(rect.width);
                  setTooltipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
                  setSelectedIdx(selectedIdx === index ? null : index);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setSelectedIdx(selectedIdx === index ? null : index);
                  }
                }}
                style={{ cursor: 'pointer', transition: 'opacity 0.12s, stroke-width 0.12s' }}
              />
            );
          })}
        </svg>

        {activeFeature && (
          <div
            className="pointer-events-none absolute z-10 w-[260px] rounded-lg border border-gray-200 bg-white p-3 shadow-lg"
            style={{
              left: Math.max(8, Math.min(tooltipPos.x + 12, svgClientWidth - 272)),
              top: tooltipPos.y - 10,
              transform: 'translateY(-100%)',
            }}
          >
            <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-gray-400">
              {activeFeature.properties.municipality_name ?? 'Municipality'} · {activeFeature.properties.state ?? 'UF'}
            </div>
            <div className="mb-2 text-xs font-semibold text-gray-900">
              {selectedLayer.label}:{' '}
              <span className="font-mono">{formatValue(numericValue(activeFeature.properties[selectedKey]), selectedKey)}</span>
            </div>
            <div className="space-y-0.5 border-t border-gray-100 pt-2 text-xs text-gray-700">
              {DETAIL_FIELDS.map((field) => {
                const value = numericValue(activeFeature.properties[field.key]);
                const hasField = field.key in activeFeature.properties;
                if (!hasField) return null;
                return (
                  <div key={field.key} className={field.key === selectedKey ? 'font-semibold' : ''}>
                    {detailLabel(field, isLegacyScope)}: <span className="font-mono">{formatValue(value, field.key)}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="absolute bottom-4 right-4 rounded-lg border border-gray-200 bg-white/95 px-3 py-2 backdrop-blur-sm">
          <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-gray-500">
            {selectedLayer.key}
          </div>
          <div className="flex items-center gap-1">
            <span className="w-12 text-right font-mono text-[10px] text-gray-500">
              {formatValue(vMin, selectedKey)}
            </span>
            <div
              className="h-3 w-24 rounded-sm"
              style={{ background: `linear-gradient(to right, ${RAMP_SEQUENTIAL.join(', ')})` }}
            />
            <span className="w-12 font-mono text-[10px] text-gray-500">
              {formatValue(vMax, selectedKey)}
            </span>
          </div>
          <div className="mt-1 flex items-center justify-end gap-1 text-[9px] text-gray-400">
            <span className="inline-block h-2 w-2 rounded-sm border border-gray-300" style={{ backgroundColor: NO_DATA_COLOR }} />
            No data
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <StatCard label="Municipalities with data" value={`${layerValues.length} / ${data.features.length}`} />
        <StatCard label="Minimum" value={formatValue(vMin, selectedKey)} />
        <StatCard label="Median" value={formatValue(vMedian, selectedKey)} />
        <StatCard label="Mean" value={formatValue(vMean, selectedKey)} />
        <StatCard
          label="Highest municipality"
          value={topEntry ? `${topEntry.feature.properties.municipality_name ?? 'N/A'} (${formatValue(topEntry.value, selectedKey)})` : 'No data'}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(300px,0.85fr)]">
        <section className="rounded-lg border border-gray-200 bg-white p-4">
          <div className="mb-3 flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">Ranking</p>
              <h2 className="text-base font-bold text-gray-900">Top Municipalities by Selected Layer</h2>
            </div>
            <span className="rounded border border-gray-200 bg-gray-50 px-2 py-1 font-mono text-[10px] text-gray-500">
              {selectedLayer.key}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-xs">
              <thead className="border-b border-gray-200 text-[10px] uppercase tracking-wide text-gray-500">
                <tr>
                  <th className="py-2 pr-3 font-semibold">#</th>
                  <th className="py-2 pr-3 font-semibold">Municipality</th>
                  <th className="py-2 pr-3 font-semibold">UF</th>
                  <th className="py-2 pr-3 text-right font-semibold">{selectedLayer.key}</th>
                  <th className="py-2 pr-3 text-right font-semibold">SVI</th>
                  <th className="py-2 text-right font-semibold">Hazard</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {layerEntries.slice(0, 10).map((entry, rank) => (
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
                    <td className="py-2 pr-3 text-gray-500">{entry.feature.properties.state ?? 'N/A'}</td>
                    <td className="py-2 pr-3 text-right font-mono text-gray-800">
                      {formatValue(entry.value, selectedKey)}
                    </td>
                    <td className="py-2 pr-3 text-right font-mono text-gray-500">
                      {formatValue(numericValue(entry.feature.properties.SVI_Coast_2022), 'SVI_Coast_2022')}
                    </td>
                    <td className="py-2 text-right font-mono text-gray-500">
                      {formatValue(numericValue(entry.feature.properties.Hazard_Index), 'Hazard_Index')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="rounded-lg border border-gray-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-gray-500">Data Product</p>
          <h2 className="mt-1 text-base font-bold text-gray-900">Detected Fields</h2>
          <p className="mt-1 text-xs text-gray-500">{scopeLabel}</p>
          <dl className="mt-3 space-y-2 text-xs text-gray-600">
            {layers.map((layer) => (
              <div key={layer.key} className="flex items-center justify-between gap-3 border-b border-gray-100 pb-2 last:border-0">
                <dt className="font-medium text-gray-800">{layer.key}</dt>
                <dd className="font-mono text-gray-500">{layer.actual_field}</dd>
              </div>
            ))}
          </dl>
          <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-3 text-xs text-gray-500">
            <p>
              Source CRS {metadata.source_crs}; exported as {metadata.output_crs}. Source shapefile has{' '}
              {metadata.source_feature_count.toLocaleString()} records; this web layer includes{' '}
              {metadata.feature_count.toLocaleString()} municipalities with at least one populated index.
            </p>
            {metadata.simplification?.enabled && (
              <p className="mt-2">
                Geometry simplified with tolerance {metadata.simplification.tolerance_degrees} degrees,
            preserving topology.
              </p>
            )}
            {!isLegacyScope && metadata.legacy_outputs && (
              <p className="mt-2">
                The former multi-metric product is retained as legacy data at{' '}
                <span className="font-mono">{metadata.legacy_outputs.geojson}</span>.
              </p>
            )}
          </div>
        </section>
      </div>

      <section className="rounded-lg border border-gray-200 bg-gray-50 p-5">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-blue-600">Methodology</p>
        <div className="grid gap-4 text-xs leading-relaxed text-gray-600 md:grid-cols-3">
          <p>
            <strong className="text-gray-800">Social vulnerability.</strong> SVI_Coast_2022 was built from
            IBGE/SIDRA 2022 socioeconomic and infrastructure variables, standardized with StandardScaler and
            submitted to PCA. PC1 was sign-adjusted so higher values mean higher social vulnerability, then
            normalized from 0 to 100.
          </p>
          {isLegacyScope ? (
            <>
              <p>
                <strong className="text-gray-800">Exposure and hazard.</strong> This legacy product uses the former
                Hazard_Index: the mean of normalized compound-event frequency, mean overlap duration, and mean
                compound-event intensity.
              </p>
              <p>
                <strong className="text-gray-800">Risk integration.</strong> Risk_Comp = (SVI_Coast_2022 / 100) x
                norm(compound_c). Risk_Hazard = (SVI_Coast_2022 / 100) x the legacy Hazard_Index. It is kept for
                audit and comparison with earlier outputs.
              </p>
            </>
          ) : (
            <>
              <p>
                <strong className="text-gray-800">Exposure and hazard.</strong> The current Hazard_Index uses only
                compound-event frequency: Hazard_Index = norm(compound_c). Duration and intensity remain visible as
                diagnostic fields and in the legacy product, but are excluded from the current hazard layer.
              </p>
              <p>
                <strong className="text-gray-800">Risk integration.</strong> Risk_Hazard = (SVI_Coast_2022 / 100) x
                Hazard_Index, with Hazard_Index = norm(compound_c). This avoids treating uncertain duration/intensity
                signals near river mouths as direct hazard intensity.
              </p>
            </>
          )}
        </div>
      </section>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3">
      <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-gray-500">
        {label}
      </div>
      <div className="break-words text-lg font-bold leading-snug text-gray-900">{value}</div>
    </div>
  );
}
