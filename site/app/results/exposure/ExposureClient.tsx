'use client';

import { useEffect, useState } from 'react';
import ExposureMap, {
  type ExposureGeoJson,
  type ExposureMetadata,
} from '@/components/ExposureMap';
import type { CoastalBasemap } from '@/components/coastalMap';

const DATA_URL = '/data/exposure_municipalities.geojson';
const METADATA_URL = '/data/exposure_metadata.json';
const BASEMAP_URL = '/data/coastal_basemap.geojson';

async function loadJson<T>(url: string, label: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to load ${label}: ${response.status}`);
  return (await response.json()) as T;
}

export default function ExposureClient() {
  const [data, setData] = useState<ExposureGeoJson | null>(null);
  const [metadata, setMetadata] = useState<ExposureMetadata | null>(null);
  const [basemap, setBasemap] = useState<CoastalBasemap | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      loadJson<ExposureGeoJson>(DATA_URL, 'exposure GeoJSON'),
      loadJson<ExposureMetadata>(METADATA_URL, 'exposure metadata'),
      loadJson<CoastalBasemap>(BASEMAP_URL, 'map basemap'),
    ])
      .then(([exposureData, exposureMetadata, mapBasemap]) => {
        if (!exposureData.features?.length) {
          throw new Error('Exposure GeoJSON loaded, but it contains no municipality features.');
        }
        if (!exposureMetadata.available_layers?.length) {
          throw new Error('Exposure metadata loaded, but no available layers were detected.');
        }
        setData(exposureData);
        setMetadata(exposureMetadata);
        setBasemap(mapBasemap);
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
            python -m src.risk_integration.municipal_exposure
          </code>{' '}
          and{' '}
          <code className="rounded bg-red-100 px-1 font-mono">
            python -m src.site.export_exposure_data
          </code>{' '}
          from the repository root to regenerate the web data files.
        </p>
      </div>
    );
  }

  if (!data || !metadata || !basemap) {
    return (
      <div className="flex h-72 items-center justify-center rounded-lg border border-gray-200 bg-gray-50">
        <p className="text-sm text-gray-500">Loading exposure layers…</p>
      </div>
    );
  }

  return <ExposureMap data={data} metadata={metadata} basemap={basemap} />;
}
