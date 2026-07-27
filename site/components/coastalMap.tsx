'use client';

/**
 * Shared map primitives for the coastal and municipal panels.
 *
 * Every map on the results pages uses the same cartography as the article
 * figures: light-gray land, light-blue ocean, dark-gray country borders,
 * lighter state borders, a dashed graticule, and discrete class colors coming
 * from `src/04_risk_integration/palettes.py`.
 */

import type { ReactNode } from 'react';

/* ── Cartography ───────────────────────────────────────────────────────── */

export const MAP_COLORS = {
  ocean: '#e9f3f7',
  land: '#ddddda',
  noData: '#c7c7c4',
  stateBorder: '#92928e',
  countryBorder: '#555553',
  graticule: '#9aa9b0',
  municipalBorder: '#f8fafc',
  highlight: '#111827',
} as const;

export type Position = [number, number];

export interface MapExtent {
  west: number;
  east: number;
  south: number;
  north: number;
}

export function extentFromArray(extent: number[]): MapExtent {
  const [west, east, south, north] = extent;
  return { west, east, south, north };
}

export interface Projection {
  width: number;
  height: number;
  extent: MapExtent;
  project: (lon: number, lat: number) => { x: number; y: number };
  lineToPath: (line: Position[]) => string;
  ringToPath: (ring: Position[]) => string;
}

export function makeProjection(extent: MapExtent, width: number): Projection {
  const height = (width * (extent.north - extent.south)) / (extent.east - extent.west);
  const project = (lon: number, lat: number) => ({
    x: ((lon - extent.west) / (extent.east - extent.west)) * width,
    y: ((extent.north - lat) / (extent.north - extent.south)) * height,
  });
  const toPoints = (coordinates: Position[]) =>
    coordinates
      .map(([lon, lat]) => {
        const { x, y } = project(lon, lat);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join('L');
  return {
    width,
    height,
    extent,
    project,
    lineToPath: (line) => (line.length ? `M${toPoints(line)}` : ''),
    ringToPath: (ring) => (ring.length ? `M${toPoints(ring)}Z` : ''),
  };
}

/* ── Basemap ───────────────────────────────────────────────────────────── */

export interface BasemapFeature {
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

export type BasemapPaths = Record<'land' | 'country' | 'state', string[]>;

export function buildBasemapPaths(
  basemap: CoastalBasemap,
  projection: Projection,
): BasemapPaths {
  const paths: BasemapPaths = { land: [], country: [], state: [] };
  basemap.features.forEach((feature) => {
    const target = paths[feature.properties.layer];
    if (!target) return;
    const { geometry } = feature;
    if (geometry.type === 'Polygon') {
      target.push(geometry.coordinates.map((ring) => projection.ringToPath(ring)).join(' '));
    } else if (geometry.type === 'MultiPolygon') {
      target.push(
        geometry.coordinates
          .flatMap((polygon) => polygon.map((ring) => projection.ringToPath(ring)))
          .join(' '),
      );
    } else if (geometry.type === 'LineString') {
      target.push(projection.lineToPath(geometry.coordinates));
    } else {
      target.push(geometry.coordinates.map((line) => projection.lineToPath(line)).join(' '));
    }
  });
  return paths;
}

/* ── Frame ─────────────────────────────────────────────────────────────── */

interface MapFrameProps {
  projection: Projection;
  basemapPaths: BasemapPaths;
  ariaLabel: string;
  /** Data drawn over the land but under the political borders (polygons). */
  children?: ReactNode;
  /** Data drawn over the political borders (coastline segments). */
  overlay?: ReactNode;
}

export function MapFrame({
  projection,
  basemapPaths,
  ariaLabel,
  children,
  overlay,
}: MapFrameProps) {
  const { width, height, extent } = projection;
  const longitudes: number[] = [];
  for (let lon = Math.ceil(extent.west / 5) * 5; lon <= extent.east; lon += 5) {
    longitudes.push(lon);
  }
  const latitudes: number[] = [];
  for (let lat = Math.ceil(extent.south / 5) * 5; lat <= extent.north; lat += 5) {
    latitudes.push(lat);
  }

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="block h-auto w-full"
      role="img"
      aria-label={ariaLabel}
    >
      <rect width={width} height={height} fill={MAP_COLORS.ocean} />

      {basemapPaths.land.map((path, index) => (
        <path key={`land-${index}`} d={path} fill={MAP_COLORS.land} fillRule="evenodd" />
      ))}

      {longitudes.map((lon) => {
        const { x } = projection.project(lon, extent.north);
        return (
          <g key={`grat-lon-${lon}`}>
            <line
              x1={x}
              y1={0}
              x2={x}
              y2={height}
              stroke={MAP_COLORS.graticule}
              strokeWidth={0.4}
              strokeDasharray="3 3"
              opacity={0.55}
            />
            <text
              x={x}
              y={height - 4}
              textAnchor="middle"
              fill="#374151"
              style={{ fontSize: '8px' }}
            >
              {Math.abs(lon)}°W
            </text>
          </g>
        );
      })}
      {latitudes.map((lat) => {
        const { y } = projection.project(extent.west, lat);
        return (
          <g key={`grat-lat-${lat}`}>
            <line
              x1={0}
              y1={y}
              x2={width}
              y2={y}
              stroke={MAP_COLORS.graticule}
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

      {children}

      {basemapPaths.state.map((path, index) => (
        <path
          key={`state-${index}`}
          d={path}
          fill="none"
          stroke={MAP_COLORS.stateBorder}
          strokeWidth={0.5}
        />
      ))}
      {basemapPaths.country.map((path, index) => (
        <path
          key={`country-${index}`}
          d={path}
          fill="none"
          stroke={MAP_COLORS.countryBorder}
          strokeWidth={0.8}
        />
      ))}

      {overlay}
    </svg>
  );
}

/* ── Discrete classes ──────────────────────────────────────────────────── */

/** Discrete class of a value, mirroring numpy.digitize(v, boundaries[1:-1]). */
export function classIndex(value: number, boundaries: number[]): number {
  const classes = boundaries.length - 1;
  for (let i = 1; i < classes; i += 1) {
    if (value < boundaries[i]) return i - 1;
  }
  return classes - 1;
}

function roundTo(value: number, step: number): number {
  const decimals = Math.max(0, Math.min(6, -Math.floor(Math.log10(step)) + 1));
  return Number(value.toFixed(decimals));
}

/**
 * Rounded class limits covering [min, max] with about `count` classes, so the
 * legend reads in human numbers instead of raw data extremes.
 */
export function niceBreaks(min: number, max: number, count: number): number[] {
  if (!Number.isFinite(min) || !Number.isFinite(max)) return [0, 1];
  if (min === max) {
    const pad = Math.abs(min) > 0 ? Math.abs(min) * 0.1 : 0.5;
    return [min - pad, min + pad];
  }
  const rawStep = (max - min) / count;
  const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)));
  const normalized = rawStep / magnitude;
  const nice = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 2.5 ? 2.5 : normalized <= 5 ? 5 : 10;
  const step = nice * magnitude;
  const start = Math.floor(min / step) * step;
  const breaks: number[] = [];
  for (let value = start; value < max + step * 0.5; value += step) {
    breaks.push(roundTo(value, step));
  }
  if (breaks.length < 2) breaks.push(roundTo(start + step, step));
  // Guarantee the top class limit sits above the largest observed value, so no
  // value falls outside the legend.
  while (breaks[breaks.length - 1] < max) {
    breaks.push(roundTo(breaks[breaks.length - 1] + step, step));
  }
  return breaks;
}

/** Symmetric class limits around zero, for signed quantities. */
export function symmetricBreaks(min: number, max: number, count: number): number[] {
  const limit = Math.max(Math.abs(min), Math.abs(max));
  if (!Number.isFinite(limit) || limit === 0) return [-1, 0, 1];
  const half = count % 2 === 0 ? count / 2 : Math.ceil(count / 2);
  const rawStep = limit / half;
  const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)));
  const normalized = rawStep / magnitude;
  const nice = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 2.5 ? 2.5 : normalized <= 5 ? 5 : 10;
  const step = nice * magnitude;
  const breaks: number[] = [];
  for (let i = -half; i <= half; i += 1) breaks.push(roundTo(i * step, step));
  return breaks;
}

export function formatValue(value: number | null | undefined, decimals: number): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return 'No data';
  if (decimals < 0) return value.toExponential(2);
  return value.toFixed(decimals);
}

export function decimalsFor(boundaries: number[]): number {
  const span = Math.abs(boundaries[boundaries.length - 1] - boundaries[0]);
  if (span === 0) return 2;
  if (span >= 100) return 0;
  if (span >= 10) return 1;
  if (span >= 1) return 2;
  if (span >= 0.1) return 3;
  return -1;
}

export const MONTH_NAMES = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
];

/* ── Legend ────────────────────────────────────────────────────────────── */

interface DiscreteLegendProps {
  title: string;
  unit: string;
  boundaries: number[];
  colors: string[];
  decimals: number;
  /** Render class labels as month names instead of numbers. */
  monthLabels?: boolean;
  note?: ReactNode;
}

export function DiscreteLegend({
  title,
  unit,
  boundaries,
  colors,
  decimals,
  monthLabels = false,
  note,
}: DiscreteLegendProps) {
  const format = (value: number) => {
    if (monthLabels) return MONTH_NAMES[Math.round(value) - 1] ?? String(value);
    return formatValue(value, decimals);
  };
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Legend</p>
      <h3 className="mt-1 text-sm font-bold text-gray-900">
        {title} <span className="font-normal text-gray-500">({unit})</span>
      </h3>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2">
        {colors.map((color, index) => {
          const lower = boundaries[index];
          const upper = boundaries[index + 1];
          const isFirst = index === 0;
          const isLast = index === colors.length - 1;
          const label = monthLabels
            ? format(lower)
            : isFirst
              ? `< ${format(upper)}`
              : isLast
                ? `≥ ${format(lower)}`
                : `${format(lower)} – ${format(upper)}`;
          return (
            <div key={`${color}-${index}`} className="flex items-center gap-1.5">
              <span
                className="inline-block h-3 w-6 rounded-sm border border-black/10"
                style={{ backgroundColor: color }}
              />
              <span className="font-mono text-[10px] text-gray-600">{label}</span>
            </div>
          );
        })}
      </div>
      {note}
    </div>
  );
}

/* ── Stat card ─────────────────────────────────────────────────────────── */

export function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3">
      <div className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-gray-500">
        {label}
      </div>
      <div className="text-sm font-bold leading-snug break-words text-gray-900">{value}</div>
    </div>
  );
}
