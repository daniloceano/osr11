'use client';

import { useEffect, useState } from 'react';

interface ScoreRow {
  hs_percentile: number;
  ssh_percentile: number;
  H: number;
  M: number;
  U: number;
  P: number;
  Y: number;
  R_pos: number;
  B_raw: number;
  B: number;
  F_soft: number;
  term_recall_raw: number;
  term_burden_raw: number;
  term_fsoft_raw: number;
  w1: number;
  w2: number;
  w3: number;
  term_recall_weighted: number;
  term_burden_weighted: number;
  term_fsoft_weighted: number;
  Score: number;
}

type MetricKey = 'term_recall_weighted' | 'term_burden_weighted' | 'term_fsoft_weighted' | 'Score';

const METRICS: { key: MetricKey; label: string; description: string; colorScale: 'green' | 'red' | 'diverging' }[] = [
  {
    key: 'term_recall_weighted',
    label: 'w₁ · R_pos',
    description: 'Weighted recall contribution (higher = better)',
    colorScale: 'green',
  },
  {
    key: 'term_burden_weighted',
    label: '−w₂ · B',
    description: 'Weighted burden penalty (closer to 0 = better)',
    colorScale: 'red',
  },
  {
    key: 'term_fsoft_weighted',
    label: '−w₃ · F_soft/P',
    description: 'Weighted soft penalty (closer to 0 = better)',
    colorScale: 'red',
  },
  {
    key: 'Score',
    label: 'Score',
    description: 'Composite score = w₁·R_pos − w₂·B − w₃·F_soft/P (higher = better)',
    colorScale: 'diverging',
  },
];

function interpolateColor(value: number, min: number, max: number, scale: 'green' | 'red' | 'diverging'): string {
  if (max === min) return 'rgb(243, 244, 246)';
  const t = (value - min) / (max - min); // 0..1

  if (scale === 'green') {
    // Low = light gray, High = green
    const r = Math.round(243 - t * 183);
    const g = Math.round(244 - t * 64);
    const b = Math.round(246 - t * 186);
    return `rgb(${r}, ${g}, ${b})`;
  }
  if (scale === 'red') {
    // More negative = darker red; closer to 0 = lighter
    const r = Math.round(254 - (1 - t) * 174);
    const g = Math.round(242 - (1 - t) * 190);
    const b = Math.round(242 - (1 - t) * 192);
    return `rgb(${r}, ${g}, ${b})`;
  }
  // diverging: low = red, mid = white, high = green
  if (t < 0.5) {
    const s = t / 0.5;
    const r = Math.round(220 - s * 20);
    const g = Math.round(50 + s * 200);
    const b = Math.round(50 + s * 200);
    return `rgb(${r}, ${g}, ${b})`;
  }
  const s = (t - 0.5) / 0.5;
  const r = Math.round(200 - s * 140);
  const g = Math.round(250 - s * 70);
  const b = Math.round(250 - s * 190);
  return `rgb(${r}, ${g}, ${b})`;
}

function Heatmap({ data, metric }: { data: ScoreRow[]; metric: typeof METRICS[number] }) {
  const percentiles = [50, 55, 60, 65, 70, 75, 80, 85, 90];
  const values = data.map((r) => r[metric.key]);
  const vmin = Math.min(...values);
  const vmax = Math.max(...values);

  const grid: Map<string, ScoreRow> = new Map();
  for (const row of data) {
    grid.set(`${row.hs_percentile}-${row.ssh_percentile}`, row);
  }

  return (
    <div>
      <h4 className="text-sm font-semibold text-gray-800 mb-1">{metric.label}</h4>
      <p className="text-xs text-gray-500 mb-2">{metric.description}</p>
      <div className="overflow-x-auto">
        <table className="text-[10px] border-collapse">
          <thead>
            <tr>
              <th className="px-1 py-0.5 text-gray-500 font-normal">Hₛ \ SSH</th>
              {percentiles.map((p) => (
                <th key={p} className="px-1.5 py-0.5 text-gray-500 font-medium text-center">q{p}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {percentiles.map((hs) => (
              <tr key={hs}>
                <td className="px-1 py-0.5 text-gray-500 font-medium">q{hs}</td>
                {percentiles.map((ssh) => {
                  const row = grid.get(`${hs}-${ssh}`);
                  if (!row) return <td key={ssh} className="px-1.5 py-1" />;
                  const val = row[metric.key];
                  const bg = interpolateColor(val, vmin, vmax, metric.colorScale);
                  const isOptimal = hs === 90 && ssh === 90;
                  return (
                    <td
                      key={ssh}
                      className={`px-1.5 py-1 text-center font-mono ${isOptimal ? 'ring-2 ring-black ring-inset' : ''}`}
                      style={{ backgroundColor: bg }}
                      title={`q${hs}/q${ssh}: ${val.toFixed(4)}`}
                    >
                      {val >= 0 ? val.toFixed(3) : val.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-1 flex justify-between text-[9px] text-gray-400">
        <span>{vmin.toFixed(3)}</span>
        <span>{vmax.toFixed(3)}</span>
      </div>
    </div>
  );
}

export default function ScoreDecompositionHeatmaps() {
  const [data, setData] = useState<ScoreRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/data/tc5_score_decomposition.json')
      .then((r) => r.json())
      .then((d: ScoreRow[]) => {
        setData(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-sm text-gray-400 py-8 text-center">Loading score decomposition...</div>;
  }
  if (!data.length) {
    return <div className="text-sm text-gray-400 py-8 text-center">No score decomposition data available.</div>;
  }

  // Optimal pair summary
  const opt = data.find((r) => r.hs_percentile === 90 && r.ssh_percentile === 90);

  return (
    <div className="space-y-6">
      {opt && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <h4 className="text-xs font-semibold text-blue-900 mb-2">Optimal pair (q90/q90) — Term breakdown</h4>
          <div className="grid grid-cols-3 gap-3 text-xs">
            <div className="rounded-lg border border-emerald-200 bg-white p-3">
              <div className="text-[10px] text-gray-500">w₁ · R_pos</div>
              <div className="text-lg font-bold text-emerald-700">+{opt.term_recall_weighted.toFixed(4)}</div>
              <div className="text-[10px] text-gray-400">recall = {opt.R_pos.toFixed(4)} × w₁={opt.w1}</div>
            </div>
            <div className="rounded-lg border border-amber-200 bg-white p-3">
              <div className="text-[10px] text-gray-500">−w₂ · B</div>
              <div className="text-lg font-bold text-amber-700">{opt.term_burden_weighted.toFixed(4)}</div>
              <div className="text-[10px] text-gray-400">B = {opt.B.toFixed(4)} (raw: {opt.B_raw.toFixed(4)}) × w₂={opt.w2}</div>
            </div>
            <div className="rounded-lg border border-red-200 bg-white p-3">
              <div className="text-[10px] text-gray-500">−w₃ · F_soft/P</div>
              <div className="text-lg font-bold text-red-700">{opt.term_fsoft_weighted.toFixed(4)}</div>
              <div className="text-[10px] text-gray-400">F_soft/P = {opt.term_fsoft_raw.toFixed(4)} × w₃={opt.w3}</div>
            </div>
          </div>
          <div className="mt-3 text-xs text-blue-800">
            <strong>Score = {opt.Score.toFixed(4)}</strong> — the F_soft/P term dominates
            ({((Math.abs(opt.term_fsoft_weighted) / (Math.abs(opt.term_recall_weighted) + Math.abs(opt.term_burden_weighted) + Math.abs(opt.term_fsoft_weighted))) * 100).toFixed(0)}%
            of total absolute magnitude)
          </div>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {METRICS.map((m) => (
          <div key={m.key} className="rounded-xl border border-gray-200 bg-white p-4">
            <Heatmap data={data} metric={m} />
          </div>
        ))}
      </div>

      <p className="text-[10px] text-gray-400 text-center">
        Black border = optimal pair (q90/q90). Hover cells for exact values.
        Full data: <code>tab_TC5_score_decomposition.csv</code> (81 rows × 21 columns).
      </p>
    </div>
  );
}
