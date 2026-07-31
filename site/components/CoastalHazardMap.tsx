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

export interface CoastalSegmentProperties {
  source_grid_index: number;
  source_longitude: number;
  source_latitude: number;
  nearest_grid_distance_km: number;
  municipality_name: string | null;
  municipality_state: string | null;
  municipality_distance_km: number | null;
  metrics_index: number;
  segment_count: number;
  [key: string]: number | string | null | undefined;
}

export interface CoastalSegmentFeature {
  type: 'Feature';
  geometry: { type: 'LineString'; coordinates: Position[] };
  properties: CoastalSegmentProperties;
}

export interface CoastalHazardGeoJson {
  type: 'FeatureCollection';
  features: CoastalSegmentFeature[];
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
  zero_is_gray?: boolean;
}

export interface CoastalPalettes {
  sequential: string[];
  diverging: string[];
  risk: string[];
  month: string[];
}

export interface CoastalHazardMetadata {
  generated_at: string;
  period: string;
  source_file: string;
  native_grid_point_count: number;
  native_grid_points_used: number;
  map_extent: number[];
  layers: CoastalHazardLayer[];
  palettes: CoastalPalettes;
  normalization_note: string;
  nearest_municipality: {
    method: string;
    distinct_municipalities: number;
  };
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

export type { CoastalBasemap };

/** A grid point whose daily record can be opened from the map. */
export interface CoastalMarker {
  id: string;
  lat: number;
  lon: number;
  label: string;
}

interface Props {
  data: CoastalHazardGeoJson;
  metadata: CoastalHazardMetadata;
  basemap: CoastalBasemap;
  /** Optional clickable points drawn over the coastal layer. */
  markers?: CoastalMarker[];
  selectedMarkerId?: string | null;
  onMarkerSelect?: (id: string) => void;
}

/* ── Component ─────────────────────────────────────────────────────────── */

export default function CoastalHazardMap({
  data,
  metadata,
  basemap,
  markers,
  selectedMarkerId = null,
  onMarkerSelect,
}: Props) {
  const layers = metadata.layers;
  const [selectedKey, setSelectedKey] = useState<string>(
    layers.find((layer) => layer.key === 'Hazard_Index')?.key ?? layers[0]?.key ?? '',
  );
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
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
  const segmentPaths = useMemo(
    () => data.features.map((feature) => projection.lineToPath(feature.geometry.coordinates)),
    [data.features, projection],
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
              style={entry.key === layer.key ? { borderBottom: '2px solid #2563eb' } : undefined}
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
            ariaLabel={`${layer.label} along the Brazilian coast, in ${layer.unit_plain}`}
            overlay={
              <>
                {data.features.map((feature, index) => {
                  const color = segmentColors[index];
                  if (!color) return null;
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

                {/* Points whose daily record can be opened. Drawn last so they
                    stay above the coastal layer, with a surface ring keeping
                    them legible over any class colour. */}
                {markers?.map((marker) => {
                  const { x, y } = projection.project(marker.lon, marker.lat);
                  const isSelected = marker.id === selectedMarkerId;
                  return (
                    <g
                      key={marker.id}
                      onClick={() => onMarkerSelect?.(marker.id)}
                      style={{ cursor: 'pointer' }}
                      role="button"
                      aria-label={`Open the daily record at ${marker.label}`}
                    >
                      <circle
                        cx={x}
                        cy={y}
                        r={isSelected ? 6.4 : 5}
                        fill="#ffffff"
                        opacity={0.9}
                      />
                      <circle
                        cx={x}
                        cy={y}
                        r={isSelected ? 4.4 : 3}
                        fill={isSelected ? MAP_COLORS.highlight : '#2a78d6'}
                        stroke="#ffffff"
                        strokeWidth={1.2}
                      />
                    </g>
                  );
                })}
              </>
            }
          />

          {hovered && (
            <div
              className="pointer-events-none absolute z-10 w-[240px] rounded-lg border border-gray-200 bg-white p-3 shadow-lg"
              style={{
                left: Math.max(6, Math.min(tooltipPos.x + 12, containerWidth - 250)),
                top: tooltipPos.y - 10,
                transform: 'translateY(-100%)',
              }}
            >
              <div className="mb-1.5 text-[11px] font-bold text-gray-900">
                {hovered.properties.municipality_name ?? 'Municipality not identified'}
                {hovered.properties.municipality_state
                  ? ` · ${hovered.properties.municipality_state}`
                  : ''}
              </div>
              <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-gray-400">
                Grid point {Math.abs(hovered.properties.source_latitude).toFixed(2)}°
                {hovered.properties.source_latitude < 0 ? 'S' : 'N'},{' '}
                {Math.abs(hovered.properties.source_longitude).toFixed(2)}°W
              </div>
              <div className="space-y-0.5 text-xs text-gray-700">
                {layers.map((entry) => (
                  <div key={entry.key} className={entry.key === layer.key ? 'font-semibold' : ''}>
                    {entry.short_label}:{' '}
                    <span className="font-mono">
                      {formatValue(
                        hovered.properties[entry.key] as number | null,
                        entry.decimals,
                      )}
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
        <div className="min-w-0 space-y-4">
          <DiscreteLegend
            title={layer.label}
            unit={layer.unit}
            boundaries={layer.boundaries}
            colors={layer.colors}
            decimals={layer.decimals}
            zeroIsGray={layer.zero_is_gray}
            note={
              <>
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
              </>
            }
          />

          <div>
            <p className="mb-2 text-[11px] text-gray-500">
              Statistics over the {layer.statistics.count.toLocaleString()} coastal polylines, in{' '}
              <span className="font-semibold text-gray-700">{layer.unit}</span>.
            </p>
            <div className="grid grid-cols-2 gap-3">
              <StatCard label="Minimum" value={formatValue(layer.statistics.min, layer.decimals)} />
              <StatCard label="Maximum" value={formatValue(layer.statistics.max, layer.decimals)} />
              <StatCard label="Median" value={formatValue(layer.statistics.median, layer.decimals)} />
              <StatCard label="Mean" value={formatValue(layer.statistics.mean, layer.decimals)} />
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
              Each segment is also labelled with its nearest coastal municipality
              ({metadata.nearest_municipality.distinct_municipalities} distinct municipalities),
              which is the unit used later in the risk integration.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
