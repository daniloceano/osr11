'use client';

import type {
  CoastalBasemap,
  CoastalHazardGeoJson,
  CoastalHazardMetadata,
} from '@/components/CoastalHazardMap';
import type { HazardData } from '@/components/HazardCharacterizationMap';

export interface CoastalBundle {
  segments: CoastalHazardGeoJson;
  metadata: CoastalHazardMetadata;
  basemap: CoastalBasemap;
  metrics: HazardData;
}

async function loadJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Failed to load ${url}: ${response.status}`);
  return (await response.json()) as T;
}

let bundle: Promise<CoastalBundle> | null = null;

/**
 * Load the coastal layers once per browser session.
 *
 * The Hazard Index panel and the per-grid-point explorer draw the same
 * coastline segments, so they share a single fetch of the geometry, the
 * metadata, the basemap, and the Step 3 metric catalog.
 */
export function loadCoastalBundle(): Promise<CoastalBundle> {
  if (!bundle) {
    bundle = Promise.all([
      loadJson<CoastalHazardGeoJson>('/data/coastal_hazard_segments.geojson'),
      loadJson<CoastalHazardMetadata>('/data/coastal_hazard_metadata.json'),
      loadJson<CoastalBasemap>('/data/coastal_basemap.geojson'),
      loadJson<HazardData>('/data/hazard_characterization_grid_metrics.json'),
    ])
      .then(([segments, metadata, basemap, metrics]) => ({
        segments,
        metadata,
        basemap,
        metrics,
      }))
      .catch((error: unknown) => {
        bundle = null;
        throw error;
      });
  }
  return bundle;
}
