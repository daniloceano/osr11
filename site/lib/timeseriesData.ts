'use client';

/**
 * On-demand loading of the per-grid-point time series.
 *
 * The index is small and is fetched once, with the coastal layers, so the map
 * can draw its markers. Each point file carries 33 years of daily record and
 * weighs about 150 KB, so it is fetched only when the reader opens that point,
 * and then kept for the rest of the session.
 */

export interface TimeSeriesThresholds {
  thr_hs_abs_m: number;
  thr_zos_abs_m: number;
  thr_zos_anomaly_m: number;
  zos_mean_m: number;
  mhws_m: number;
}

export interface TimeSeriesPointMetrics {
  compound_count_total: number | null;
  compound_count_annual_mean: number | null;
  mean_overlap_duration: number | null;
  mean_full_criterion_duration: number | null;
  mean_compound_intensity_norm: number | null;
  mean_integrated_severity: number | null;
  n_candidate_events: number | null;
  n_rejected_by_mhws: number | null;
}

export interface TimeSeriesSelectionFeatures {
  surge_q99_over_swing: number;
  mhws_m: number;
  thr_hs_abs: number;
  Hazard_Frequency: number;
  Hazard_Severity: number;
}

export interface TimeSeriesIndexEntry {
  point_id: string;
  lat: number;
  lon: number;
  label: string;
  state: string;
  latitude_band: string;
  file: string;
  file_size_kb: number;
  n_municipalities_served: number;
  n_events: number;
  selection_features: TimeSeriesSelectionFeatures;
  thresholds: TimeSeriesThresholds;
  point_metrics: TimeSeriesPointMetrics;
}

export interface TimeSeriesIndex {
  generated_at: string;
  implementation: string;
  source_dataset: string;
  detection: string;
  period: { start: string; end: string; years: number };
  selection: { frozen_at: string; implementation: string; rule: string };
  index_components: Record<string, string>;
  retired_from_index: { fields: string[]; retired_on: string; note: string };
  points: TimeSeriesIndexEntry[];
}

/** A candidate level datum, with what the same detector does under it. */
export interface LevelDatum {
  key: string;
  label: string;
  value_m: number;
  source: string;
  in_force: boolean;
  n_events: number;
  n_rejected: number;
  n_event_days: number;
  /** Share of accepted events the tide alone would have carried over. */
  frac_tide_alone: number | null;
  mean_meteo_term_m: number | null;
  mean_astro_term_m: number | null;
}

export interface CompoundEvent {
  start_index: number;
  end_index: number;
  /** Days on which all three criteria hold; not necessarily contiguous. */
  full_indices: number[];
  overlap_duration_days: number;
  full_criterion_duration_days: number;
  peak_hs_m: number;
  max_swl_m: number;
  exc_level_m: number;
  peak_intensity_norm: number;
  integrated_severity: number;
}

export interface PointTimeSeries {
  point_id: string;
  lat: number;
  lon: number;
  label: string;
  state: string;
  period: { start: string; end: string; n_days: number };
  thresholds: TimeSeriesThresholds;
  point_metrics: TimeSeriesPointMetrics;
  index_components: string[];
  datums: LevelDatum[];
  selection_features: TimeSeriesSelectionFeatures;
  daily: {
    units: string;
    note: string;
    hs_cm: (number | null)[];
    zos_anomaly_cm: (number | null)[];
    tide_cm: (number | null)[];
  };
  monthly: {
    month_start: string[];
    hs_mean_cm: (number | null)[];
    swl_max_cm: (number | null)[];
    event_days: number[];
  };
  events: CompoundEvent[];
}

const BASE = '/data/timeseries';

async function loadJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to load ${url}: ${response.status}`);
  return (await response.json()) as T;
}

let indexPromise: Promise<TimeSeriesIndex> | null = null;
const pointPromises = new Map<string, Promise<PointTimeSeries>>();

export function loadTimeSeriesIndex(): Promise<TimeSeriesIndex> {
  if (!indexPromise) {
    indexPromise = loadJson<TimeSeriesIndex>(`${BASE}/index.json`).catch(
      (error: unknown) => {
        indexPromise = null;
        throw error;
      },
    );
  }
  return indexPromise;
}

export function loadPointTimeSeries(entry: TimeSeriesIndexEntry): Promise<PointTimeSeries> {
  const cached = pointPromises.get(entry.point_id);
  if (cached) return cached;
  const promise = loadJson<PointTimeSeries>(`${BASE}/${entry.file}`).catch(
    (error: unknown) => {
      pointPromises.delete(entry.point_id);
      throw error;
    },
  );
  pointPromises.set(entry.point_id, promise);
  return promise;
}
