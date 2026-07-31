import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';
import FigureGallery from '@/components/FigureGallery';
import ScoreDecompositionHeatmaps from '@/components/ScoreDecompositionHeatmaps';
import QiDecompositionTable from '@/components/QiDecompositionTable';
import { tc5Figures, tc5FigureGroups } from '@/content/figures';

export const metadata = {
  title: 'PU Composite Calibration (Step 2e) — OSR11',
  description:
    'Final threshold calibration via PU composite scoring against the combined positive-event set (expanded 56 + legacy 91 = 147 events, 27 municipalities, 1998–2020). Recalibrated 2026-07-30 on the production detector over a 121-pair grid; selected pair q70/q99.',
};

export default function PuCalibrationPage() {
  return (
    <>
      <Navigation />
      <main className="pt-16">

        {/* ── Page header ──────────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-16">
          <div className="mx-auto max-w-5xl px-6">
            <div className="mb-4 flex items-center gap-2 text-xs text-gray-500">
              <Link href="/" className="hover:text-gray-700 transition-colors">Overview</Link>
              <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span>Results</span>
              <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <Link href="/results/threshold-calibration" className="hover:text-gray-700 transition-colors">Threshold Calibration</Link>
              <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span className="text-gray-600">PU Composite Calibration</span>
            </div>

            <div className="flex flex-wrap items-start gap-2 mb-4">
              <StatusBadge status="done" />
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Step 2e · Final calibration</span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Combined: expanded (56) + legacy (91) = 147 events · 27 municipalities · 1998–2020</span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">PU composite score · 81 pairs · B_target = 12 × 27 = 324 ep/yr</span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              PU Composite Calibration
              <br />
              <span className="text-blue-600">Final Threshold Calibration Under Under-Reporting</span>
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-gray-600">
              Step 2e performs an <strong>independent</strong> threshold sweep using a positive-unlabeled
              (PU) composite score designed to handle the systematic under-reporting in the Civil Defense
              database. Instead of treating all unmatched detections as false alarms, this framework
              assigns each unmatched episode a confidence weight qᵢ based on external evidence,
              physical intensity, and contextual coherence — then optimises a weighted composite that
              balances recall, operational burden, and soft penalty.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              {[
                { label: 'Positive-event set',  value: 'Combined: expanded (56 events, 14 cities) + legacy (91 events, 22 cities) = 147 unique (municipality, date) pairs, 27 municipalities' },
                { label: 'Threshold grid',     value: 'q50–q90 × q50–q90, every 5 pct points — 81 pairs (same sweep as Step 2d)' },
                { label: 'Match window',       value: '[D-2, D-1, D, D+1 00Z] — inherited from Step 2d' },
                { label: 'Score formula',      value: 'Score = w₁·R_pos − w₂·B − w₃·F_soft/P  (w₁=0.60, w₂=0.20, w₃=0.20)' },
                { label: 'B_target',           value: '12 ep/yr/muni × 27 municipalities (union) = 324 ep/yr effective domain budget' },
                { label: 'Confidence weights', value: 'qᵢ = α_E·Eᵢ + α_I·Iᵢ + α_C·Cᵢ  (α_E=0.60, α_I=0.30, α_C=0.10)' },
              ].map((m) => (
                <div key={m.label} className="rounded-lg border border-gray-300/60 bg-gray-50 px-3 py-2">
                  <div className="text-xs text-gray-500">{m.label}</div>
                  <div className="text-xs font-medium text-gray-800">{m.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── What this analysis is about ───────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-4 text-xl font-bold text-gray-900">Why Step 2d is diagnostic and Step 2e is the final calibration</h2>
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-4 text-sm text-gray-700 leading-relaxed">
                <p>
                  Step 2d (CSI Grid Scan) revealed that FAR is near 1 at all threshold pairs — even the
                  most restrictive pair it scanned (q90/q90) produces 1 298 unmatched compound
                  episodes against 91 reported disasters. The CSI score (0.0151) is low. The naive interpretation is
                  that the detector has almost no skill.
                </p>
                <p>
                  But FAR assumes the Civil Defense database is a complete record of coastal flooding
                  events. It is not. Reporting is voluntary, spatially uneven, and historically incomplete,
                  particularly before 2005 and in less-populated sectors. Many unmatched compound
                  detections may correspond to real coastal events that were never reported.
                </p>
                <p>
                  <strong>Step 2e addresses this directly</strong> by treating unmatched detected
                  episodes not as false alarms, but as <em>unlabeled</em> examples — plausible
                  but unconfirmed events. Each episode receives a confidence weight qᵢ that quantifies
                  how likely it is to correspond to a real, unreported event. The composite score
                  then penalises only episodes with low plausibility, not all unmatched detections equally.
                </p>
              </div>
              <div className="space-y-3">
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                  <h3 className="text-xs font-semibold text-amber-900 mb-2">Step 2d (diagnostic) — CSI framework</h3>
                  <ul className="space-y-1 text-xs text-amber-800">
                    <li>— Uses legacy Leal et al. (2024) database: 91 events</li>
                    <li>— All unmatched episodes = false alarms</li>
                    <li>— CSI = H / (H + M + F) — penalises every unmatched detection equally</li>
                    <li>— Result: q90/q90, CSI=0.0151, FAR=0.984</li>
                    <li>— Interpretation: low skill — OR low reporting coverage</li>
                  </ul>
                </div>
                <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
                  <h3 className="text-xs font-semibold text-emerald-900 mb-2">Step 2e (final calibration) — PU composite</h3>
                  <ul className="space-y-1 text-xs text-emerald-800">
                    <li>— Uses combined positive-event set: 147 events (expanded 56 + legacy 91), 27 municipalities</li>
                    <li>— 0 exact (municipality, date) overlaps between databases; 2 near-matches at Florianópolis (±3 d)</li>
                    <li>— Unmatched episodes = unlabeled, not false alarms</li>
                    <li>— Score = w₁·R_pos − w₂·B − w₃·F_soft/P, with w = (0.30, 0.60, 0.10)</li>
                    <li>— B is a two-sided deviation from an expected rate of 2.0 detections/municipality/year</li>
                    <li>— Grid extended to 11 levels (q50…q90, q95, q99) = 121 pairs</li>
                    <li>— Result: <strong>q70/q99</strong>, recalibrated 2026-07-30 on the production detector</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Composite score components ────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-6 text-xl font-bold text-gray-900">Score Components</h2>
            <div className="grid gap-4 md:grid-cols-3 mb-6">
              {[
                {
                  name: 'R_pos',
                  full: 'Positive Recall',
                  formula: 'H / P',
                  range: '0–1 (higher = better)',
                  color: 'border-blue-200 bg-blue-50',
                  text: 'Fraction of the combined positive-event set (147 events: expanded 56 + legacy 91) captured at each threshold pair. P = evaluable events with valid grid associations (~143; 4 expanded cities lack grid points). Analogous to POD. Weighted with w₁=0.60 as the primary objective.',
                },
                {
                  name: 'B',
                  full: 'Normalised Annual Burden',
                  formula: 'min(1, (H+U) / (Y · B_target))',
                  range: '0–1 (lower = better)',
                  color: 'border-amber-100 bg-amber-50',
                  text: 'Ratio of total annual detections (hits + unmatched) to the operational budget (B_target_effective = 12 × 27 = 324 ep/yr, using the full union of 27 municipalities). Penalises thresholds that fire too frequently for operational use. B=1 when the detector saturates the budget; B=0 is unachievable.',
                },
                {
                  name: 'F_soft',
                  full: 'Soft Unmatched Penalty',
                  formula: 'Σᵢ (1 − qᵢ)',
                  range: '≥ 0 (lower = better)',
                  color: 'border-red-100 bg-red-50',
                  text: 'Sum of (1 − qᵢ) over all unmatched episodes for a given threshold pair. Episodes with qᵢ ≈ 1 (high external evidence, intense, contextually coherent) contribute almost nothing to F_soft. Episodes with qᵢ ≈ 0 (low evidence, weak, out-of-season) are penalised fully. Normalised by P before entering the score formula.',
                },
              ].map((m) => (
                <div key={m.name} className={`rounded-xl border p-5 ${m.color}`}>
                  <div className="text-2xl font-black text-gray-800 mb-0.5">{m.name}</div>
                  <div className="text-xs text-gray-600 mb-2">{m.full}</div>
                  <code className="text-xs bg-white/70 px-2 py-1 rounded border border-gray-200 block mb-3">
                    {m.formula}
                  </code>
                  <div className="text-xs text-gray-500 mb-2">{m.range}</div>
                  <p className="text-xs text-gray-600 leading-relaxed">{m.text}</p>
                </div>
              ))}
            </div>

            <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
              <h3 className="text-sm font-semibold text-blue-900 mb-2">Composite score formula</h3>
              <code className="text-sm text-blue-800 font-mono block mb-3">
                Score(θ) = w₁ · R_pos(θ) − w₂ · B(θ) − w₃ · F_soft(θ) / P
              </code>
              <p className="text-xs text-blue-700 leading-relaxed">
                Higher is better. The score is typically negative when the burden and soft penalty terms
                dominate recall. With B_target_effective = 324 ep/yr (12 × 27 municipalities), the burden
                budget is larger than the previous 168 ep/yr, which reduces B and makes the score less
                negative. The optimisation selects the threshold pair with the <em>least negative</em> score.
                Normalising F_soft by P places it on the same scale as R_pos for interpretable weighting.
              </p>
            </div>
          </div>
        </div>

        {/* ── Confidence weight construction ────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-4 text-xl font-bold text-gray-900">Episode Confidence Weights (qᵢ)</h2>
            <p className="mb-6 text-sm text-gray-600 max-w-3xl">
              For each unmatched compound episode, a confidence weight qᵢ ∈ [0, 1] is computed from
              three independent indicators. The higher the weight, the more plausible it is that the
              episode corresponds to a real but unreported coastal event.
            </p>

            <div className="grid gap-4 md:grid-cols-3 mb-6">
              {[
                {
                  symbol: 'Eᵢ',
                  label: 'External evidence',
                  weight: 'α_E = 0.60',
                  color: 'border-emerald-200 bg-emerald-50',
                  desc: 'Binary indicator: does the legacy database (Leal et al. 2024) contain any reported event within a 5-day window of this episode at the same municipality? If yes, Eᵢ=1 (corroborated by an independent source). Weighted most heavily because independent documentary evidence is the strongest signal.',
                },
                {
                  symbol: 'Iᵢ',
                  label: 'Physical intensity',
                  weight: 'α_I = 0.30',
                  color: 'border-blue-200 bg-blue-50',
                  desc: 'Continuous indicator: the mean of the normalised Hₛ and SSH_total exceedances within the episode relative to the detection threshold. Episodes where both hazard variables far exceed their thresholds receive high Iᵢ. Captures genuine extreme conditions that are more likely to have caused real impacts.',
                },
                {
                  symbol: 'Cᵢ',
                  label: 'Context coherence',
                  weight: 'α_C = 0.10',
                  color: 'border-violet-200 bg-violet-50',
                  desc: 'Composite indicator combining: (1) active season flag (Apr–Oct = 1); (2) spatial coherence (concurrent exceedance at neighbouring municipalities); (3) exposure flag (northern sector municipalities with higher exposure and partial model coverage). Rewards contextually plausible episodes.',
                },
              ].map((c) => (
                <div key={c.symbol} className={`rounded-xl border p-5 ${c.color}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl font-black text-gray-800">{c.symbol}</span>
                    <span className="rounded-full border border-gray-300 bg-white/70 px-2 py-0.5 text-xs font-mono text-gray-700">{c.weight}</span>
                  </div>
                  <div className="text-xs font-semibold text-gray-700 mb-2">{c.label}</div>
                  <p className="text-xs text-gray-600 leading-relaxed">{c.desc}</p>
                </div>
              ))}
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-5">
              <h3 className="text-sm font-semibold text-gray-900 mb-2">qᵢ formula</h3>
              <code className="text-xs font-mono text-gray-700 block mb-3">
                qᵢ = clip( α_E · Eᵢ + α_I · Iᵢ + α_C · Cᵢ ,  0,  1 )
              </code>
              <p className="text-xs text-gray-600 leading-relaxed">
                The three components are linearly weighted and clipped to [0, 1]. An episode corroborated
                by the legacy database (Eᵢ=1) already reaches qᵢ ≥ 0.60, regardless of intensity or
                context. Episodes with no external corroboration, weak forcing, and out-of-season timing
                receive qᵢ close to 0 and contribute their full (1 − qᵢ) ≈ 1 to the soft penalty.
              </p>
            </div>
          </div>
        </div>

        {/* ── Methodology pipeline ─────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-6 text-xl font-bold text-gray-900">Calibration Pipeline</h2>
            <div className="space-y-4">
              {[
                {
                  step: '1',
                  title: 'Load combined positive-event set (both databases)',
                  text: 'Step 2e uses BOTH event databases as its positive set P. The expanded documentary database (56 events, 14 municipalities, news/theses/reports, explicit marine forcing) and the legacy Leal et al. (2024) Civil Defense database (91 events from 72 disasters, 22 municipalities) are loaded and merged via load_combined_events(). Deduplication on exact (municipality, date) yields 0 overlaps → 147 unique pairs, 27 municipalities. Two near-matches (±3 days at Florianópolis) are retained as separate events and flagged in tab_TC5_event_provenance.csv.',
                  tag: 'Input',
                  tagColor: 'text-gray-700 bg-gray-100 border-gray-200',
                },
                {
                  step: '2',
                  title: 'Clip to validated temporal domain',
                  text: 'The dataset is clipped to [min(event_dates) + min(offsets), max(event_dates) + max(offsets)] — roughly 1998–2020. This prevents the false alarm scan from sampling years outside the documentary record, avoiding artificially inflated unmatched episode counts from unvalidated periods.',
                  tag: 'Preprocessing',
                  tagColor: 'text-amber-700 bg-amber-50 border-amber-200',
                },
                {
                  step: '3',
                  title: 'Layer 1 — event hit/miss scan',
                  text: 'For each of the 81 threshold pairs and each of the combined 147 events (143 evaluable with valid grid associations): check whether Hₛ and SSH_total simultaneously exceed their local percentile thresholds at any timestep within the causal window [D-2, D+1 00Z]. Record H (hit) or M (miss). Events at Biguaçu, Imbituba, Joinville, Laguna (4 expanded-only cities without grid points) are structural misses excluded from the hit/miss scan.',
                  tag: 'Layer 1',
                  tagColor: 'text-orange-700 bg-orange-50 border-orange-200',
                },
                {
                  step: '4',
                  title: 'Layer 2 — unmatched episode collection with full metadata',
                  text: 'Unlike Step 2d which only counts false alarms, Layer 2 collects full metadata for every unmatched compound episode: peak Hₛ, peak SSH_total, episode dates, municipality, and grid point. This metadata is required to compute the qᵢ confidence weights in the next step. Episodes matched to any event window are discarded here.',
                  tag: 'Layer 2',
                  tagColor: 'text-red-700 bg-red-50 border-red-200',
                },
                {
                  step: '5',
                  title: 'Build episode audit table — compute Eᵢ, Iᵢ, Cᵢ, qᵢ',
                  text: 'For each unmatched episode (across all threshold pairs), compute the three qᵢ components: Eᵢ (legacy database corroboration within 5 days), Iᵢ (normalised exceedance intensity), Cᵢ (season + spatial coherence + exposure). Combine into qᵢ = clip(α_E·Eᵢ + α_I·Iᵢ + α_C·Cᵢ, 0, 1). Save as tab_TC5_episode_audit.csv.',
                  tag: 'Audit',
                  tagColor: 'text-violet-700 bg-violet-50 border-violet-200',
                },
                {
                  step: '6',
                  title: 'Compute PU composite scores for all 81 pairs',
                  text: 'For each threshold pair: aggregate R_pos, B, and F_soft = Σ(1 − qᵢ) from the episode audit table; compute Score = w₁·R_pos − w₂·B − w₃·F_soft/P. Scores are saved in tab_TC5_pu_metrics_full.csv.',
                  tag: 'Scoring',
                  tagColor: 'text-blue-700 bg-blue-50 border-blue-200',
                },
                {
                  step: '7',
                  title: 'Select optimal pair — rank by Score, then B, then R_pos',
                  text: 'The selection hierarchy is: (1) highest composite Score; (2) lowest burden B as tiebreaker; (3) highest R_pos as second tiebreaker; (4) most restrictive (highest percentile sum) as final tiebreaker. The optimal pair is saved to tab_TC5_optimal_pair_pu.csv.',
                  tag: 'Selection',
                  tagColor: 'text-teal-700 bg-teal-50 border-teal-200',
                },
                {
                  step: '8',
                  title: 'Sensitivity analysis — weights, alphas, B_target',
                  text: 'Three sensitivity experiments test robustness: (i) alternative weight triplets (w₁, w₂, w₃); (ii) alternative confidence weight triplets (α_E, α_I, α_C); (iii) alternative per-municipality B_target values (6, 12, 18, 24 ep/yr/muni). Each experiment re-runs the composite score under the alternative parameters and reports the optimal pair. Results confirm stability across all tested configurations.',
                  tag: 'Sensitivity',
                  tagColor: 'text-emerald-700 bg-emerald-50 border-emerald-200',
                },
              ].map((item) => (
                <div key={item.step} className="flex gap-4">
                  <div className="flex-shrink-0 flex items-start pt-0.5">
                    <div className="h-7 w-7 rounded-full bg-gray-100 border border-gray-300 flex items-center justify-center text-xs font-bold text-gray-600">
                      {item.step}
                    </div>
                  </div>
                  <div className="flex-1 rounded-xl border border-gray-200 p-4">
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <h3 className="text-sm font-semibold text-gray-900">{item.title}</h3>
                      <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${item.tagColor}`}>
                        {item.tag}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 leading-relaxed">{item.text}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Key results ───────────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-5 text-xl font-bold text-gray-900">Key Results</h2>

            <div className="grid gap-4 md:grid-cols-2 mb-6">
              <div className="rounded-xl border-2 border-emerald-200 bg-white p-5">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">PU-optimal threshold pair</h3>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div><span className="text-gray-500">Hₛ threshold</span><br /><span className="font-bold text-2xl text-gray-900">q90</span></div>
                  <div><span className="text-gray-500">SSH_total threshold</span><br /><span className="font-bold text-2xl text-gray-900">q90</span></div>
                  <div><span className="text-gray-500">Positive set P</span><br /><span className="font-bold text-gray-800">147 events (56 expanded + 91 legacy)</span></div>
                  <div><span className="text-gray-500">Evaluable (grid-mapped)</span><br /><span className="font-bold text-gray-800">~143 (4 expanded cities unmapped)</span></div>
                  <div><span className="text-gray-500">B_target_effective</span><br /><span className="font-bold text-gray-800">12 × 27 = 324 ep/yr</span></div>
                  <div><span className="text-gray-500">N_union_cities</span><br /><span className="font-bold text-gray-800">27 municipalities</span></div>
                  <div><span className="text-gray-500">Result</span><br /><span className="font-bold text-gray-800">q70/q99</span></div>
                  <div><span className="text-gray-500">Near-matches</span><br /><span className="font-bold text-gray-800">2 (±3 d, Florianópolis)</span></div>
                </div>
              </div>

              <div className="space-y-3">
                <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
                  <h3 className="text-xs font-semibold text-blue-900 mb-1.5">Why the earlier q90/q90 agreement did not survive</h3>
                  <p className="text-xs text-blue-800 leading-relaxed">
                    Step 2d (CSI, 91 legacy events) and the first Step 2e calibration both selected
                    q90/q90, and that agreement was read as convergent evidence. It was not: both
                    sweeps stopped <em>at</em> q90, and both scored a detector built on
                    SSH_total = zos + tide. Recalibrating on the production detector over a grid
                    extended to q95 and q99 showed the composite score has no interior optimum —
                    Spearman(Score, accepted episodes) = −0.999 — so q90/q90 had only ever looked
                    optimal because the grid ended there. See AUD-01 §14.
                  </p>
                </div>
                <div className="rounded-xl border border-gray-200 bg-white p-4">
                  <h3 className="text-xs font-semibold text-gray-900 mb-1.5">Robustness across sensitivity experiments</h3>
                  <p className="text-xs text-gray-600 leading-relaxed">
                    Across the 14 variants tested (weights, alphas, expected rate, episode gap), the
                    level percentile <strong>q99 is selected in 14 of 14</strong>. The wave percentile
                    is the poorly determined axis: q70 in 8, q50 in 2, q85 in 2, q95 in 1, q99 in 1.
                    The six best pairs differ by less than 1 % in score and span q50 to q80, so the
                    composite score does not carry the information to fix the wave threshold — which
                    matters for AUD-02, where a physical floor would have to come from outside this
                    calibration.
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
              <h3 className="text-sm font-semibold text-amber-900 mb-2">Scientific interpretation — why the score is negative</h3>
              <p className="text-xs text-amber-800 leading-relaxed">
                The composite score at the selected pair q70/q99 is −0.318. It is negative because the
                soft penalty still dominates: 831 unmatched episodes, most with low qᵢ. That does not mean
                the detector is useless — it means the PU framework correctly identifies that most
                unmatched episodes lack independent corroboration and cannot be confidently attributed to
                real events. The score is <em>relative</em>: q70/q99 scores better than any other of the
                121 pairs. Against the superseded q90/q90 <em>under the same detector</em>, it achieves the
                identical recall (H = 28 of 147) with 62 % fewer unmatched detections — 831 against 2 214 —
                and a detection rate of 1.42 against an anchor of 2.0 per municipality per year.
              </p>
            </div>
          </div>
        </div>

        {/* ── Score Decomposition ────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-2 text-xl font-bold text-gray-900">Score Decomposition</h2>
            <p className="mb-6 text-sm text-gray-600 max-w-3xl">
              Full decomposition of <strong>Score(θ) = w₁·R_pos − w₂·B − w₃·F_soft/P</strong> across all 121
              threshold pairs of the extended grid (q50…q90, q95, q99). Each heatmap shows one weighted term,
              making it transparent which component dominates the final score at each pair. The selected pair
              (q70/q99) is marked with a black border.
            </p>
            <ScoreDecompositionHeatmaps />
          </div>
        </div>

        {/* ── q_i Decomposition ────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-2 text-xl font-bold text-gray-900">Episode Confidence Decomposition (qᵢ)</h2>
            <p className="mb-6 text-sm text-gray-600 max-w-3xl">
              Per-episode breakdown of the confidence weight qᵢ at the selected pair (q70/q99).
              Shows the weighted contribution of each component — external evidence (α_E·Eᵢ),
              physical intensity (α_I·Iᵢ), and context coherence (α_C·Cᵢ) — so that the
              driver of each episode&apos;s penalty (1 − qᵢ) is immediately visible.
              Sortable by any column. Filter by municipality or evidence status.
            </p>
            <QiDecompositionTable />
          </div>
        </div>

        {/* ── Figures ───────────────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-2 text-xl font-bold text-gray-900">Figures</h2>
            <p className="mb-6 text-sm text-gray-500">
              {tc5Figures.length} figures · score surface heatmaps · CSI/PU comparison · sensitivity analysis · episode audit · city/database source audit
            </p>
            <FigureGallery figures={tc5Figures} groups={tc5FigureGroups} />
          </div>
        </div>

        {/* ── Calibrated threshold for Step 3 ──────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-5 text-xl font-bold text-gray-900">Output: Calibrated Threshold for Step 3</h2>
            <div className="space-y-3">
              {[
                {
                  label: 'The calibrated pair is q70/q99, selected on 2026-07-30 over a 121-pair grid, scoring the production detector.',
                  text: 'Step 2d (CSI, 91 legacy events) and Step 2e (PU composite, combined 147-event set: 56 expanded + 91 legacy, 27 municipalities) both select q90/q90. The result is robust to the events database used, the calibration objective, and all sensitivity parameters tested. B_target_effective = 12 × 27 = 324 ep/yr using the union of both database city sets.',
                },
                {
                  label: 'The threshold is defined locally, not domain-wide.',
                  text: 'Thresholds are percentiles of the local climatological series at each municipality\'s nearest coastal grid point, computed from the validated period (approximately 1998–2020). The q90 label does not correspond to a single fixed Hₛ or SSH_total value — it means the top 10% of local conditions at each location.',
                },
                {
                  label: 'The high unmatched count reflects under-reporting, not detector failure.',
                  text: '831 unmatched compound episodes remain at q70/q99, against 2 214 at the superseded q90/q90 under the same detector. The PU framework assigns most of them low qᵢ weights, which is consistent with under-reporting being the dominant explanation rather than spurious oceanic detections. External evidence is available for only 0.04 % of unmatched episodes, which is why α_E was reduced from 0.60 to 0.20: the term was measuring the sparseness of the register, not the implausibility of a detection.',
                },
                {
                  label: 'Step 3 receives: tab_TC5_optimal_pair_pu.csv → q70/q99.',
                  text: 'The optimal threshold pair (hs_percentile=90, ssh_percentile=90) is passed to Step 3 (Storm Catalog Generation), where it defines the exceedance thresholds used to identify independent compound storm episodes in the full 1993–2025 series at all coastal grid points across the five SC coastal sectors.',
                },
              ].map((item, i) => (
                <div key={i} className="rounded-xl border border-gray-200 bg-white p-5">
                  <div className="flex gap-3">
                    <span className="text-blue-600 font-bold flex-shrink-0 mt-0.5">{i + 1}.</span>
                    <div>
                      <p className="text-sm font-semibold text-gray-900 mb-1">{item.label}</p>
                      <p className="text-xs text-gray-600 leading-relaxed">{item.text}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Navigation ────────────────────────────────────────────────────── */}
        <div className="bg-white py-12">
          <div className="mx-auto max-w-5xl px-6 flex items-center justify-between">
            <Link
              href="/results/threshold-calibration/csi-scan"
              className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Step 2d — CSI Grid Scan
            </Link>
            <Link
              href="/results/threshold-calibration"
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 transition-colors font-medium"
            >
              Threshold Calibration hub
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>

      </main>
      <Footer />
    </>
  );
}
