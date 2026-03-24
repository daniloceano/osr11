'use client';

import { useState } from 'react';
import Image from 'next/image';
import { tcEvents } from '@/content/tcEvents';

const SECTORS = ['All', 'North', 'Central-north', 'Central', 'Central-south', 'South'] as const;
type Sector = (typeof SECTORS)[number];

export default function EventFigureSelector() {
  const [sectorFilter, setSectorFilter] = useState<Sector>('All');
  const [selectedIdx, setSelectedIdx] = useState(0);

  const filtered = sectorFilter === 'All'
    ? tcEvents
    : tcEvents.filter((e) => e.sector === sectorFilter);

  // Reset selection when filter changes and current idx is out of range
  const safeIdx = selectedIdx < filtered.length ? selectedIdx : 0;
  const selected = filtered[safeIdx];

  return (
    <div className="space-y-5">
      {/* Sector filter chips */}
      <div className="flex flex-wrap gap-2">
        {SECTORS.map((s) => (
          <button
            key={s}
            onClick={() => { setSectorFilter(s); setSelectedIdx(0); }}
            className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
              sectorFilter === s
                ? 'bg-blue-600 text-white'
                : 'border border-gray-300 bg-white text-gray-600 hover:border-blue-400 hover:text-blue-600'
            }`}
          >
            {s === 'All' ? `All sectors (${tcEvents.length})` : `${s} (${tcEvents.filter(e => e.sector === s).length})`}
          </button>
        ))}
      </div>

      {/* Event selector dropdown */}
      <div className="flex flex-col gap-1.5">
        <label htmlFor="event-select" className="text-xs font-medium text-gray-500 uppercase tracking-wider">
          Select event
        </label>
        <select
          id="event-select"
          value={safeIdx}
          onChange={(e) => setSelectedIdx(Number(e.target.value))}
          className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-800 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          {filtered.map((ev, i) => (
            <option key={ev.file} value={i}>
              {ev.label}{ev.isConcurrent ? ' ⬤' : ''}
            </option>
          ))}
        </select>
        <p className="text-xs text-gray-400">
          ⬤ = concurrent exceedance (both Hₛ and SSH above q90 simultaneously)
        </p>
      </div>

      {/* Figure display */}
      {selected && (
        <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
          <div className="flex items-center justify-between px-5 py-3 border-b border-gray-100 bg-gray-50">
            <div>
              <span className="text-sm font-semibold text-gray-800">{selected.label}</span>
              <span className={`ml-2 rounded-full px-2 py-0.5 text-xs font-medium ${
                selected.isConcurrent
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-500'
              }`}>
                {selected.sector}
              </span>
              {selected.isConcurrent && (
                <span className="ml-1.5 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                  concurrent ⬤
                </span>
              )}
            </div>
            <span className="text-xs text-gray-400">
              {safeIdx + 1} / {filtered.length}
            </span>
          </div>

          <div className="p-4">
            <Image
              src={`/figures/tc_events/${selected.file}`}
              alt={selected.label}
              width={1000}
              height={600}
              className="w-full h-auto rounded-lg"
              unoptimized
            />
          </div>

          {/* Navigation arrows */}
          <div className="flex items-center justify-between border-t border-gray-100 px-5 py-3">
            <button
              disabled={safeIdx === 0}
              onClick={() => setSelectedIdx(safeIdx - 1)}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Previous
            </button>
            <button
              disabled={safeIdx === filtered.length - 1}
              onClick={() => setSelectedIdx(safeIdx + 1)}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              Next
              <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
