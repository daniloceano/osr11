'use client';

/**
 * Daily record and compound events at one ocean grid point, in plain SVG.
 *
 * The site carries no charting library and its maps are hand-written SVG, so
 * this follows the same pattern. Thirty-three years cannot be drawn as one
 * daily path — 12 053 vertices render but stall on interaction, and at 800 px
 * a pixel would hold a fortnight — so the panel is an overview plus a detail:
 * a monthly strip for navigation and seasonality, and a 90-day window at daily
 * resolution, which is where the physics is legible. Ninety days span four to
 * six spring-neap cycles, enough for the tide-dominated north and the
 * surge-dominated south to look plainly different.
 *
 * One panel per criterion, stacked on a shared time axis and never sharing a
 * y-axis: the wave height against its q90; the still water level against the
 * MHWS, with the tide that carries it; and the tide-free sea level `zos`
 * against its q90. The last panel shows `zos` exactly as the detector reads
 * it — in the model's own vertical reference, against the threshold value
 * recorded in the catalogue — while the still water level keeps the local mean
 * removed, which is what makes it comparable with the MHWS.
 */

import { useCallback, useMemo, useRef, useState } from 'react';
import type { PointTimeSeries } from '@/lib/timeseriesData';

/* ── Geometry ──────────────────────────────────────────────────────────── */

const WIDTH = 880;
const MARGIN = { left: 52, right: 96, top: 10, bottom: 4 };
const WAVE_HEIGHT = 104;
const PANEL_GAP = 30;
const LEVEL_HEIGHT = 150;
const ZOS_HEIGHT = 96;
const AXIS_HEIGHT = 18;
const DETAIL_HEIGHT =
  MARGIN.top +
  WAVE_HEIGHT +
  PANEL_GAP +
  LEVEL_HEIGHT +
  PANEL_GAP +
  ZOS_HEIGHT +
  AXIS_HEIGHT +
  MARGIN.bottom;
const PLOT_WIDTH = WIDTH - MARGIN.left - MARGIN.right;
const WAVE_TOP = MARGIN.top;
const LEVEL_TOP = MARGIN.top + WAVE_HEIGHT + PANEL_GAP;
const ZOS_TOP = LEVEL_TOP + LEVEL_HEIGHT + PANEL_GAP;
const PLOT_BOTTOM = ZOS_TOP + ZOS_HEIGHT;

const OVERVIEW_HEIGHT = 84;
const OVERVIEW_PLOT_TOP = 8;
const OVERVIEW_PLOT_HEIGHT = 44;
const OVERVIEW_BARS_TOP = OVERVIEW_PLOT_TOP + OVERVIEW_PLOT_HEIGHT + 6;
const OVERVIEW_BARS_HEIGHT = 12;

const WINDOW_DAYS = 90;
/** Approximate rendered height of the event tooltip, used to flip it. */
const TOOLTIP_HEIGHT = 330;

/* ── Colors ───────────────────────────────────────────────────────────────
 * Categorical slots 1, 2, 7 and 3 of the reference palette, validated with
 * scripts/validate_palette.js against a white surface: lightness band, chroma
 * floor, all-pairs CVD separation and normal-vision separation all pass. The
 * aqua sits just under the 3:1 contrast target, so every series carries a
 * legend entry and a direct label rather than relying on color alone.
 */
const SERIES = {
  swl: '#2a78d6',
  zos: '#eb6834',
  tide: '#4a3aa7',
  hs: '#1baf7a',
} as const;
const INK = { primary: '#111827', secondary: '#374151', muted: '#6b7280' };
const GRID = '#e5e7eb';
const REFERENCE = '#4b5563';

/* ── Small helpers ─────────────────────────────────────────────────────── */

function toMetres(values: (number | null)[]): (number | null)[] {
  return values.map((value) => (value === null ? null : value / 100));
}

function dayLabel(startISO: string, index: number, withYear = true): string {
  const [year, month, day] = startISO.split('-').map(Number);
  const date = new Date(Date.UTC(year, month - 1, day + index));
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    ...(withYear ? { year: 'numeric' } : {}),
    timeZone: 'UTC',
  });
}

/** Axis ticks on 1/2/5 × 10^n steps covering [min, max]. */
function niceTicks(min: number, max: number, target: number): number[] {
  if (!Number.isFinite(min) || !Number.isFinite(max) || max <= min) return [min];
  const raw = (max - min) / target;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const normalized = raw / magnitude;
  const step =
    (normalized >= 5 ? 10 : normalized >= 2 ? 5 : normalized >= 1 ? 2 : 1) * magnitude;
  const ticks: number[] = [];
  for (let v = Math.ceil(min / step) * step; v <= max + 1e-9; v += step) {
    ticks.push(Number(v.toFixed(6)));
  }
  return ticks;
}

/** Path with gaps where the record is missing. */
function linePath(
  values: (number | null)[],
  xOf: (index: number) => number,
  yOf: (value: number) => number,
): string {
  let path = '';
  let pen = false;
  values.forEach((value, index) => {
    if (value === null || !Number.isFinite(value)) {
      pen = false;
      return;
    }
    path += `${pen ? 'L' : 'M'}${xOf(index).toFixed(2)} ${yOf(value).toFixed(2)}`;
    pen = true;
  });
  return path;
}

interface EdgeLabel {
  y: number;
  text: string;
  color: string;
  bold?: boolean;
}

/**
 * Push right-margin labels apart so none is written over another.
 *
 * Series and reference lines can end the window at almost the same level —
 * where the tide carries the whole signal, `zos′ + tide` and `tide` are within
 * a few centimetres of each other — and unseparated labels would overprint.
 */
function deCollide(labels: EdgeLabel[], top: number, bottom: number, gap = 11): EdgeLabel[] {
  const ordered = [...labels].sort((a, b) => a.y - b.y);
  for (let i = 1; i < ordered.length; i += 1) {
    ordered[i] = { ...ordered[i], y: Math.max(ordered[i].y, ordered[i - 1].y + gap) };
  }
  const overflow = ordered[ordered.length - 1].y - bottom;
  if (overflow > 0) {
    for (let i = ordered.length - 1; i >= 0; i -= 1) {
      const ceiling = i === ordered.length - 1 ? bottom : ordered[i + 1].y - gap;
      ordered[i] = { ...ordered[i], y: Math.max(top, Math.min(ordered[i].y, ceiling)) };
    }
  }
  return ordered;
}

/** Consecutive day indices grouped into runs, for the event shading. */
function runsOf(indices: number[]): Array<[number, number]> {
  const runs: Array<[number, number]> = [];
  for (const index of indices) {
    const last = runs[runs.length - 1];
    if (last && index === last[1] + 1) last[1] = index;
    else runs.push([index, index]);
  }
  return runs;
}

function format(value: number | null | undefined, decimals: number): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
  return value.toFixed(decimals);
}

/* ── Component ─────────────────────────────────────────────────────────── */

export default function CompoundTimeSeriesChart({ point }: { point: PointTimeSeries }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(WIDTH);
  const [hoveredEvent, setHoveredEvent] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [hoverDay, setHoverDay] = useState<number | null>(null);
  /* The candidate datums of the AUD-01 sensitivity. Only MHWS is in force; the
   * others are drawn so the reader can see where the event condition would move
   * without re-running anything. */
  const [showDatums, setShowDatums] = useState(true);

  const nDays = point.period.n_days;
  const series = useMemo(
    () => ({
      hs: toMetres(point.daily.hs_cm),
      zos: toMetres(point.daily.zos_anomaly_cm),
      tide: toMetres(point.daily.tide_cm),
    }),
    [point],
  );
  const swl = useMemo(
    () =>
      series.zos.map((zos, index) => {
        const tide = series.tide[index];
        return zos === null || tide === null ? null : zos + tide;
      }),
    [series],
  );
  /* The payload stores the de-meaned series, because that is what the still
   * water level is built from; adding the local mean back recovers `zos` in
   * the reference the detector and the catalogue threshold use. */
  const zosRaw = useMemo(
    () =>
      series.zos.map((value) =>
        value === null ? null : value + point.thresholds.zos_mean_m,
      ),
    [series.zos, point.thresholds.zos_mean_m],
  );

  /* The window opens on the most severe event, so the reader lands on the
   * phenomenon rather than on an arbitrary stretch of 1993. */
  const strongestEvent = useMemo(() => {
    if (point.events.length === 0) return null;
    return point.events.reduce((best, event) =>
      event.integrated_severity > best.integrated_severity ? event : best,
    );
  }, [point.events]);

  const clampStart = useCallback(
    (value: number) => Math.max(0, Math.min(Math.round(value), nDays - WINDOW_DAYS)),
    [nDays],
  );
  const [start, setStart] = useState(() =>
    clampStart(
      strongestEvent
        ? (strongestEvent.start_index + strongestEvent.end_index) / 2 - WINDOW_DAYS / 2
        : nDays / 2,
    ),
  );
  const end = Math.min(start + WINDOW_DAYS, nDays);

  /* ── Scales ─────────────────────────────────────────────────────────── */

  const xOf = useCallback(
    (index: number) =>
      MARGIN.left + ((index - start) / (WINDOW_DAYS - 1)) * PLOT_WIDTH,
    [start],
  );

  const waveScale = useMemo(() => {
    const window_ = series.hs.slice(start, end).filter((v): v is number => v !== null);
    const max = Math.max(point.thresholds.thr_hs_abs_m, ...(window_.length ? window_ : [1]));
    const top = max * 1.12;
    return {
      top,
      yOf: (value: number) => WAVE_TOP + WAVE_HEIGHT - (value / top) * WAVE_HEIGHT,
    };
  }, [series.hs, start, end, point.thresholds.thr_hs_abs_m]);

  const levelScale = useMemo(() => {
    // MHWS is forced into the range so the line that defines an event is always
    // on screen, even in a window where the level never approaches it.
    const values: number[] = showDatums
      ? point.datums.map((datum) => datum.value_m)
      : [point.thresholds.mhws_m];
    for (let index = start; index < end; index += 1) {
      for (const value of [series.tide[index], swl[index]]) {
        if (value !== null && Number.isFinite(value)) values.push(value);
      }
    }
    const min = Math.min(...values);
    const max = Math.max(...values);
    const pad = (max - min) * 0.1 || 0.1;
    const lower = min - pad;
    const upper = max + pad;
    return {
      lower,
      upper,
      yOf: (value: number) =>
        LEVEL_TOP + LEVEL_HEIGHT - ((value - lower) / (upper - lower)) * LEVEL_HEIGHT,
    };
  }, [series, swl, start, end, point.thresholds.mhws_m, point.datums, showDatums]);

  const zosScale = useMemo(() => {
    // The q90 is forced into the range so the sea-level criterion is always
    // visible, even across a quiet window.
    const values: number[] = [point.thresholds.thr_zos_abs_m];
    for (let index = start; index < end; index += 1) {
      const value = zosRaw[index];
      if (value !== null && Number.isFinite(value)) values.push(value);
    }
    const min = Math.min(...values);
    const max = Math.max(...values);
    const pad = (max - min) * 0.12 || 0.05;
    const lower = min - pad;
    const upper = max + pad;
    return {
      lower,
      upper,
      yOf: (value: number) =>
        ZOS_TOP + ZOS_HEIGHT - ((value - lower) / (upper - lower)) * ZOS_HEIGHT,
    };
  }, [zosRaw, start, end, point.thresholds.thr_zos_abs_m]);

  /* ── Events in view ─────────────────────────────────────────────────── */

  const visibleEvents = useMemo(
    () =>
      point.events
        .map((event, index) => ({ event, index }))
        .filter(({ event }) => event.end_index >= start && event.start_index < end),
    [point.events, start, end],
  );

  const goToEvent = useCallback(
    (direction: -1 | 1) => {
      if (point.events.length === 0) return;
      const centre = start + WINDOW_DAYS / 2;
      const ordered =
        direction === 1
          ? point.events.filter((event) => event.start_index > centre + 2)
          : [...point.events].reverse().filter((event) => event.start_index < centre - 2);
      const target = ordered[0] ?? (direction === 1 ? point.events[0] : point.events.at(-1));
      if (!target) return;
      setHoveredEvent(null);
      setStart(
        clampStart((target.start_index + target.end_index) / 2 - WINDOW_DAYS / 2),
      );
    },
    [point.events, start, clampStart],
  );

  /* ── Overview strip ─────────────────────────────────────────────────── */

  const monthly = point.monthly;
  const overview = useMemo(() => {
    const swlMax = toMetres(monthly.swl_max_cm);
    const finite = swlMax.filter((v): v is number => v !== null);
    const min = Math.min(...finite);
    const max = Math.max(...finite);
    const pad = (max - min) * 0.08 || 0.1;
    const maxEventDays = Math.max(1, ...monthly.event_days);
    const step = PLOT_WIDTH / Math.max(1, monthly.month_start.length - 1);
    return {
      swlMax,
      xOf: (index: number) => MARGIN.left + index * step,
      yOf: (value: number) =>
        OVERVIEW_PLOT_TOP +
        OVERVIEW_PLOT_HEIGHT -
        ((value - min + pad) / (max - min + 2 * pad)) * OVERVIEW_PLOT_HEIGHT,
      barHeight: (days: number) => (days / maxEventDays) * OVERVIEW_BARS_HEIGHT,
      barWidth: Math.max(1.2, step * 0.8),
      maxEventDays,
    };
  }, [monthly]);

  const seekFromOverview = useCallback(
    (clientX: number) => {
      const node = containerRef.current?.querySelector('[data-overview]');
      if (!node) return;
      const rect = node.getBoundingClientRect();
      const scale = WIDTH / rect.width;
      const svgX = (clientX - rect.left) * scale;
      const fraction = (svgX - MARGIN.left) / PLOT_WIDTH;
      setStart(clampStart(fraction * nDays - WINDOW_DAYS / 2));
    },
    [clampStart, nDays],
  );

  const handleDetailMove = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    const container = containerRef.current;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    setContainerWidth(rect.width);
    setTooltipPos({ x: event.clientX - rect.left, y: event.clientY - rect.top });
  }, []);

  /* Bound to the <svg> rather than to a hit rectangle, so that the pointer
   * still drives the crosshair while it rests on an event band. */
  const handlePlotMove = useCallback(
    (event: React.MouseEvent<SVGSVGElement>) => {
      const rect = event.currentTarget.getBoundingClientRect();
      const svgX = ((event.clientX - rect.left) / rect.width) * WIDTH;
      const fraction = (svgX - MARGIN.left) / PLOT_WIDTH;
      if (fraction < 0 || fraction > 1) {
        setHoverDay(null);
        return;
      }
      const day = start + Math.round(fraction * (WINDOW_DAYS - 1));
      setHoverDay(Math.max(start, Math.min(day, end - 1)));
    },
    [start, end],
  );

  const readoutDay = hoverDay ?? null;
  const hovered = hoveredEvent !== null ? point.events[hoveredEvent] : null;

  const waveTicks = niceTicks(0, waveScale.top, 3);
  const levelTicks = niceTicks(levelScale.lower, levelScale.upper, 4);
  const zosTicks = niceTicks(zosScale.lower, zosScale.upper, 3);
  const dayTicks = [0, 15, 30, 45, 60, 75, 89].map((offset) => start + offset);

  const waveLabels = deCollide(
    [
      {
        y: waveScale.yOf(point.thresholds.thr_hs_abs_m),
        text: `q90 Hₛ = ${format(point.thresholds.thr_hs_abs_m, 2)} m`,
        color: INK.muted,
      },
      {
        y: waveScale.yOf(lastFinite(series.hs, end - 1) ?? 0),
        text: 'Hₛ',
        color: SERIES.hs,
        bold: true,
      },
    ],
    WAVE_TOP,
    WAVE_TOP + WAVE_HEIGHT,
  );
  const levelLabels = deCollide(
    [
      ...(showDatums
        ? point.datums
            .filter((datum) => !datum.in_force)
            .map((datum) => ({
              y: levelScale.yOf(datum.value_m),
              text: datum.label,
              color: INK.muted,
            }))
        : []),
      {
        y: levelScale.yOf(point.thresholds.mhws_m),
        text: `MHWS = ${format(point.thresholds.mhws_m, 2)} m`,
        color: INK.primary,
        bold: true,
      },
      {
        y: levelScale.yOf(lastFinite(swl, end - 1) ?? 0),
        text: 'zos′ + tide',
        color: SERIES.swl,
        bold: true,
      },
      {
        y: levelScale.yOf(lastFinite(series.tide, end - 1) ?? 0),
        text: 'tide',
        color: SERIES.tide,
        bold: true,
      },
    ],
    LEVEL_TOP,
    LEVEL_TOP + LEVEL_HEIGHT,
  );
  const zosLabels = deCollide(
    [
      {
        // Both the series and the threshold are in the model's own vertical
        // reference here: this is the comparison the detector performs.
        y: zosScale.yOf(point.thresholds.thr_zos_abs_m),
        text: `q90 zos = ${format(point.thresholds.thr_zos_abs_m, 2)} m`,
        color: INK.muted,
      },
      {
        y: zosScale.yOf(lastFinite(zosRaw, end - 1) ?? 0),
        text: 'zos',
        color: SERIES.zos,
        bold: true,
      },
    ],
    ZOS_TOP,
    ZOS_TOP + ZOS_HEIGHT,
  );

  return (
    <div ref={containerRef} className="relative" onMouseMove={handleDetailMove}>
      {/* ── Header: identity, window and navigation ──────────────────── */}
      <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h3 className="text-sm font-bold text-gray-900">
            {point.label} · {point.state}
            <span className="ml-2 font-mono text-[11px] font-normal text-gray-500">
              {Math.abs(point.lat).toFixed(1)}°S {Math.abs(point.lon).toFixed(1)}°W
            </span>
          </h3>
          <p className="text-[11px] text-gray-500">
            {dayLabel(point.period.start, start)} – {dayLabel(point.period.start, end - 1)}
            {' · '}
            {visibleEvents.length === 0
              ? 'no compound event in this window'
              : `${visibleEvents.length} compound event${visibleEvents.length > 1 ? 's' : ''} in this window`}
            {' · '}
            {point.events.length} in 1993–2025
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex cursor-pointer items-center gap-1.5 text-[11px] text-gray-600">
            <input
              type="checkbox"
              checked={showDatums}
              onChange={(event) => setShowDatums(event.target.checked)}
              className="rounded border-gray-300 text-blue-600"
            />
            Candidate datums
          </label>
          <div className="flex items-center gap-1.5">
          <NavButton onClick={() => setStart(clampStart(start - WINDOW_DAYS))} label="◀◀">
            Previous window
          </NavButton>
          <NavButton onClick={() => goToEvent(-1)} label="◀">
            Previous event
          </NavButton>
          <NavButton onClick={() => goToEvent(1)} label="▶">
            Next event
          </NavButton>
          <NavButton onClick={() => setStart(clampStart(start + WINDOW_DAYS))} label="▶▶">
            Next window
          </NavButton>
          </div>
        </div>
      </div>

      {/* ── Value readout, which also gives the aqua series a text label ─ */}
      <div className="mb-2 flex flex-wrap items-center gap-x-5 gap-y-1 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-[11px]">
        <span className="font-mono font-semibold text-gray-700">
          {readoutDay === null
            ? 'Hover the chart to read values'
            : dayLabel(point.period.start, readoutDay)}
        </span>
        <Readout color={SERIES.hs} label="Hₛ" value={readoutDay === null ? null : series.hs[readoutDay]} />
        <Readout color={SERIES.swl} label="Still water level" value={readoutDay === null ? null : swl[readoutDay]} />
        <Readout color={SERIES.zos} label="zos" value={readoutDay === null ? null : zosRaw[readoutDay]} />
        <Readout color={SERIES.tide} label="Astronomical tide" value={readoutDay === null ? null : series.tide[readoutDay]} />
      </div>

      {/* ── Detail window ────────────────────────────────────────────── */}
      <svg
        viewBox={`0 0 ${WIDTH} ${DETAIL_HEIGHT}`}
        className="block h-auto w-full"
        role="img"
        aria-label={`Daily significant wave height, sea level and astronomical tide at ${point.label}, with the detected compound events shaded`}
        onMouseMove={handlePlotMove}
        onMouseLeave={() => setHoverDay(null)}
      >
        <rect width={WIDTH} height={DETAIL_HEIGHT} fill="#ffffff" />

        {/* Days on which all three criteria hold, drawn behind everything. */}
        {visibleEvents.map(({ event, index }) =>
          runsOf(event.full_indices).map(([from, to], run) => {
            const x1 = xOf(Math.max(from, start) - 0.5);
            const x2 = xOf(Math.min(to, end - 1) + 0.5);
            return (
              <rect
                key={`event-${index}-${run}`}
                x={x1}
                y={WAVE_TOP}
                width={Math.max(1.5, x2 - x1)}
                height={PLOT_BOTTOM - WAVE_TOP}
                fill={INK.primary}
                opacity={hoveredEvent === index ? 0.16 : 0.07}
                pointerEvents="none"
              />
            );
          }),
        )}

        {/* ── Wave panel ─────────────────────────────────────────────── */}
        {waveTicks.map((tick) => (
          <g key={`wave-tick-${tick}`}>
            <line
              x1={MARGIN.left}
              y1={waveScale.yOf(tick)}
              x2={MARGIN.left + PLOT_WIDTH}
              y2={waveScale.yOf(tick)}
              stroke={GRID}
              strokeWidth={1}
            />
            <text
              x={MARGIN.left - 6}
              y={waveScale.yOf(tick) + 3}
              textAnchor="end"
              fill={INK.muted}
              style={{ fontSize: '9px' }}
            >
              {tick.toFixed(1)}
            </text>
          </g>
        ))}
        <text
          x={MARGIN.left}
          y={WAVE_TOP - 1}
          fill={INK.secondary}
          style={{ fontSize: '9.5px', fontWeight: 600 }}
        >
          Significant wave height Hₛ (m)
        </text>
        <ReferenceLine y={waveScale.yOf(point.thresholds.thr_hs_abs_m)} dash="4 3" />
        <path
          d={linePath(series.hs.slice(0, end), (i) => xOf(i), waveScale.yOf)}
          fill="none"
          stroke={SERIES.hs}
          strokeWidth={2}
          strokeLinejoin="round"
          clipPath="url(#wave-clip)"
        />

        {/* ── Level panel ────────────────────────────────────────────── */}
        {levelTicks.map((tick) => (
          <g key={`level-tick-${tick}`}>
            <line
              x1={MARGIN.left}
              y1={levelScale.yOf(tick)}
              x2={MARGIN.left + PLOT_WIDTH}
              y2={levelScale.yOf(tick)}
              stroke={GRID}
              strokeWidth={1}
            />
            <text
              x={MARGIN.left - 6}
              y={levelScale.yOf(tick) + 3}
              textAnchor="end"
              fill={INK.muted}
              style={{ fontSize: '9px' }}
            >
              {tick.toFixed(1)}
            </text>
          </g>
        ))}
        <text
          x={MARGIN.left}
          y={LEVEL_TOP - 1}
          fill={INK.secondary}
          style={{ fontSize: '9.5px', fontWeight: 600 }}
        >
          Level above local mean sea level (m)
        </text>
        {/* Candidate datums first, so the one in force is drawn over them. */}
        {showDatums &&
          point.datums
            .filter((datum) => !datum.in_force)
            .map((datum) => (
              <line
                key={`datum-${datum.key}`}
                x1={MARGIN.left}
                y1={levelScale.yOf(datum.value_m)}
                x2={MARGIN.left + PLOT_WIDTH}
                y2={levelScale.yOf(datum.value_m)}
                stroke={REFERENCE}
                strokeWidth={0.9}
                strokeDasharray="2 4"
                opacity={0.55}
              />
            ))}
        {/* The condition that defines an event: seeing it crossed is half the
            message, so it is labelled in place rather than left to the legend. */}
        <ReferenceLine y={levelScale.yOf(point.thresholds.mhws_m)} dash="6 3" emphasis />
        <path
          d={linePath(series.tide.slice(0, end), (i) => xOf(i), levelScale.yOf)}
          fill="none"
          stroke={SERIES.tide}
          strokeWidth={1.6}
          strokeLinejoin="round"
          clipPath="url(#level-clip)"
        />
        <path
          d={linePath(swl.slice(0, end), (i) => xOf(i), levelScale.yOf)}
          fill="none"
          stroke={SERIES.swl}
          strokeWidth={2.8}
          strokeLinejoin="round"
          clipPath="url(#level-clip)"
        />

        {/* ── Sea-level panel: the detection variable, unshifted ─────── */}
        {zosTicks.map((tick) => (
          <g key={`zos-tick-${tick}`}>
            <line
              x1={MARGIN.left}
              y1={zosScale.yOf(tick)}
              x2={MARGIN.left + PLOT_WIDTH}
              y2={zosScale.yOf(tick)}
              stroke={GRID}
              strokeWidth={1}
            />
            <text
              x={MARGIN.left - 6}
              y={zosScale.yOf(tick) + 3}
              textAnchor="end"
              fill={INK.muted}
              style={{ fontSize: '9px' }}
            >
              {tick.toFixed(2)}
            </text>
          </g>
        ))}
        <text
          x={MARGIN.left}
          y={ZOS_TOP - 1}
          fill={INK.secondary}
          style={{ fontSize: '9.5px', fontWeight: 600 }}
        >
          Tide-free sea level zos (m, as detected — GLORYS reference)
        </text>
        <ReferenceLine y={zosScale.yOf(point.thresholds.thr_zos_abs_m)} dash="4 3" />
        <path
          d={linePath(zosRaw.slice(0, end), (i) => xOf(i), zosScale.yOf)}
          fill="none"
          stroke={SERIES.zos}
          strokeWidth={1.8}
          strokeLinejoin="round"
          clipPath="url(#zos-clip)"
        />

        {/* Direct labels at the right edge, so identity never rests on hue. */}
        <EdgeLabels labels={waveLabels} />
        <EdgeLabels labels={levelLabels} />
        <EdgeLabels labels={zosLabels} />

        {/* ── Time axis ──────────────────────────────────────────────── */}
        {dayTicks.map((day) => (
          <text
            key={`day-${day}`}
            x={xOf(day)}
            y={PLOT_BOTTOM + 13}
            textAnchor="middle"
            fill={INK.muted}
            style={{ fontSize: '9px' }}
          >
            {dayLabel(point.period.start, day, day === dayTicks[0])}
          </text>
        ))}

        {/* Crosshair */}
        {readoutDay !== null && (
          <line
            x1={xOf(readoutDay)}
            y1={WAVE_TOP}
            x2={xOf(readoutDay)}
            y2={PLOT_BOTTOM}
            stroke={INK.primary}
            strokeWidth={0.8}
            strokeDasharray="2 2"
            opacity={0.5}
            pointerEvents="none"
          />
        )}

        {/* Hover targets for the events, drawn last so nothing covers them.
            They are transparent: the visible shading is the band underneath. */}
        {visibleEvents.map(({ event, index }) => {
          const x1 = xOf(Math.max(event.start_index, start) - 0.5);
          const x2 = xOf(Math.min(event.end_index, end - 1) + 0.5);
          return (
            <rect
              key={`event-hit-${index}`}
              x={x1}
              y={WAVE_TOP}
              width={Math.max(3, x2 - x1)}
              height={PLOT_BOTTOM - WAVE_TOP}
              fill="transparent"
              onMouseEnter={() => setHoveredEvent(index)}
              onMouseLeave={() => setHoveredEvent(null)}
              style={{ cursor: 'pointer' }}
            />
          );
        })}

        <defs>
          <clipPath id="wave-clip">
            <rect x={MARGIN.left} y={WAVE_TOP - 2} width={PLOT_WIDTH} height={WAVE_HEIGHT + 4} />
          </clipPath>
          <clipPath id="zos-clip">
            <rect x={MARGIN.left} y={ZOS_TOP - 2} width={PLOT_WIDTH} height={ZOS_HEIGHT + 4} />
          </clipPath>
          <clipPath id="level-clip">
            <rect x={MARGIN.left} y={LEVEL_TOP - 2} width={PLOT_WIDTH} height={LEVEL_HEIGHT + 4} />
          </clipPath>
        </defs>
      </svg>

      {/* ── Overview strip ───────────────────────────────────────────── */}
      <svg
        data-overview
        viewBox={`0 0 ${WIDTH} ${OVERVIEW_HEIGHT}`}
        className="mt-1 block h-auto w-full cursor-crosshair"
        role="img"
        aria-label="Monthly overview of the whole record, 1993 to 2025; click to move the detail window"
        onMouseDown={(event) => seekFromOverview(event.clientX)}
        onMouseMove={(event) => {
          if (event.buttons === 1) seekFromOverview(event.clientX);
        }}
      >
        <rect width={WIDTH} height={OVERVIEW_HEIGHT} fill="#ffffff" />
        <text x={MARGIN.left} y={OVERVIEW_PLOT_TOP - 1} fill={INK.secondary} style={{ fontSize: '9.5px', fontWeight: 600 }}>
          1993–2025 overview — monthly maximum still water level
        </text>
        <path
          d={linePath(overview.swlMax, overview.xOf, overview.yOf)}
          fill="none"
          stroke={SERIES.swl}
          strokeWidth={1}
          strokeLinejoin="round"
          opacity={0.85}
        />
        {monthly.event_days.map((days, index) =>
          days === 0 ? null : (
            <rect
              key={`bar-${index}`}
              x={overview.xOf(index) - overview.barWidth / 2}
              y={OVERVIEW_BARS_TOP + OVERVIEW_BARS_HEIGHT - overview.barHeight(days)}
              width={overview.barWidth}
              height={overview.barHeight(days)}
              fill={INK.primary}
              opacity={0.55}
              rx={0.6}
            />
          ),
        )}
        <text
          x={MARGIN.left + PLOT_WIDTH + 6}
          y={OVERVIEW_BARS_TOP + OVERVIEW_BARS_HEIGHT}
          fill={INK.muted}
          style={{ fontSize: '8.5px' }}
        >
          event days
        </text>

        {/* Window handle */}
        <rect
          x={MARGIN.left + (start / nDays) * PLOT_WIDTH}
          y={OVERVIEW_PLOT_TOP - 3}
          width={Math.max(3, (WINDOW_DAYS / nDays) * PLOT_WIDTH)}
          height={OVERVIEW_PLOT_HEIGHT + OVERVIEW_BARS_HEIGHT + 12}
          fill={SERIES.swl}
          opacity={0.16}
          stroke={SERIES.swl}
          strokeWidth={1}
        />

        {[1995, 2000, 2005, 2010, 2015, 2020, 2025].map((year) => {
          const index = monthly.month_start.indexOf(`${year}-01`);
          if (index < 0) return null;
          return (
            <text
              key={year}
              x={overview.xOf(index)}
              y={OVERVIEW_HEIGHT - 4}
              textAnchor="middle"
              fill={INK.muted}
              style={{ fontSize: '9px' }}
            >
              {year}
            </text>
          );
        })}
      </svg>

      {/* ── Legend ───────────────────────────────────────────────────── */}
      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[10.5px] text-gray-600">
        <LegendItem color={SERIES.hs} label="Hₛ (upper panel)" />
        <LegendItem color={SERIES.swl} label="Still water level zos′ + tide, zos′ = zos − local mean" width={3} />
        <LegendItem color={SERIES.zos} label="zos, the sea-level detection variable (bottom panel)" />
        <LegendItem color={SERIES.tide} label="Astronomical tide (daily maximum)" />
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-4 rounded-sm bg-gray-900/10" />
          Compound-event days (all three criteria)
        </span>
      </div>

      {/* ── Level-datum sensitivity ──────────────────────────────────── */}
      {showDatums && (
        <div className="mt-4 overflow-x-auto rounded-lg border border-gray-200">
          <table className="w-full min-w-[620px] text-left text-[10.5px]">
            <caption className="px-3 pt-2 text-left text-[10.5px] leading-relaxed text-gray-500">
              What the same detector does at this point under each candidate level
              datum. Only <strong className="text-gray-700">MHWS</strong> is in force;
              the shaded events above are its events. <em>Tide alone</em> is the share
              of accepted events in which the astronomical tide would have cleared the
              datum on the same days with no surge at all — the closer to zero, the
              more the level condition requires the weather. The excess splits exactly
              as <span className="font-mono">SWL − datum = zos′ + (tide − datum)</span>.
            </caption>
            <thead className="border-b border-gray-200 text-gray-500">
              <tr>
                <th className="px-3 py-1.5 font-semibold">Datum</th>
                <th className="px-3 py-1.5 text-right font-semibold">Level</th>
                <th className="px-3 py-1.5 text-right font-semibold">Events</th>
                <th className="px-3 py-1.5 text-right font-semibold">Rejected</th>
                <th className="px-3 py-1.5 text-right font-semibold">Tide alone</th>
                <th className="px-3 py-1.5 text-right font-semibold">Meteo term</th>
                <th className="px-3 py-1.5 text-right font-semibold">Astro term</th>
              </tr>
            </thead>
            <tbody className="text-gray-700">
              {point.datums.map((datum) => (
                <tr
                  key={datum.key}
                  className={datum.in_force ? 'bg-blue-50 font-semibold' : ''}
                >
                  <td className="px-3 py-1.5">
                    {datum.label}
                    {datum.in_force && (
                      <span className="ml-1.5 text-[9px] uppercase tracking-wide text-blue-700">
                        in force
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-1.5 text-right font-mono">
                    {format(datum.value_m, 2)} m
                  </td>
                  <td className="px-3 py-1.5 text-right font-mono">{datum.n_events}</td>
                  <td className="px-3 py-1.5 text-right font-mono">{datum.n_rejected}</td>
                  <td className="px-3 py-1.5 text-right font-mono">
                    {datum.frac_tide_alone === null
                      ? '—'
                      : `${(datum.frac_tide_alone * 100).toFixed(0)}%`}
                  </td>
                  <td className="px-3 py-1.5 text-right font-mono">
                    {format(datum.mean_meteo_term_m, 3)}
                  </td>
                  <td className="px-3 py-1.5 text-right font-mono">
                    {format(datum.mean_astro_term_m, 3)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Event tooltip ────────────────────────────────────────────── */}
      {hovered && (
        <div
          className="pointer-events-none absolute z-20 w-[268px] rounded-lg border border-gray-200 bg-white p-3 shadow-lg"
          style={{
            left: Math.max(6, Math.min(tooltipPos.x + 14, containerWidth - 280)),
            // Anchored above the pointer, but flipped below it near the top of
            // the panel, where the box would otherwise run off the card and
            // under the sticky navigation bar.
            ...(tooltipPos.y > TOOLTIP_HEIGHT
              ? { top: tooltipPos.y - 10, transform: 'translateY(-100%)' }
              : { top: tooltipPos.y + 18 }),
          }}
        >
          <div className="text-[11px] font-bold text-gray-900">Compound event</div>
          <div className="mb-2 font-mono text-[10px] text-gray-500">
            {dayLabel(point.period.start, hovered.start_index)} –{' '}
            {dayLabel(point.period.start, hovered.end_index)}
          </div>

          <div className="rounded-md border border-blue-200 bg-blue-50 p-2">
            <div className="mb-1 text-[9px] font-semibold uppercase tracking-wide text-blue-700">
              Enters the hazard index
            </div>
            {/* Stacked: the value is a sentence, and squeezing it into the
                right-hand column would wrap the label instead. */}
            <div className="text-[10.5px] font-semibold text-gray-900">
              Contribution to frequency
            </div>
            <div className="mb-1 font-mono text-[10.5px] text-gray-900">
              1 of {format(point.point_metrics.compound_count_total, 0)} events here
            </div>
            <MetricRow
              label="Integrated severity"
              value={format(hovered.integrated_severity, 3)}
              emphasis
            />
          </div>

          <div className="mt-2 space-y-0.5">
            <div className="mb-1 text-[9px] font-semibold uppercase tracking-wide text-gray-400">
              Diagnostics — published, outside the index since 2026-07-29
            </div>
            <MetricRow label="Overlap duration" value={`${hovered.overlap_duration_days} d`} />
            <MetricRow
              label="Three-criteria duration"
              value={`${hovered.full_criterion_duration_days} d`}
            />
            <MetricRow label="Peak intensity" value={format(hovered.peak_intensity_norm, 3)} />
            <MetricRow label="Peak Hₛ" value={`${format(hovered.peak_hs_m, 2)} m`} />
            <MetricRow label="Max still water level" value={`${format(hovered.max_swl_m, 2)} m`} />
            <MetricRow label="Excess over MHWS" value={`${format(hovered.exc_level_m, 2)} m`} />
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Presentational helpers ────────────────────────────────────────────── */

function lastFinite(values: (number | null)[], index: number): number | null {
  for (let i = index; i >= 0 && i > index - 30; i -= 1) {
    const value = values[i];
    if (value !== null && Number.isFinite(value)) return value;
  }
  return null;
}

function ReferenceLine({
  y,
  dash,
  emphasis = false,
}: {
  y: number;
  dash: string;
  emphasis?: boolean;
}) {
  return (
    <line
      x1={MARGIN.left}
      y1={y}
      x2={MARGIN.left + PLOT_WIDTH}
      y2={y}
      stroke={emphasis ? INK.primary : REFERENCE}
      strokeWidth={emphasis ? 1.4 : 1}
      strokeDasharray={dash}
      opacity={emphasis ? 0.9 : 0.6}
    />
  );
}

/** Right-margin labels, already pushed apart by {@link deCollide}. */
function EdgeLabels({ labels }: { labels: EdgeLabel[] }) {
  return (
    <>
      {labels.map((label) => (
        <text
          key={label.text}
          x={MARGIN.left + PLOT_WIDTH + 6}
          y={label.y + 3}
          fill={label.color}
          style={{ fontSize: '8.5px', fontWeight: label.bold ? 700 : 400 }}
        >
          {label.text}
        </text>
      ))}
    </>
  );
}

function LegendItem({ color, label, width = 2 }: { color: string; label: string; width?: number }) {
  return (
    <span className="flex items-center gap-1.5">
      <span
        className="inline-block w-4 rounded-full"
        style={{ backgroundColor: color, height: `${width}px` }}
      />
      {label}
    </span>
  );
}

function Readout({
  color,
  label,
  value,
}: {
  color: string;
  label: string;
  value: number | null;
}) {
  return (
    <span className="flex items-center gap-1.5 text-gray-600">
      <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
      {label}: <span className="font-mono text-gray-800">{format(value, 2)} m</span>
    </span>
  );
}

function MetricRow({
  label,
  value,
  emphasis = false,
}: {
  label: string;
  value: string;
  emphasis?: boolean;
}) {
  return (
    <div
      className={`flex items-baseline justify-between gap-3 text-[10.5px] ${
        emphasis ? 'font-semibold text-gray-900' : 'text-gray-600'
      }`}
    >
      <span>{label}</span>
      <span className="font-mono whitespace-nowrap">{value}</span>
    </div>
  );
}

function NavButton({
  onClick,
  label,
  children,
}: {
  onClick: () => void;
  label: string;
  children: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={children}
      aria-label={children}
      className="rounded-md border border-gray-300 bg-white px-2 py-1 font-mono text-[10px] text-gray-600 transition-colors hover:bg-gray-50 hover:text-gray-900"
    >
      {label}
    </button>
  );
}
