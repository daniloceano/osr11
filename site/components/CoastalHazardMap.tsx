'use client';

import { useCallback, useMemo, useRef, useState } from 'react';

/* ── Types ─────────────────────────────────────────────────────────────── */

type Position = [number, number];

interface SegmentProperties {
  source_grid_index: number;
  source_longitude: number;
  source_latitude: number;
  nearest_grid_distance_km: number;
  segment_count: number;
  [key: string]: number | null | undefined;
}

interface SegmentFeature {
  type: 'Feature';
  geometry: { type: 'LineString'; coordinates: Position[] };
  properties: SegmentProperties;
}

export interface CoastalHazardGeoJson {
  type: 'FeatureCollection';
  features: SegmentFeature[];
}

interface BasemapFeature {
  type: 'Feature';
  properties: { layer: 'land' | 'country' | 'state' };
  geometry:
    | { type: 'Polygon'; coordinates: Position[][] }
    | { type: 'MultiPolygon'; coordinates: Position[][][] }
    | { type: 'LineString'; coordinates: Position[] }
    | { type: 'MultiLineString'; coordinates: Position[][] };
}

export interface CoastalBasemap {
  type: 'FeatureCollection';
  features: BasemapFeature[];
}

interface LayerStats {
  count: number;
  min: number | null;
  max: number | null;
  mean: number | null;
  median: number | null;
}

export interface CoastalHazardLayer {
  key: string;
  label: string;
  short_label: string;
  unit: string;
  unit_plain: string;
  value_kind: 'catalog' | 'index';
  decimals: number;
  boundaries: number[];
  colors: string[];
  palette: string;
  palette_source: string;
  display_values: string;
  description: string;
  statistics: LayerStats;
}

export interface CoastalHazardMetadata {
  generated_at: string;
  period: string;
  source_file: string;
  native_grid_point_count: number;
  native_grid_points_used: number;
  map_extent: number[];
  layers: CoastalHazardLayer[];
  normalization_note: string;
  coastal_projection: {
    method: string;
    projected_crs: string;
    maximum_segment_length_m: number;
    segment_count: number;
    feature_count: number;
    nearest_distance_km: {
      minimum: number;
      median: number;
      mean: number;
      p90: number;
      p99: number;
      maximum: number;
    };
  };
}

interface Props {
  data: CoastalHazardGeoJson;
  metadata: CoastalHazardMetadata;
  basemap: CoastalBasemap;
}

/* ── Map colors (mirror the article figure) ────────────────────────────── */

const OCEAN_COLOR = '#e9f3f7';
const LAND_COLOR = '#ddddda';
const STATE_BORDER_COLOR = '#92928e';
const COUNTRY_BORDER_COLOR = '#555553';
const GRATICULE_COLOR = '#9aa9b0';

/* ── Helpers ───────────────────────────────────────────────────────────── */

/** Discrete class of a value, mirroring numpy.digitize(v, boundaries[1:-1]). */
function classIndex(value: number, boundaries: number[]): number {
  const classes = boundaries.length - 1;
  for (let i = 1; i < classes; i += 1) {
    if (value < boundaries[i]) return i - 1;
  }
  return classes - 1;
}

function formatNumber(value: number | null | undefined, decimals: number): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return 'No data';
  return value.toFixed(decimals);
}

function formatBoundary(value: number, decimals: number): string {
  return Number.isInteger(value) && decimals <= 1
    ? value.toFixed(0)
    : value.toFixed(decimals);
}

/* ── Component ─────────────────────────────────────────────────────────── */

export default function CoastalHazardMap({ data, metadata, basemap }: Props) {
  const layers = metadata.layers;
  const [selectedKey, setSelectedKey] = useState<string>(
    layers.find((layer) => layer.key === 'Hazard_Index')?.key ?? layers[0]?.key ?? '',
  );
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [containerWidth, setContainerWidth] = useState(420);
  const mapRef = useRef<HTMLDivElement>(null);

  const layer = layers.find((entry) => entry.key === selectedKey) ?? layers[0];

  const [west, east, south, north] = metadata.map_extent;
  const svgWidth = 420;
  const svgHeight = (svgWidth * (north - south)) / (east - west);

  const project = useCallback(
    (lon: number, lat: number) => ({
      x: ((lon - west) / (east - west)) * svgWidth,
      y: ((north - lat) / (north - south)) * svgHeight,
    }),
    [west, east, north, south, svgHeight],
  );

  const toPath = useCallback(
    (ring: Position[], close: boolean) => {
      if (ring.length === 0) return '';
      const points = ring.map(([lon, lat]) => {
        const { x, y } = project(lon, lat);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      });
      return `M${points.join('L')}${close ? 'Z' : ''}`;
    },
    [project],
  );

  const basemapPaths = useMemo(() => {
    const paths: Record<'land' | 'country' | 'state', string[]> = {
      land: [],
      country: [],
      state: [],
    };
    basemap.features.forEach((feature) => {
      const { geometry } = feature;
      const target = paths[feature.properties.layer];
      if (!target) return;
      if (geometry.type === 'Polygon') {
        target.push(geometry.coordinates.map((ring) => toPath(ring, true)).join(' '));
      } else if (geometry.type === 'MultiPolygon') {
        target.push(
          geometry.coordinates
            .flatMap((polygon) => polygon.map((ring) => toPath(ring, true)))
            .join(' '),
        );
      } else if (geometry.type === 'LineString') {
        target.push(toPath(geometry.coordinates, false));
      } else {
        target.push(geometry.coordinates.map((line) => toPath(line, false)).join(' '));
      }
    });
    return paths;
  }, [basemap.features, toPath]);

  const segmentPaths = useMemo(
    () => data.features.map((feature) => toPath(feature.geometry.coordinates, false)),
    [data.features, toPath],
  );

  const segmentColors = useMemo(() => {
    if (!layer) return [];
    return data.features.map((feature) => {
      const value = feature.properties[layer.key];
      if (typeof value !== 'number' || !Number.isFinite(value)) return null;
      return layer.colors[classIndex(value, layer.boundaries)];
    });
  }, [data.features, layer]);

  const handleMouseMove = useCallback((event: React.MouseEvent) => {
    if (!mapRef.current) return;
    const rect = mapRef.current.getBoundingClientRect();
    setContainerWidth(rect.width);
    setTooltipPos({ x: event.clientX - rect.left, y: event.clientY - rect.top });
  }, []);

  const hovered = hoveredIdx !== null ? data.features[hoveredIdx] : null;

  if (!layer) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-6 text-center text-sm text-amber-800">
        No coastal hazard layers were found in the metadata.
      </div>
    );
  }

  const longitudeTicks: number[] = [];
  for (let lon = Math.ceil(west / 5) * 5; lon <= east; lon += 5) longitudeTicks.push(lon);
  const latitudeTicks: number[] = [];
  for (let lat = Math.ceil(south / 5) * 5; lat <= north; lat += 5) latitudeTicks.push(lat);

  return (
    <div className="space-y-5">
      {/* ── Layer selector ──────────────────────────────────────────── */}
      <div>
        <label
          htmlFor="coastal-hazard-layer"
          className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-gray-500"
        >
          Coastal layer
        </label>
        <div className="hidden flex-wrap gap-1 rounded-lg border border-gray-200 bg-gray-50 p-1 sm:flex">
          {layers.map((entry) => (
            <button
              key={entry.key}
              type="button"
              onClick={() => setSelectedKey(entry.key)}
              aria-pressed={entry.key === layer.key}
              className={`rounded-md px-3 py-2 text-xs font-medium transition-colors ${
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
        <select
          id="coastal-hazard-layer"
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

      <div className="grid gap-6 lg:grid-cols-[minmax(0,460px)_minmax(0,1fr)]">
        {/* ── Map ───────────────────────────────────────────────────── */}
        <div
          ref={mapRef}
          className="relative mx-auto w-full max-w-[460px] overflow-hidden rounded-xl border border-gray-200"
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoveredIdx(null)}
        >
          <svg
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            className="block h-auto w-full"
            role="img"
            aria-label={`${layer.label} along the Brazilian coast, in ${layer.unit_plain}`}
          >
            <rect width={svgWidth} height={svgHeight} fill={OCEAN_COLOR} />

            {basemapPaths.land.map((path, index) => (
              <path key={`land-${index}`} d={path} fill={LAND_COLOR} fillRule="evenodd" />
            ))}

            {longitudeTicks.map((lon) => {
              const { x } = project(lon, north);
              return (
                <g key={`grat-lon-${lon}`}>
                  <line
                    x1={x}
                    y1={0}
                    x2={x}
                    y2={svgHeight}
                    stroke={GRATICULE_COLOR}
                    strokeWidth={0.4}
                    strokeDasharray="3 3"
                    opacity={0.55}
                  />
                  <text
                    x={x}
                    y={svgHeight - 4}
                    textAnchor="middle"
                    fill="#374151"
                    style={{ fontSize: '8px' }}
                  >
                    {Math.abs(lon)}°W
                  </text>
                </g>
              );
            })}
            {latitudeTicks.map((lat) => {
              const { y } = project(west, lat);
              return (
                <g key={`grat-lat-${lat}`}>
                  <line
                    x1={0}
                    y1={y}
                    x2={svgWidth}
                    y2={y}
                    stroke={GRATICULE_COLOR}
                    strokeWidth={0.4}
                    strokeDasharray="3 3"
                    opacity={0.55}
                  />
                  <text x={4} y={y - 3} fill="#374151" style={{ fontSize: '8px' }}>
                    {Math.abs(lat)}°{lat < 0 ? 'S' : 'N'}
                  </text>
                </g>
              );
            })}

            {basemapPaths.state.map((path, index) => (
              <path
                key={`state-${index}`}
                d={path}
                fill="none"
                stroke={STATE_BORDER_COLOR}
                strokeWidth={0.5}
              />
            ))}
            {basemapPaths.country.map((path, index) => (
              <path
                key={`country-${index}`}
                d={path}
                fill="none"
                stroke={COUNTRY_BORDER_COLOR}
                strokeWidth={0.8}
              />
            ))}

            {data.features.map((feature, index) => {
              const color = segmentColors[index];
              if (!color) return null;
              const isHovered = hoveredIdx === index;
              return (
                <path
                  key={`${feature.properties.source_grid_index}-${index}`}
                  d={segmentPaths[index]}
                  fill="none"
                  stroke={isHovered ? '#111827' : color}
                  strokeWidth={isHovered ? 4.4 : 3}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  onMouseEnter={() => setHoveredIdx(index)}
                  style={{ cursor: 'pointer' }}
                />
              );
            })}
          </svg>

          {hovered && (
            <div
              className="pointer-events-none absolute z-10 w-[230px] rounded-lg border border-gray-200 bg-white p-3 shadow-lg"
              style={{
                left: Math.max(6, Math.min(tooltipPos.x + 12, containerWidth - 240)),
                top: tooltipPos.y - 10,
                transform: 'translateY(-100%)',
              }}
            >
              <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-gray-400">
                Nearest grid point {Math.abs(hovered.properties.source_latitude).toFixed(2)}°
                {hovered.properties.source_latitude < 0 ? 'S' : 'N'},{' '}
                {Math.abs(hovered.properties.source_longitude).toFixed(2)}°W
              </div>
              <div className="space-y-0.5 text-xs text-gray-700">
                {layers.map((entry) => (
                  <div key={entry.key} className={entry.key === layer.key ? 'font-semibold' : ''}>
                    {entry.short_label}:{' '}
                    <span className="font-mono">
                      {formatNumber(hovered.properties[entry.key], entry.decimals)}
                    </span>{' '}
                    <span className="text-gray-400">{entry.unit}</span>
                  </div>
                ))}
                <div className="border-t border-gray-100 pt-1 text-[10px] text-gray-500">
                  Distance to grid point:{' '}
                  <span className="font-mono">
                    {hovered.properties.nearest_grid_distance_km.toFixed(1)} km
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ── Legend and context ────────────────────────────────────── */}
        <div className="space-y-4">
          <div className="rounded-xl border border-gray-200 bg-white p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
              Legend
            </p>
            <h3 className="mt-1 text-sm font-bold text-gray-900">
              {layer.label}{' '}
              <span className="font-normal text-gray-500">({layer.unit})</span>
            </h3>
            <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2">
              {layer.colors.map((color, index) => {
                const lower = layer.boundaries[index];
                const upper = layer.boundaries[index + 1];
                const isFirst = index === 0;
                const isLast = index === layer.colors.length - 1;
                const label = isFirst
                  ? `< ${formatBoundary(upper, layer.decimals)}`
                  : isLast
                    ? `≥ ${formatBoundary(lower, layer.decimals)}`
                    : `${formatBoundary(lower, layer.decimals)} – ${formatBoundary(upper, layer.decimals)}`;
                return (
                  <div key={color + index} className="flex items-center gap-1.5">
                    <span
                      className="inline-block h-3 w-6 rounded-sm border border-black/10"
                      style={{ backgroundColor: color }}
                    />
                    <span className="font-mono text-[10px] text-gray-600">{label}</span>
                  </div>
                );
              })}
            </div>
            <p className="mt-3 text-[11px] leading-relaxed text-gray-500">
              {layer.description}
            </p>
            {layer.value_kind === 'catalog' && (
              <p className="mt-2 rounded-md border border-blue-100 bg-blue-50 px-2.5 py-2 text-[11px] leading-relaxed text-blue-800">
                Values shown are the native-grid catalog values in {layer.unit_plain}. The
                Min–Max scaling of this component is a methodological step used only inside
                the Hazard Index — it is not applied here.
              </p>
            )}
          </div>

          <div>
            <p className="mb-2 text-[11px] text-gray-500">
              Statistics over the {layer.statistics.count.toLocaleString()} coastal polylines, in{' '}
              <span className="font-semibold text-gray-700">{layer.unit}</span>.
            </p>
            <div className="grid grid-cols-2 gap-3">
              <StatCard
                label="Minimum"
                value={formatNumber(layer.statistics.min, layer.decimals)}
              />
              <StatCard
                label="Maximum"
                value={formatNumber(layer.statistics.max, layer.decimals)}
              />
              <StatCard
                label="Median"
                value={formatNumber(layer.statistics.median, layer.decimals)}
              />
              <StatCard label="Mean" value={formatNumber(layer.statistics.mean, layer.decimals)} />
            </div>
          </div>

          <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 text-[11px] leading-relaxed text-gray-600">
            <p>
              <strong className="text-gray-800">Coastal representation.</strong> The index is
              calculated on {metadata.native_grid_point_count} native ocean grid points
              ({metadata.period}). For display, the Natural Earth 10-m coastline is clipped to
              the coastal-municipality band, split into segments of at most{' '}
              {(metadata.coastal_projection.maximum_segment_length_m / 1000).toFixed(0)} km in{' '}
              {metadata.coastal_projection.projected_crs}, and each segment takes the value of its
              nearest grid point. This is a visualization step: no index is recalculated or
              renormalized.
            </p>
            <p className="mt-2">
              {metadata.coastal_projection.segment_count.toLocaleString()} segments (merged into{' '}
              {metadata.coastal_projection.feature_count.toLocaleString()} polylines) draw on{' '}
              {metadata.native_grid_points_used} distinct grid points. Median distance from a
              segment to its grid point is{' '}
              {metadata.coastal_projection.nearest_distance_km.median.toFixed(1)} km (99th
              percentile {metadata.coastal_projection.nearest_distance_km.p99.toFixed(1)} km).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3">
      <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-gray-500">
        {label}
      </div>
      <div className="text-sm font-bold leading-snug break-words text-gray-900">{value}</div>
    </div>
  );
}
