'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import CoastalHazardMap from '@/components/CoastalHazardMap';
import CompoundTimeSeriesChart from '@/components/CompoundTimeSeriesChart';
import HazardCharacterizationMap from '@/components/HazardCharacterizationMap';
import { loadCoastalBundle, type CoastalBundle } from '@/lib/coastalData';
import {
  loadPointTimeSeries,
  loadTimeSeriesIndex,
  type PointTimeSeries,
  type TimeSeriesIndex,
  type TimeSeriesIndexEntry,
} from '@/lib/timeseriesData';

function useCoastalBundle() {
  const [bundle, setBundle] = useState<CoastalBundle | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    loadCoastalBundle()
      .then((loaded) => {
        if (active) setBundle(loaded);
      })
      .catch((err: Error) => {
        if (active) setError(err.message);
      });
    return () => {
      active = false;
    };
  }, []);

  return { bundle, error };
}

function LoadFailure({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
      <p className="text-sm text-red-700">{message}</p>
      <p className="mt-2 text-xs text-red-500">
        Run{' '}
        <code className="rounded bg-red-100 px-1 font-mono">
          python -m src.site.export_coastal_hazard_data
        </code>{' '}
        from the repository root to regenerate the coastal layers.
      </p>
    </div>
  );
}

function Loading({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center py-24">
      <div className="text-center">
        <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  );
}

export default function CoastalHazardClient() {
  const { bundle, error } = useCoastalBundle();
  const [timeSeriesIndex, setTimeSeriesIndex] = useState<TimeSeriesIndex | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [point, setPoint] = useState<PointTimeSeries | null>(null);
  const [pointError, setPointError] = useState<string | null>(null);
  const [pointLoading, setPointLoading] = useState(false);
  //  Kept outside React state so that ``openPoint`` stays referentially stable
  //  and the index is fetched exactly once.
  const openedId = useRef<string | null>(null);

  const openPoint = useCallback((entry: TimeSeriesIndexEntry) => {
    if (openedId.current === entry.point_id) return;
    openedId.current = entry.point_id;
    setSelectedId(entry.point_id);
    setPointError(null);
    setPointLoading(true);
    // A point is worth linking to from the manuscript or an email, so the open
    // point lives in the URL fragment.
    window.history.replaceState(null, '', `#point=${entry.point_id}`);
    loadPointTimeSeries(entry)
      .then((loaded) => {
        setPoint(loaded);
        setPointLoading(false);
      })
      .catch((err: Error) => {
        setPointError(err.message);
        setPointLoading(false);
      });
  }, []);

  /* The index is a few kilobytes and only names the points; the daily record of
   * a point is fetched when that point is opened, or straight away when the URL
   * fragment already names one. */
  useEffect(() => {
    let active = true;
    loadTimeSeriesIndex()
      .then((loaded) => {
        if (!active) return;
        setTimeSeriesIndex(loaded);
        const match = /(?:^|#|&)point=([\w-]+)/.exec(window.location.hash);
        const entry = match
          ? loaded.points.find((candidate) => candidate.point_id === match[1])
          : undefined;
        if (entry) openPoint(entry);
      })
      .catch(() => {
        // The panel is supplementary: if its data has not been exported, the
        // Hazard Index map must still render.
      });
    return () => {
      active = false;
    };
  }, [openPoint]);

  if (error) return <LoadFailure message={error} />;
  if (!bundle) return <Loading label="Loading coastal Hazard Index layers…" />;

  const entries = timeSeriesIndex?.points ?? [];

  return (
    <div className="space-y-6">
      <CoastalHazardMap
        data={bundle.segments}
        metadata={bundle.metadata}
        basemap={bundle.basemap}
        markers={entries.map((entry) => ({
          id: entry.point_id,
          lat: entry.lat,
          lon: entry.lon,
          label: `${entry.label}, ${entry.state}`,
        }))}
        selectedMarkerId={selectedId}
        onMarkerSelect={(id) => {
          const entry = entries.find((candidate) => candidate.point_id === id);
          if (entry) openPoint(entry);
        }}
      />

      {entries.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-blue-600">
            Behind the map
          </p>
          <h3 className="text-lg font-bold text-gray-900">
            The daily record at {entries.length} grid points
          </h3>
          <p className="mt-2 max-w-3xl text-[11px] leading-relaxed text-gray-500">
            The dots on the map open the daily series that the detection actually reads —
            wave height, tide-free sea level and astronomical tide — with the compound
            events shaded. The points were chosen by the data, not by hand: they are the
            medoids of equal-count strata of the surge-to-tide ratio in a standardised
            space of physical features, taken over the grid points that serve at least one
            municipality. The municipality names are labels attached after the selection,
            never a criterion. The rule is frozen in{' '}
            <code className="rounded bg-gray-100 px-1 font-mono text-[10px]">
              {timeSeriesIndex?.selection.frozen_at}
            </code>
            .
          </p>

          <div className="mt-4 flex flex-wrap gap-1.5">
            {entries.map((entry) => (
              <button
                key={entry.point_id}
                type="button"
                onClick={() => openPoint(entry)}
                aria-pressed={entry.point_id === selectedId}
                className={`rounded-md border px-2.5 py-1.5 text-[11px] font-medium transition-colors ${
                  entry.point_id === selectedId
                    ? 'border-blue-600 bg-blue-50 text-blue-700'
                    : 'border-gray-300 bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                {entry.label}
                <span className="ml-1 text-gray-400">{entry.state}</span>
              </button>
            ))}
          </div>

          <div className="mt-5 border-t border-gray-100 pt-5">
            {pointError && (
              <p className="text-xs text-red-600">
                Could not load this point: {pointError}
              </p>
            )}
            {!pointError && pointLoading && (
              <Loading label="Loading 33 years of daily record…" />
            )}
            {!pointError && !pointLoading && point && (
              <CompoundTimeSeriesChart point={point} />
            )}
            {!pointError && !pointLoading && !point && (
              <p className="py-6 text-center text-xs text-gray-500">
                Select a point above, or click one of the dots on the map, to open its
                daily record.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export function CoastalMetricExplorerClient() {
  const { bundle, error } = useCoastalBundle();
  if (error) return <LoadFailure message={error} />;
  if (!bundle) return <Loading label="Loading the 87-metric coastal explorer…" />;
  return (
    <HazardCharacterizationMap
      data={bundle.metrics}
      segments={bundle.segments}
      coastalMetadata={bundle.metadata}
      basemap={bundle.basemap}
    />
  );
}
