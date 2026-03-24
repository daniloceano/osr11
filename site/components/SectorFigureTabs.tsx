'use client';

import { useState } from 'react';
import Image from 'next/image';

type Tab = { label: string; file: string };

interface SectorFigureTabsProps {
  figureKey: string;       // e.g. 'S1', 'S3', 'S4'
  overallFile: string;     // filename for the "All sectors" view
  sectorTabs: Tab[];       // per-sector tabs
  caption: string;
}

export default function SectorFigureTabs({
  figureKey,
  overallFile,
  sectorTabs,
  caption,
}: SectorFigureTabsProps) {
  const allTabs: Tab[] = [
    { label: 'All sectors', file: overallFile },
    ...sectorTabs,
  ];
  const [activeTab, setActiveTab] = useState(0);

  return (
    <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
      {/* Tab bar */}
      <div className="flex overflow-x-auto border-b border-gray-200 bg-gray-50 px-5 pt-3 gap-1">
        {allTabs.map((tab, i) => (
          <button
            key={tab.label}
            onClick={() => setActiveTab(i)}
            className={`flex-shrink-0 rounded-t-md px-3 py-2 text-xs font-medium transition-colors ${
              activeTab === i
                ? 'border border-b-white border-gray-200 bg-white text-blue-600 -mb-px'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Figure */}
      <div className="p-5">
        <Image
          src={`/figures/tc_summary/${allTabs[activeTab].file}`}
          alt={`Figure TC-${figureKey} — ${allTabs[activeTab].label}`}
          width={1000}
          height={600}
          className="w-full h-auto rounded-lg"
          unoptimized
        />
      </div>

      {/* Caption */}
      <div className="border-t border-gray-100 px-5 py-4">
        <p className="text-xs text-gray-500 leading-relaxed italic">{caption}</p>
      </div>
    </div>
  );
}
