'use client';

import { useEffect, useState } from 'react';
import RiskIntegrationMap, {
  type RiskGeoJson,
  type RiskMetadata,
} from '@/components/RiskIntegrationMap';

export default function RiskIntegrationClient() {
  const [data, setData] = useState<RiskGeoJson | null>(null);
  const [metadata, setMetadata] = useState<RiskMetadata | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch('/data/risk_index_municipalities.geojson').then((r) => {
        if (!r.ok) throw new Error(`Failed to load risk-index GeoJSON: ${r.status}`);
        return r.json() as Promise<RiskGeoJson>;
      }),
      fetch('/data/risk_index_metadata.json').then((r) => {
        if (!r.ok) throw new Error(`Failed to load risk-index metadata: ${r.status}`);
        return r.json() as Promise<RiskMetadata>;
      }),
    ])
      .then(([riskData, riskMetadata]) => {
        if (!riskData.features?.length) {
          throw new Error('Risk-index GeoJSON loaded, but it contains no municipality features.');
        }
        if (!riskMetadata.available_layers?.length) {
          throw new Error('Risk-index metadata loaded, but no available layers were detected.');
        }
        setData(riskData);
        setMetadata(riskMetadata);
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
            python -m src.site.export_risk_index_data
          </code>{' '}
          from the repository root to regenerate the web data files.
        </p>
      </div>
    );
  }

  if (!data || !metadata) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
          <p className="text-sm text-gray-500">Loading municipal risk-index data...</p>
        </div>
      </div>
    );
  }

  return <RiskIntegrationMap data={data} metadata={metadata} />;
}
