'use client';

import { useState } from 'react';
import Image from 'next/image';
import type { FigureItem } from '@/lib/types';
import { figureGroups } from '@/content/figures';

export default function FigureGallery({ figures }: { figures: FigureItem[] }) {
  const [activeGroup, setActiveGroup] = useState<string>('All');
  const [lightbox, setLightbox] = useState<FigureItem | null>(null);

  const groups = ['All', ...figureGroups.filter((g) => figures.some((f) => f.group === g))];
  const filtered = activeGroup === 'All' ? figures : figures.filter((f) => f.group === activeGroup);

  return (
    <div>
      {/* Filter tabs */}
      <div className="mb-8 flex flex-wrap gap-2">
        {groups.map((g) => (
          <button
            key={g}
            onClick={() => setActiveGroup(g)}
            className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
              activeGroup === g
                ? 'border-sky-500/50 bg-blue-600/15 text-sky-300'
                : 'border-gray-300 bg-gray-50 text-gray-500 hover:border-slate-600 hover:text-gray-700'
            }`}
          >
            {g}
            <span className="ml-1.5 text-gray-400">
              {g === 'All' ? figures.length : figures.filter((f) => f.group === g).length}
            </span>
          </button>
        ))}
      </div>

      {/* Grid */}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((fig) => (
          <button
            key={fig.filename}
            onClick={() => setLightbox(fig)}
            className="group text-left rounded-xl border border-gray-200 bg-gray-50 overflow-hidden hover:border-sky-500/30 transition-all"
          >
            {/* Thumbnail */}
            <div className="relative aspect-[4/3] w-full bg-white overflow-hidden">
              <Image
                src={`/figures/${fig.filename}`}
                alt={fig.title}
                fill
                className="object-contain p-2 group-hover:scale-105 transition-transform duration-300"
                sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
              />
              {/* Hover overlay */}
              <div className="absolute inset-0 flex items-center justify-center bg-blue-600/0 group-hover:bg-blue-600/5 transition-colors">
                <svg className="h-8 w-8 text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity drop-shadow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                </svg>
              </div>
            </div>

            {/* Caption */}
            <div className="p-4">
              <div className="mb-1 flex items-center gap-2">
                <span className="rounded border border-gray-300 bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500">
                  {fig.part}
                </span>
                <span className="text-xs text-gray-400">{fig.group}</span>
              </div>
              <p className="text-xs font-semibold text-gray-700 group-hover:text-sky-300 transition-colors line-clamp-2">
                {fig.title}
              </p>
            </div>
          </button>
        ))}
      </div>

      {/* Lightbox */}
      {lightbox && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-white/95 backdrop-blur-sm p-4"
          onClick={() => setLightbox(null)}
        >
          <div
            className="relative max-w-5xl w-full max-h-[90vh] flex flex-col rounded-2xl border border-gray-300 bg-gray-50 overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Lightbox header */}
            <div className="flex items-start justify-between gap-4 border-b border-gray-200 p-5">
              <div>
                <div className="mb-1 flex items-center gap-2">
                  <span className="rounded border border-gray-300 bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500">
                    {lightbox.part}
                  </span>
                  <span className="text-xs text-gray-400">{lightbox.group}</span>
                </div>
                <h3 className="text-sm font-semibold text-gray-800">{lightbox.title}</h3>
              </div>
              <button
                onClick={() => setLightbox(null)}
                className="flex-shrink-0 rounded-lg border border-gray-300 bg-gray-100 p-1.5 text-gray-600 hover:text-gray-800 transition-colors"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Image */}
            <div className="relative flex-1 min-h-0 bg-white">
              <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
                <Image
                  src={`/figures/${lightbox.filename}`}
                  alt={lightbox.title}
                  fill
                  className="object-contain p-4"
                  sizes="100vw"
                  quality={95}
                />
              </div>
            </div>

            {/* Caption */}
            <div className="border-t border-gray-200 p-5 max-h-40 overflow-y-auto">
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1.5">
                Figure Caption
              </p>
              <p className="text-xs leading-relaxed text-gray-600">{lightbox.caption}</p>
              <p className="mt-2 text-xs text-gray-400">{lightbox.filename}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
