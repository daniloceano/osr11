'use client';

import { useState, useMemo } from 'react';
import Image from 'next/image';
import { tsEvents } from '@/content/tsEvents';

type ChangeFilter = 'all' | 'maintained' | 'lost' | 'neither';

const CHANGE_LABELS: Record<ChangeFilter, string> = {
  all:        'All events',
  maintained: 'Consistent detection (both)',
  lost:       'Detection lost with tide',
  neither:    'Not detected in either',
};

const CHANGE_COLORS: Record<string, string> = {
  maintained: 'bg-blue-100 text-blue-800 border-blue-300',
  lost:       'bg-red-100 text-red-800 border-red-300',
  neither:    'bg-gray-100 text-gray-600 border-gray-300',
  new:        'bg-green-100 text-green-800 border-green-300',
};

const SECTORS = ['All', 'North', 'Central-north', 'Central', 'Central-south', 'South'];

export default function TsEventSelector() {
  const [sector, setSector] = useState<string>('All');
  const [change, setChange] = useState<ChangeFilter>('all');
  const [idx, setIdx] = useState(0);

  const filtered = useMemo(() => {
    return tsEvents.filter((e) => {
      const sectorOk = sector === 'All' || e.sector === sector;
      const changeOk = change === 'all' || e.detectionChange === change;
      return sectorOk && changeOk;
    });
  }, [sector, change]);

  const safeIdx = Math.min(idx, Math.max(0, filtered.length - 1));
  const current = filtered[safeIdx];

  function go(delta: number) {
    setIdx((i) => Math.max(0, Math.min(filtered.length - 1, i + delta)));
  }

  // Reset index when filters change
  function handleSector(s: string) { setSector(s); setIdx(0); }
  function handleChange(c: ChangeFilter) { setChange(c); setIdx(0); }

  return (
    <div className="space-y-4">
      {/* Sector filter */}
      <div className="flex flex-wrap gap-2">
        {SECTORS.map((s) => (
          <button
            key={s}
            onClick={() => handleSector(s)}
            className={`rounded-full px-3 py-1 text-xs font-medium border transition-colors ${
              sector === s
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-gray-50 text-gray-600 border-gray-300 hover:bg-gray-100'
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Detection change filter */}
      <div className="flex flex-wrap gap-2">
        {(Object.entries(CHANGE_LABELS) as [ChangeFilter, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => handleChange(key)}
            className={`rounded-full px-3 py-1 text-xs font-medium border transition-colors ${
              change === key
                ? 'bg-gray-800 text-white border-gray-800'
                : 'bg-gray-50 text-gray-600 border-gray-300 hover:bg-gray-100'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <p className="text-sm text-gray-400 italic py-4">No events match the selected filters.</p>
      ) : (
        <>
          {/* Event label + navigation */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => go(-1)}
              disabled={safeIdx === 0}
              className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 disabled:opacity-30"
            >
              ◀ Prev
            </button>
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-medium text-gray-800">{current?.label}</span>
                {current && (
                  <span className={`rounded-full px-2 py-0.5 text-xs border font-medium ${CHANGE_COLORS[current.detectionChange] ?? 'bg-gray-100 text-gray-600 border-gray-300'}`}>
                    {{
                      maintained: 'Consistent ✓',
                      lost:       'Detection lost',
                      neither:    'Not detected',
                      new:        'New detection ✓',
                    }[current.detectionChange] ?? current.detectionChange}
                  </span>
                )}
                {current?.isConcurrentSsh && (
                  <span className="rounded-full px-2 py-0.5 text-xs bg-blue-50 text-blue-700 border border-blue-200">SSH-only ✓</span>
                )}
                {current?.isConcurrentTotal && (
                  <span className="rounded-full px-2 py-0.5 text-xs bg-purple-50 text-purple-700 border border-purple-200">SSH+tide ✓</span>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-0.5">
                Event {safeIdx + 1} of {filtered.length} · {current?.sector} sector
              </p>
            </div>
            <button
              onClick={() => go(1)}
              disabled={safeIdx >= filtered.length - 1}
              className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 disabled:opacity-30"
            >
              Next ▶
            </button>
          </div>

          {/* Figure */}
          {current && (
            <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
              <div className="p-4">
                <Image
                  src={`/figures/ts_events/${current.file}`}
                  alt={`Tidal sensitivity figure — ${current.label}`}
                  width={900}
                  height={700}
                  className="w-full h-auto rounded-lg"
                  unoptimized
                />
              </div>
              <div className="border-t border-gray-100 px-4 py-3 text-xs text-gray-500 italic leading-relaxed">
                Three-panel figure for {current.label} ({current.sector} sector).
                Top panel: Hₛ with q90 threshold and MagicA POT peaks. Middle panel: SSH (zos) with
                SSH-only q90. Bottom panel: SSH + FES2022 tide with SSH_total q90; the dashed green
                line shows the tidal component alone. The coloured title bar indicates the detection
                change: blue = consistent in both, red = lost with tide, grey = not detected in either.
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
