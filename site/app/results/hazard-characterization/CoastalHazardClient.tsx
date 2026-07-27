'use client';

import { useEffect, useState } from 'react';
import CoastalHazardMap from '@/components/CoastalHazardMap';
import type {
  CoastalBasemap,
  CoastalHazardGeoJson,
  CoastalHazardMetadata,
} from '@/components/CoastalHazardMap';

export default function CoastalHazardClient() {
  const [data, setData] = useState<CoastalHazardGeoJson | null>(null);
  const [metadata, setMetadata] = useState<CoastalHazardMetadata | null>(null);
  const [basemap, setBasemap] = useState<CoastalBasemap | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async <T,>(url: string): Promise<T> => {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Failed to load ${url}: ${response.status}`);
      return (await response.json()) as T;
    };

    Promise.all([
      load<CoastalHazardGeoJson>('/data/coastal_hazard_segments.geojson'),
      load<CoastalHazardMetadata>('/data/coastal_hazard_metadata.json'),
      load<CoastalBasemap>('/data/coastal_basemap.geojson'),
    ])
      .then(([segments, meta, base]) => {
        setData(segments);
        setMetadata(meta);
        setBasemap(base);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <p className="text-sm text-red-700">{error}</p>
        <p className="mt-2 text-xs text-red-500">
          Run{' '}
          <code className="rounded bg-red-100 px-1 font-mono">
            python -m src.site.export_coastal_hazard_data
          </code>{' '}
          from the repository root to regenerate the coastal hazard layers.
        </p>
      </div>
    );
  }

  if (!data || !metadata || !basemap) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
          <p className="text-sm text-gray-500">Loading coastal Hazard Index layers…</p>
        </div>
      </div>
    );
  }

  return <CoastalHazardMap data={data} metadata={metadata} basemap={basemap} />;
}
