'use client';

import { useEffect, useMemo, useState } from 'react';

interface QiRow {
  episode_id: string;
  municipality: string;
  date_start: string;
  date_end: string;
  hs_peak: number;
  ssh_peak: number;
  n_days: number;
  E_i: number;
  I_i: number;
  C_season: number;
  C_multi: number;
  C_exposure: number;
  C_i: number;
  alpha_E: number;
  alpha_I: number;
  alpha_C: number;
  contrib_E: number;
  contrib_I: number;
  contrib_C: number;
  q_i_raw: number;
  q_i: number;
  penalty_component: number;
}

type SortKey = keyof QiRow;

export default function QiDecompositionTable() {
  const [data, setData] = useState<QiRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortKey, setSortKey] = useState<SortKey>('penalty_component');
  const [sortAsc, setSortAsc] = useState(false);
  const [filterMuni, setFilterMuni] = useState('');
  const [filterEi, setFilterEi] = useState<'' | '0' | '1'>('');
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    fetch('/data/tc5_qi_decomposition.json')
      .then((r) => r.json())
      .then((d: QiRow[]) => {
        setData(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const municipalities = useMemo(
    () => [...new Set(data.map((r) => r.municipality))].sort(),
    [data],
  );

  const filtered = useMemo(() => {
    let rows = data;
    if (filterMuni) rows = rows.filter((r) => r.municipality === filterMuni);
    if (filterEi !== '') rows = rows.filter((r) => String(r.E_i) === filterEi);
    return [...rows].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === 'number' && typeof bv === 'number') return sortAsc ? av - bv : bv - av;
      return sortAsc ? String(av).localeCompare(String(bv)) : String(bv).localeCompare(String(av));
    });
  }, [data, filterMuni, filterEi, sortKey, sortAsc]);

  const displayed = showAll ? filtered : filtered.slice(0, 50);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  };

  if (loading) {
    return <div className="text-sm text-gray-400 py-8 text-center">Loading q_i decomposition...</div>;
  }
  if (!data.length) {
    return <div className="text-sm text-gray-400 py-8 text-center">No q_i decomposition data available.</div>;
  }

  // Summary stats
  const meanPenalty = data.reduce((s, r) => s + r.penalty_component, 0) / data.length;
  const meanQi = data.reduce((s, r) => s + r.q_i, 0) / data.length;
  const e1Count = data.filter((r) => r.E_i === 1).length;

  const meanContribE = data.reduce((s, r) => s + r.contrib_E, 0) / data.length;
  const meanContribI = data.reduce((s, r) => s + r.contrib_I, 0) / data.length;
  const meanContribC = data.reduce((s, r) => s + r.contrib_C, 0) / data.length;

  const SortHeader = ({ k, label, className = '' }: { k: SortKey; label: string; className?: string }) => (
    <th
      className={`px-2 py-1.5 text-left font-medium cursor-pointer hover:bg-gray-100 select-none whitespace-nowrap ${className}`}
      onClick={() => handleSort(k)}
    >
      {label}
      {sortKey === k && <span className="ml-0.5">{sortAsc ? '▲' : '▼'}</span>}
    </th>
  );

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <div className="rounded-lg border border-gray-200 bg-white p-3 text-center">
          <div className="text-[10px] text-gray-500">Episodes</div>
          <div className="text-lg font-bold text-gray-800">{data.length.toLocaleString()}</div>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-3 text-center">
          <div className="text-[10px] text-gray-500">Mean q_i</div>
          <div className="text-lg font-bold text-gray-800">{meanQi.toFixed(3)}</div>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-3 text-center">
          <div className="text-[10px] text-gray-500">Mean penalty</div>
          <div className="text-lg font-bold text-red-700">{meanPenalty.toFixed(3)}</div>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-3 text-center">
          <div className="text-[10px] text-gray-500">E_i = 1</div>
          <div className="text-lg font-bold text-emerald-700">{e1Count} ({((e1Count / data.length) * 100).toFixed(1)}%)</div>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-3 text-center">
          <div className="text-[10px] text-gray-500">Mean contrib</div>
          <div className="text-xs font-mono text-gray-700">
            E: {meanContribE.toFixed(3)} · I: {meanContribI.toFixed(3)} · C: {meanContribC.toFixed(3)}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <select
          className="text-xs border border-gray-300 rounded px-2 py-1 bg-white"
          value={filterMuni}
          onChange={(e) => setFilterMuni(e.target.value)}
        >
          <option value="">All municipalities ({municipalities.length})</option>
          {municipalities.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
        <select
          className="text-xs border border-gray-300 rounded px-2 py-1 bg-white"
          value={filterEi}
          onChange={(e) => setFilterEi(e.target.value as '' | '0' | '1')}
        >
          <option value="">All E_i</option>
          <option value="1">E_i = 1 (corroborated)</option>
          <option value="0">E_i = 0 (uncorroborated)</option>
        </select>
        <span className="text-xs text-gray-400">
          Showing {displayed.length} of {filtered.length} episodes
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-[11px]">
          <thead className="bg-gray-50 text-gray-600 border-b border-gray-200">
            <tr>
              <SortHeader k="municipality" label="Municipality" />
              <SortHeader k="date_start" label="Start" />
              <SortHeader k="date_end" label="End" />
              <SortHeader k="hs_peak" label="Hₛ peak" />
              <SortHeader k="ssh_peak" label="SSH peak" />
              <SortHeader k="E_i" label="E_i" />
              <SortHeader k="I_i" label="I_i" />
              <SortHeader k="C_i" label="C_i" />
              <SortHeader k="contrib_E" label="α_E·E_i" className="text-emerald-700" />
              <SortHeader k="contrib_I" label="α_I·I_i" className="text-blue-700" />
              <SortHeader k="contrib_C" label="α_C·C_i" className="text-violet-700" />
              <SortHeader k="q_i" label="q_i" />
              <SortHeader k="penalty_component" label="1−q_i" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {displayed.map((row) => {
              const penaltyPct = row.penalty_component * 100;
              const bgRed = Math.round(penaltyPct * 2.2);
              return (
                <tr
                  key={row.episode_id}
                  className="hover:bg-gray-50"
                  title={row.episode_id}
                >
                  <td className="px-2 py-1 font-medium text-gray-800 whitespace-nowrap">{row.municipality}</td>
                  <td className="px-2 py-1 text-gray-600 whitespace-nowrap">{row.date_start}</td>
                  <td className="px-2 py-1 text-gray-600 whitespace-nowrap">{row.date_end}</td>
                  <td className="px-2 py-1 font-mono text-gray-700">{row.hs_peak.toFixed(2)}</td>
                  <td className="px-2 py-1 font-mono text-gray-700">{row.ssh_peak.toFixed(3)}</td>
                  <td className="px-2 py-1 text-center">
                    <span className={`inline-block w-4 h-4 rounded-full text-[9px] leading-4 text-center font-bold ${row.E_i === 1 ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-400'}`}>
                      {row.E_i}
                    </span>
                  </td>
                  <td className="px-2 py-1 font-mono text-gray-700">{row.I_i.toFixed(3)}</td>
                  <td className="px-2 py-1 font-mono text-gray-700">{row.C_i.toFixed(3)}</td>
                  <td className="px-2 py-1 font-mono text-emerald-700">{row.contrib_E.toFixed(3)}</td>
                  <td className="px-2 py-1 font-mono text-blue-700">{row.contrib_I.toFixed(3)}</td>
                  <td className="px-2 py-1 font-mono text-violet-700">{row.contrib_C.toFixed(3)}</td>
                  <td className="px-2 py-1 font-mono font-medium text-gray-900">{row.q_i.toFixed(3)}</td>
                  <td
                    className="px-2 py-1 font-mono font-bold"
                    style={{ backgroundColor: `rgba(220, 38, 38, ${penaltyPct / 100 * 0.15})` }}
                  >
                    {row.penalty_component.toFixed(3)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Show more / less */}
      {filtered.length > 50 && (
        <div className="text-center">
          <button
            className="text-xs text-blue-600 hover:text-blue-800 underline"
            onClick={() => setShowAll(!showAll)}
          >
            {showAll ? `Show top 50 only` : `Show all ${filtered.length} episodes`}
          </button>
        </div>
      )}

      <p className="text-[10px] text-gray-400 text-center">
        Sorted by {String(sortKey)} ({sortAsc ? 'ascending' : 'descending'}).
        Click column headers to re-sort. Hover rows for episode_id.
        Full data: <code>tab_TC5_qi_decomposition.csv</code> ({data.length} episodes × 22 columns).
      </p>
    </div>
  );
}
