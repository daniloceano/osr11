'use client';

import { useEffect, useState } from 'react';
import CoastalStormMap from '@/components/CoastalStormMap';
import type { StormMapsData } from '@/components/CoastalStormMap';

export default function StormMapsClient() {
  const [data, setData] = useState<StormMapsData | null>(null);
  const [coastline, setCoastline] = useState<number[][][] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch('/data/storm_maps_grid_metrics.json').then(r => {
        if (!r.ok) throw new Error(`Failed to load grid metrics: ${r.status}`);
        return r.json();
      }),
      fetch('/data/brazil_coastline.json').then(r => {
        if (!r.ok) throw new Error(`Failed to load coastline: ${r.status}`);
        return r.json();
      }),
    ])
      .then(([metricsData, coastData]) => {
        setData(metricsData);
        setCoastline(coastData);
      })
      .catch(err => setError(err.message));
  }, []);

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
        <p className="text-sm text-red-700">{error}</p>
        <p className="mt-2 text-xs text-red-500">
          Run <code className="font-mono bg-red-100 px-1 rounded">python -m src.site.export_storm_maps_data</code> to generate the data files.
        </p>
      </div>
    );
  }

  if (!data || !coastline) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
          <p className="text-sm text-gray-500">Loading storm data (808 grid points)…</p>
        </div>
      </div>
    );
  }

  return <CoastalStormMap data={data} coastline={coastline} />;
}
