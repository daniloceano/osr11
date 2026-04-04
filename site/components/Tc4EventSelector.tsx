'use client';

import { useState, useMemo } from 'react';
import Image from 'next/image';
import { tc4Events, TC4_OPTIMAL_HS_PCT, TC4_OPTIMAL_SSH_PCT, Tc4EventEntry } from '@/content/tc4Events';

const PCT_LEVELS = [50, 55, 60, 65, 70, 75, 80, 85, 90];
const SECTORS = ['All', 'North', 'Central-north', 'Central', 'Central-south', 'South'];

type CaptureFilter = 'all' | 'hit' | 'miss';

const CAPTURE_LABELS: Record<CaptureFilter, string> = {
  all:  'All events',
  hit:  'Captured ✓',
  miss: 'Missed ✗',
};

export default function Tc4EventSelector() {
  const defaultPct = PCT_LEVELS.includes(TC4_OPTIMAL_HS_PCT) ? TC4_OPTIMAL_HS_PCT : 75;

  const [pct, setPct]                       = useState<number>(defaultPct);
  const [sector, setSector]                 = useState<string>('All');
  const [captureFilter, setCaptureFilter]   = useState<CaptureFilter>('all');
  const [idx, setIdx]                       = useState(0);

  const filtered = useMemo<Tc4EventEntry[]>(() => {
    return tc4Events.filter((e) => {
      const sectorOk  = sector === 'All' || e.sector === sector;
      const captured  = e.capturedAt[pct.toString()] ?? false;
      const captureOk =
        captureFilter === 'all' ||
        (captureFilter === 'hit'  && captured) ||
        (captureFilter === 'miss' && !captured);
      return sectorOk && captureOk;
    });
  }, [sector, captureFilter, pct]);

  const safeIdx = Math.min(idx, Math.max(0, filtered.length - 1));
  const current = filtered[safeIdx] ?? null;

  function go(delta: number) {
    setIdx((i) => Math.max(0, Math.min(filtered.length - 1, i + delta)));
  }
  function handleSector(s: string)          { setSector(s);        setIdx(0); }
  function handleCapture(c: CaptureFilter)  { setCaptureFilter(c); setIdx(0); }
  function handlePct(p: number)             { setPct(p);           setIdx(0); }

  // Construct figure path
  const figFile = current
    ? `fig_TC4_E${String(current.disasterId).padStart(3, '0')}_${current.slug}_${current.date}_hs${pct}_ssh${pct}.png`
    : null;

  const isOptimalPair = pct === TC4_OPTIMAL_HS_PCT && pct === TC4_OPTIMAL_SSH_PCT;
  const isCaptured    = current ? (current.capturedAt[pct.toString()] ?? false) : false;

  return (
    <div className="space-y-4">

      {/* Percentile selector */}
      <div>
        <p className="mb-1.5 text-xs font-medium text-gray-500 uppercase tracking-wide">
          Threshold percentile (Hₛ = SSH_total)
        </p>
        <div className="flex flex-wrap gap-2">
          {PCT_LEVELS.map((p) => (
            <button
              key={p}
              onClick={() => handlePct(p)}
              className={`rounded-full px-3 py-1 text-xs font-medium border transition-colors ${
                pct === p
                  ? 'bg-violet-600 text-white border-violet-600'
                  : 'bg-gray-50 text-gray-600 border-gray-300 hover:bg-gray-100'
              }`}
            >
              q{p}
              {p === TC4_OPTIMAL_HS_PCT && p === TC4_OPTIMAL_SSH_PCT && (
                <span className="ml-1 text-[10px] opacity-80">★</span>
              )}
            </button>
          ))}
        </div>
        {isOptimalPair && (
          <p className="mt-1.5 text-xs text-violet-600 font-medium">
            ★ This is the optimal threshold pair selected by the CSI grid scan.
          </p>
        )}
      </div>

      {/* Sector filter */}
      <div>
        <p className="mb-1.5 text-xs font-medium text-gray-500 uppercase tracking-wide">
          Coastal sector
        </p>
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
      </div>

      {/* Hit / miss filter */}
      <div>
        <p className="mb-1.5 text-xs font-medium text-gray-500 uppercase tracking-wide">
          Capture status at q{pct}
        </p>
        <div className="flex flex-wrap gap-2">
          {(Object.entries(CAPTURE_LABELS) as [CaptureFilter, string][]).map(([key, label]) => (
            <button
              key={key}
              onClick={() => handleCapture(key)}
              className={`rounded-full px-3 py-1 text-xs font-medium border transition-colors ${
                captureFilter === key
                  ? 'bg-gray-800 text-white border-gray-800'
                  : 'bg-gray-50 text-gray-600 border-gray-300 hover:bg-gray-100'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <p className="text-sm text-gray-400 italic py-4">
          No events match the selected filters.
        </p>
      ) : (
        <>
          {/* Navigation */}
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
                  <span className={`rounded-full px-2 py-0.5 text-xs border font-medium ${
                    isCaptured
                      ? 'bg-green-100 text-green-800 border-green-300'
                      : 'bg-red-100 text-red-800 border-red-300'
                  }`}>
                    {isCaptured ? '✓ Hit' : '✗ Miss'} at q{pct}
                  </span>
                )}
                {current?.capturedOptimal && (
                  <span className="rounded-full px-2 py-0.5 text-xs bg-violet-50 text-violet-700 border border-violet-200">
                    ★ Captured at optimal
                  </span>
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
          {current && figFile && (
            <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
              <div className="p-4">
                <Image
                  src={`/figures/tc4_events/${figFile}`}
                  alt={`Event time-series — ${current.label} at q${pct}`}
                  width={900}
                  height={600}
                  className="w-full h-auto rounded-lg"
                  unoptimized
                />
              </div>
              <div className="border-t border-gray-100 px-4 py-3 text-xs text-gray-500 italic leading-relaxed">
                Two-panel time-series for {current.label} ({current.sector} sector) at threshold pair
                Hₛ q{pct} / SSH_total q{pct}. Top panel: Hₛ daily maximum (WAVERYS). Bottom panel:
                SSH_total = zos (GLORYS12 00:00 UTC) + FES2022 tide (daily maximum). The blue band
                marks the causal window [D-2, D-1, D, D+1 00Z]. The dashed grey line is the local
                percentile threshold computed from the validated-period climatology at that grid point.
                Title in green = event captured (hit); red = missed.
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
