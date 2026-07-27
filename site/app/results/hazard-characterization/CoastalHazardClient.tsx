'use client';

import { useEffect, useState } from 'react';
import CoastalHazardMap from '@/components/CoastalHazardMap';
import HazardCharacterizationMap from '@/components/HazardCharacterizationMap';
import { loadCoastalBundle, type CoastalBundle } from '@/lib/coastalData';

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
  if (error) return <LoadFailure message={error} />;
  if (!bundle) return <Loading label="Loading coastal Hazard Index layers…" />;
  return (
    <CoastalHazardMap
      data={bundle.segments}
      metadata={bundle.metadata}
      basemap={bundle.basemap}
    />
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
