import Image from 'next/image';
import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';

export const metadata = {
  title: 'Threshold Calibration (CSI Grid Scan) — OSR11',
  description:
    'Systematic optimisation of Hₛ and SSH_total exceedance thresholds against the 91-event SC coastal disaster database. CSI grid scan over q50–q90 threshold pairs (every 5 percentile points) with causal/antecedent matching window.',
};

export default function ThresholdCalibrationPage() {
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
              <span className="text-gray-600">Threshold Calibration</span>
            </div>

            <div className="flex flex-wrap items-start gap-2 mb-4">
              <StatusBadge status="done" />
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Step 4</span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Full SC coast · 5 sectors · 91 events</span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">81 threshold pairs · CSI optimisation</span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              Threshold Calibration
              <br />
              <span className="text-blue-600">CSI Grid Scan — Hₛ × SSH_total</span>
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-gray-600">
              Systematic optimisation of Hₛ and SSH_total (= SSH + FES2022 tide) exceedance thresholds
              against the 91-event SC coastal disaster database. For each of 81 threshold pair
              combinations, the analysis evaluates hits, misses, and false alarms using an asymmetric
              causal matching window, then selects the pair that maximises CSI.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              {[
                { label: 'Threshold grid',  value: 'q50–q90, every 5 percentile points (9 × 9 = 81 pairs) · configurable via pct_step in analysis_config.py' },
                { label: 'SSH variable',    value: 'SSH_total = zos + FES2022 tide (00:00 UTC instantaneous)' },
                { label: 'Match window',    value: '[D-2, D-1, D, D+1 00Z] — causal/antecedent' },
                { label: 'Primary metric',  value: 'CSI = H / (H + M + F)' },
                { label: 'Local thresholds', value: 'Per grid point · validated-period climatology (~25 yr)' },
                { label: 'Events',          value: '91 events · 22 municipalities · 5 sectors' },
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
            <h2 className="mb-4 text-xl font-bold text-gray-900">What this analysis is about</h2>
            <div className="grid gap-6 md:grid-cols-2">
              <p className="text-sm text-gray-700 leading-relaxed">
                Steps 2 and 3 of the OSR11 pipeline used a fixed q90 threshold for both Hₛ and SSH_total,
                and found that only 2–13 of the 91 reported SC coastal disasters show concurrent
                exceedances within the event window. This low detection rate is expected:
                q90 is a conventional starting point, not an empirically calibrated threshold.
                <br /><br />
                Step 4 asks: <strong>which pair of (Hₛ, SSH_total) thresholds best separates the
                91 reported coastal disasters from background ocean conditions?</strong> Instead of
                assuming q90, the analysis sweeps all combinations from q50 to q90 (in steps of 0.05)
                and evaluates, for each pair, how many events are captured (hits), missed, and how
                many spurious compound detections occur outside event windows (false alarms).
              </p>
              <p className="text-sm text-gray-700 leading-relaxed">
                The Critical Success Index (CSI) summarises all three counts into a single skill score:
                <br /><br />
                <code className="text-xs bg-gray-200 px-1.5 py-0.5 rounded">CSI = H / (H + M + F)</code>
                <br /><br />
                A CSI of 1 means perfect detection; a CSI of 0 means no skill. The CSI penalises
                both misses (too restrictive a threshold) and false alarms (too permissive a threshold),
                making it the appropriate metric when the target is a balanced detector.
                <br /><br />
                The calibrated threshold pair from Step 4 directly informs Step 5 (Storm Catalog
                Generation), where it is used to define independent compound storm episodes in the
                full 1993–2025 time series.
              </p>
            </div>
          </div>
        </div>

        {/* ── Methodological step-by-step ───────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-6 text-xl font-bold text-gray-900">Methodology — Step by Step</h2>
            <div className="space-y-4">
              {[
                {
                  step: '0',
                  title: 'Reuse infrastructure from Steps 2–3',
                  text: 'The municipality→grid association uses a centralised preprocessing reference (outputs/preprocessing/municipality_grid_ref.csv) that selects the nearest grid point with ≥80% valid data across the full time series — resolving NaN-coverage issues for northern SC municipalities. Climatological Hₛ and SSH series and the FES2022 tidal cache from Steps 2–3 are reused without modification. SSH_total = SSH + FES2022 tide (instantaneous 00:00 UTC) is computed for each unique grid point.',
                  tag: 'Reuse',
                  tagColor: 'text-emerald-700 bg-emerald-50 border-emerald-200',
                },
                {
                  step: '0b',
                  title: 'Temporal domain restriction — clip to validated period',
                  text: 'The unified dataset spans 1993–2025, but the SC disaster database covers only 1998–2023. Without restriction, Layer 2 would scan ~7 unvalidated years and classify every compound episode there as a false alarm — not because the episode is spurious, but because no validation record exists for those periods. This inflates F and distorts FAR. The preprocessing layer clips the dataset to [min(event_dates) + min(offsets), max(event_dates) + max(offsets)], i.e., from roughly late 1997 to early 2024. Both the false alarm scan (Layer 2) and the quantile threshold computation operate on this validated period only.',
                  tag: 'Preprocessing',
                  tagColor: 'text-amber-700 bg-amber-50 border-amber-200',
                },
                {
                  step: '1',
                  title: 'Define the causal matching window [D-2, D-1, D, D+1 00Z]',
                  text: 'For each reported event on civil date D, the admissible match timestamps are D-2, D-1, D, and D+1 (operational 00Z tolerance). The window is asymmetric: antecedents are allowed (the forcing may precede the reported impact by 1–2 days), but compound episodes detected only on D+2 or later are NOT considered matches.',
                  tag: 'Key decision',
                  tagColor: 'text-blue-700 bg-blue-50 border-blue-200',
                },
                {
                  step: '2',
                  title: 'Build the threshold grid',
                  text: 'Nine percentile levels are tested for each variable: q50, q55, q60, q65, q70, q75, q80, q85, q90 (every 5 percentile points). This produces 81 threshold pairs. The sweep range and step are controlled by three parameters in analysis_config.py (pct_start, pct_stop, pct_step), making it straightforward to change resolution (e.g., every 2%) or extend the range (e.g., to q95). Thresholds are computed locally at each municipality\'s grid point using the validated-period climatological series (~25 years, not the full 1993–2025 record), not seasonally.',
                  tag: 'Grid scan',
                  tagColor: 'text-violet-700 bg-violet-50 border-violet-200',
                },
                {
                  step: '3',
                  title: 'Layer 1 — Event-by-event hit/miss evaluation',
                  text: 'For each threshold pair and each of the 91 observed events: extract Hₛ(t) and SSH_total(t) at the event\'s grid point; check if both exceed their local thresholds at any of the match times; record hit (H) or miss (M). This layer requires 91 × 81 = 7,371 evaluations.',
                  tag: 'Layer 1',
                  tagColor: 'text-orange-700 bg-orange-50 border-orange-200',
                },
                {
                  step: '4',
                  title: 'Layer 2 — False alarm detection from the full series',
                  text: 'For each unique grid point and each threshold pair: scan the validated-period series (after preprocessing clip, ~1998–2023) for compound days (both conditions simultaneously exceeded); cluster consecutive compound days into episodes (gap ≤ 1 day); check if each episode overlaps with any observed event\'s causal window at that grid point. Episodes that do not overlap → false alarms (F). The temporal restriction ensures F only counts episodes that the validation database is in a position to confirm or reject.',
                  tag: 'Layer 2',
                  tagColor: 'text-red-700 bg-red-50 border-red-200',
                },
                {
                  step: '5',
                  title: 'Compute CSI, POD, FAR for each threshold pair',
                  text: 'POD = H/(H+M); FAR = F/(H+F); CSI = H/(H+M+F). These three metrics form the verification grid used to select the optimal threshold pair.',
                  tag: 'Metrics',
                  tagColor: 'text-gray-700 bg-gray-100 border-gray-200',
                },
                {
                  step: '6',
                  title: 'Select the optimal threshold pair',
                  text: 'Selection hierarchy: (1) highest CSI; (2) lowest FAR as tiebreaker (prefer less permissive solutions); (3) highest percentile sum (most restrictive pair) as second tiebreaker. The selected pair is saved to tab_TC4_optimal_pair.csv and passed to Step 5.',
                  tag: 'Selection',
                  tagColor: 'text-teal-700 bg-teal-50 border-teal-200',
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

        {/* ── Causal window rationale ───────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-4 text-xl font-bold text-gray-900">The Causal/Antecedent Matching Window</h2>
            <p className="mb-6 text-sm text-gray-600 max-w-3xl">
              This is the central methodological decision of Step 4. An observed event reported on civil
              date <strong>D</strong> is considered <em>captured</em> if the compound condition holds at any
              of the following daily 00Z timestamps:
            </p>

            <div className="grid gap-4 md:grid-cols-4 mb-8">
              {[
                {
                  offset: 'D-2',
                  color: 'border-blue-300 bg-blue-50',
                  label: 'Early antecedent',
                  desc: 'Joint forcing arrived 2 days before the reported impact. Physical: large swells from distant storms may arrive well before the peak coastal damage is recorded.',
                },
                {
                  offset: 'D-1',
                  color: 'border-blue-200 bg-blue-50/70',
                  label: 'Late antecedent',
                  desc: 'Compound condition on the day before the reported event. Often the scenario closest to the actual peak forcing.',
                },
                {
                  offset: 'D',
                  color: 'border-gray-300 bg-white',
                  label: 'Event day',
                  desc: 'The civil date of the reported disaster. Corresponds to the 00:00 UTC snapshot of the event day.',
                },
                {
                  offset: 'D+1 00Z',
                  color: 'border-orange-200 bg-orange-50',
                  label: 'Operational tolerance',
                  desc: 'If the compound peak occurred during the afternoon or evening of civil day D (e.g., 18:00 UTC), it appears at 00Z of D+1 in the daily snapshot series. This step avoids penalising for UTC convention.',
                },
              ].map((w) => (
                <div key={w.offset} className={`rounded-xl border p-4 ${w.color}`}>
                  <div className="text-lg font-bold text-gray-800 mb-1">{w.offset}</div>
                  <div className="text-xs font-semibold text-gray-600 mb-2">{w.label}</div>
                  <p className="text-xs text-gray-600 leading-relaxed">{w.desc}</p>
                </div>
              ))}
            </div>

            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
              <p className="text-xs font-semibold text-amber-800 mb-1">Important: the window is asymmetric</p>
              <p className="text-xs text-amber-700 leading-relaxed">
                Compound episodes detected only on <strong>D+2 or later</strong> are <strong>not</strong> counted
                as matches for the reported event on D. The logic is explicitly causal: a physical forcing that
                arrives two or more days after the reported disaster cannot have caused it. This restriction
                prevents the method from inflating its hit count by claiming post-hoc associations.
              </p>
            </div>
          </div>
        </div>

        {/* ── Metrics explained ─────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-6 text-xl font-bold text-gray-900">Verification Metrics</h2>
            <div className="grid gap-4 md:grid-cols-3">
              {[
                {
                  name: 'POD',
                  full: 'Probability of Detection',
                  formula: 'H / (H + M)',
                  range: '0–1 (higher = better)',
                  color: 'border-blue-200 bg-blue-50',
                  text: 'What fraction of the observed disasters was captured? POD is the primary sensitivity measure. Maximising POD alone would lead to very permissive (low) thresholds that flag almost everything.',
                },
                {
                  name: 'FAR',
                  full: 'False Alarm Ratio',
                  formula: 'F / (H + F)',
                  range: '0–1 (lower = better)',
                  color: 'border-red-100 bg-red-50',
                  text: 'What fraction of compound detections do NOT correspond to any reported disaster? High FAR means the detector fires too often. Minimising FAR alone would lead to very restrictive thresholds that rarely detect anything.',
                },
                {
                  name: 'CSI',
                  full: 'Critical Success Index',
                  formula: 'H / (H + M + F)',
                  range: '0–1 (higher = better)',
                  color: 'border-emerald-200 bg-emerald-50',
                  text: 'The primary optimisation metric. CSI penalises both misses and false alarms simultaneously. A CSI of 1 means every observed event is captured and no spurious episodes exist. CSI is 0 when there are no hits.',
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

            <div className="mt-6 rounded-xl border border-gray-200 p-5 bg-gray-50">
              <h3 className="text-sm font-semibold text-gray-900 mb-2">Why not also compute Brier Score or ETS?</h3>
              <p className="text-xs text-gray-600 leading-relaxed">
                The Equitable Threat Score (ETS) and Brier Score require knowing the number of
                <em> true negatives</em> (days where no event was reported AND no compound episode was
                detected). In this application, &ldquo;true negatives&rdquo; are not well-defined: the 32-year series
                has ~12,000 days, but only 91 are labelled as disaster events. The non-event population
                is not a carefully selected control group — it includes periods with no observations at all
                and regions with sparse Civil Defense data. CSI avoids this by focusing exclusively on H,
                M, and F, which are directly interpretable without assumptions about TN.
              </p>
            </div>
          </div>
        </div>

        {/* ── Assumptions and limitations ───────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-5 text-xl font-bold text-gray-900">Key Assumptions &amp; Limitations</h2>
            <ul className="space-y-3 mb-8">
              {[
                {
                  icon: '⚠️',
                  title: 'Daily temporal resolution — instantaneous 00:00 UTC snapshots',
                  text: 'WAVERYS and GLORYS12 are daily datasets. Both SSH and Hₛ use their 00:00 UTC values, and the FES2022 tide is also evaluated at 00:00 UTC (instantaneous snapshot at midnight, not a daily average). Intra-day tidal peaks that occur at other times (e.g., afternoon high tide) are not captured. The D+1 00Z tolerance partially compensates for events whose peak occurred late on civil day D.',
                },
                {
                  icon: '⚠️',
                  title: 'Local percentile thresholds from the full annual series',
                  text: 'Thresholds are computed from the full 1993–2025 climatological series, without seasonal decomposition. This means q80 in winter and q80 in summer correspond to different absolute values of Hₛ and SSH_total. A seasonal threshold would be more physically meaningful but adds complexity and is deferred to a future extension.',
                },
                {
                  icon: '⚠️',
                  title: 'False alarms evaluated only at grid points with observed events',
                  text: 'The false alarm count is restricted to the 22 municipalities with Civil Defense records. Compound episodes at other coastal locations are not counted as false alarms. This keeps the evaluation domain interpretable but means the CSI may be slightly optimistic relative to a full-domain scan.',
                },
                {
                  icon: '⚠️',
                  title: 'Reported event quality and timing uncertainty',
                  text: 'The Leal et al. (2024) database is based on Civil Defense records, which may have reporting delays or missing entries. Dates are civil dates (not UTC datetimes), introducing up to ±12 h of timing uncertainty relative to the 00Z snapshot convention.',
                },
                {
                  icon: '⚠️',
                  title: 'Data coverage near complex coastal geometries',
                  text: 'Northern SC municipalities (Araquari, São Francisco do Sul, Itapoá, etc.) are near estuaries and embayments that may lie at or beyond the limit of the GLORYS12/WAVERYS grid resolution. The preprocessing reference (src/preprocessing/municipality_grid_ref.py) selects the nearest grid point with ≥80% valid data across the full series, which may be a few kilometres offshore. Municipalities where no grid point meets this threshold are flagged as insufficient_data in the reference table and logged at run time.',
                },
                {
                  icon: '⚠️',
                  title: 'Single global matching window',
                  text: 'The same [D-2, D-1, D, D+1] window is applied to all municipalities regardless of coastal sector, distance to open ocean, or local wave/surge propagation times. A future sensitivity analysis could test sector-specific or distance-based windows.',
                },
              ].map((lim, i) => (
                <li key={i} className="rounded-xl border border-gray-200 bg-white p-4">
                  <div className="flex gap-3">
                    <span className="text-lg flex-shrink-0">{lim.icon}</span>
                    <div>
                      <p className="text-sm font-semibold text-gray-800 mb-1">{lim.title}</p>
                      <p className="text-xs text-gray-600 leading-relaxed">{lim.text}</p>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* ── Key results summary ───────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <div className="flex flex-wrap items-center gap-3 mb-6">
              <StatusBadge status="done" />
              <h2 className="text-xl font-bold text-gray-900">Results</h2>
            </div>

            {/* Optimal pair highlight */}
            <div className="rounded-xl border-2 border-emerald-300 bg-emerald-50 p-5 mb-8">
              <h3 className="text-sm font-semibold text-emerald-900 mb-3">
                Optimal threshold pair (maximum CSI)
              </h3>
              <div className="flex flex-wrap gap-4">
                {[
                  { label: 'Hₛ threshold',       value: 'q90', sub: '90th percentile' },
                  { label: 'SSH_total threshold', value: 'q55', sub: '55th percentile' },
                  { label: 'Hits (H)',            value: '42',  sub: 'of 91 events captured' },
                  { label: 'Misses (M)',          value: '49',  sub: 'events not captured' },
                  { label: 'False alarms (F)',    value: '3 406', sub: 'spurious compound episodes' },
                  { label: 'POD',                value: '0.46', sub: 'H / (H + M)' },
                  { label: 'FAR',                value: '0.99', sub: 'F / (H + F)' },
                  { label: 'CSI',                value: '0.012', sub: 'H / (H + M + F)' },
                ].map((m) => (
                  <div key={m.label} className="rounded-lg border border-emerald-200 bg-white px-4 py-3 min-w-[110px]">
                    <div className="text-xs text-gray-500 mb-0.5">{m.label}</div>
                    <div className="text-xl font-black text-gray-900">{m.value}</div>
                    <div className="text-xs text-gray-400">{m.sub}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Interpretation note */}
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 mb-8">
              <p className="text-xs font-semibold text-amber-800 mb-1">Interpreting these results</p>
              <p className="text-xs text-amber-700 leading-relaxed">
                The optimal pair (Hₛ=q90, SSH_total=q55) captures <strong>42 of 91 events (POD=0.46)</strong> but
                produces <strong>3 406 false alarms</strong> — compound episodes in the full 32-year series with no
                matching reported disaster. This leads to a very low CSI (0.012) and FAR near 1. The dominant driver
                is the low SSH_total threshold (q55), which causes the compound condition to fire very frequently
                at all grid points. The CSI grid scan confirms that no threshold pair in the q50–q90 range achieves
                a meaningful balance between POD and FAR at daily resolution with the current 91-event database.
                This is an important result: it indicates that the compound signal as defined here (simultaneous
                daily exceedances) is too common relative to the reporting density, motivating either a stricter
                compound definition, episodic clustering, or a move to sub-daily data.
              </p>
            </div>

            {/* Capture lag summary table */}
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Capture lag distribution at optimal pair</h3>
            <div className="mb-8 overflow-x-auto rounded-xl border border-gray-200 bg-gray-50">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-100">
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Offset</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-700">Label</th>
                    <th className="px-4 py-3 text-center font-semibold text-gray-700">Captures</th>
                    <th className="px-4 py-3 text-center font-semibold text-gray-700">Fraction</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { offset: 'D-2', label: 'Early antecedent', count: 8,  frac: '19%' },
                    { offset: 'D-1', label: 'Late antecedent',  count: 13, frac: '31%' },
                    { offset: 'D',   label: 'Event day',        count: 15, frac: '36%' },
                    { offset: 'D+1 00Z', label: 'Operational tolerance', count: 6, frac: '14%' },
                  ].map((r, i) => (
                    <tr key={r.offset} className={`border-b border-gray-100 ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}>
                      <td className="px-4 py-2.5 font-mono font-semibold text-gray-800">{r.offset}</td>
                      <td className="px-4 py-2.5 text-gray-600">{r.label}</td>
                      <td className="px-4 py-2.5 text-center font-bold text-gray-800">{r.count}</td>
                      <td className="px-4 py-2.5 text-center text-gray-600">{r.frac}</td>
                    </tr>
                  ))}
                  <tr className="border-t-2 border-gray-300 bg-gray-100">
                    <td className="px-4 py-2.5 font-semibold text-gray-800" colSpan={2}>Total hits</td>
                    <td className="px-4 py-2.5 text-center font-black text-gray-900">42</td>
                    <td className="px-4 py-2.5 text-center font-semibold text-gray-700">100%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* ── Figure TC4-H1: CSI heatmap ────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">fig_TC4_H1</span>
              <h2 className="text-xl font-bold text-gray-900">CSI Grid Scan</h2>
            </div>
            <p className="mb-6 text-sm text-gray-600 max-w-2xl">
              CSI across all 81 threshold pairs (Hₛ × SSH_total, q50–q90). The ★ marks the optimal pair
              (Hₛ=q90, SSH_total=q55). A broad plateau would indicate robustness; the absence of one
              confirms the sensitivity of CSI to the false-alarm structure in this dataset.
            </p>
            <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
              <div className="p-5">
                <Image
                  src="/figures/tc4_summary/fig_TC4_H1_csi_heatmap.png"
                  alt="Figure TC4-H1 — CSI heatmap"
                  width={900} height={750}
                  className="w-full h-auto rounded-lg"
                  unoptimized
                />
              </div>
              <div className="border-t border-gray-100 px-5 py-4">
                <p className="text-xs text-gray-500 italic leading-relaxed">
                  CSI = H / (H + M + F) for each (Hₛ, SSH_total) percentile pair. Optimal pair marked with ★.
                  Values annotated in each cell. Colourmap: YlGn (0 = white, higher = darker green).
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* ── Figures TC4-H2 and TC4-H3 side by side ───────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-6 text-xl font-bold text-gray-900">FAR and POD Heatmaps</h2>
            <div className="grid gap-8 md:grid-cols-2">
              <div>
                <div className="flex flex-wrap items-center gap-3 mb-2">
                  <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">fig_TC4_H2</span>
                  <h3 className="text-base font-bold text-gray-900">False Alarm Ratio</h3>
                </div>
                <p className="mb-4 text-xs text-gray-600">
                  FAR = F / (H + F). High FAR (near 1) for most pairs confirms that compound episodes
                  in the full series vastly outnumber reported events, regardless of threshold.
                </p>
                <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
                  <div className="p-4">
                    <Image
                      src="/figures/tc4_summary/fig_TC4_H2_far_heatmap.png"
                      alt="Figure TC4-H2 — FAR heatmap"
                      width={700} height={600}
                      className="w-full h-auto rounded-lg"
                      unoptimized
                    />
                  </div>
                </div>
              </div>
              <div>
                <div className="flex flex-wrap items-center gap-3 mb-2">
                  <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">fig_TC4_H3</span>
                  <h3 className="text-base font-bold text-gray-900">Probability of Detection</h3>
                </div>
                <p className="mb-4 text-xs text-gray-600">
                  POD = H / (H + M). POD decreases toward the top-right (more restrictive thresholds).
                  The best POD (~0.59) is achieved at q85/q50 but with even higher false alarms.
                </p>
                <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
                  <div className="p-4">
                    <Image
                      src="/figures/tc4_summary/fig_TC4_H3_pod_heatmap.png"
                      alt="Figure TC4-H3 — POD heatmap"
                      width={700} height={600}
                      className="w-full h-auto rounded-lg"
                      unoptimized
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Figure TC4-S1: ranking scatter ────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">fig_TC4_S1</span>
              <h2 className="text-xl font-bold text-gray-900">Threshold Ranking: POD vs FAR</h2>
            </div>
            <p className="mb-6 text-sm text-gray-600 max-w-2xl">
              All 81 threshold pairs plotted in POD–FAR space. Bubble size is proportional to CSI;
              the optimal pair (★) is highlighted. The clustering of all points near FAR=1 reveals
              the dominant false-alarm problem at daily resolution.
            </p>
            <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
              <div className="p-5">
                <Image
                  src="/figures/tc4_summary/fig_TC4_S1_ranking_scatter.png"
                  alt="Figure TC4-S1 — Ranking scatter POD vs FAR"
                  width={800} height={650}
                  className="w-full h-auto rounded-lg"
                  unoptimized
                />
              </div>
              <div className="border-t border-gray-100 px-5 py-4">
                <p className="text-xs text-gray-500 italic leading-relaxed">
                  POD vs FAR for all 81 pairs (q50–q90 × q50–q90). Bubble size ∝ CSI. Optimal pair marked with ★.
                  Preferred region: upper-left (high POD, low FAR). The absence of any pair near the upper-left
                  confirms the false-alarm problem is structural at this temporal resolution.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* ── Figure TC4-S2: per-event hit/miss ────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">fig_TC4_S2</span>
              <h2 className="text-xl font-bold text-gray-900">Per-Event Hit / Miss — Optimal Pair</h2>
            </div>
            <p className="mb-6 text-sm text-gray-600 max-w-2xl">
              Each of the 91 reported SC coastal disasters shown as a horizontal bar: green = captured (hit),
              red = missed. At the optimal pair (Hₛ=q90, SSH_total=q55), 42 events are hits and 49 are misses.
            </p>
            <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
              <div className="p-5">
                <Image
                  src="/figures/tc4_summary/fig_TC4_S2_event_hits.png"
                  alt="Figure TC4-S2 — Per-event hit/miss chart"
                  width={1000} height={1200}
                  className="w-full h-auto rounded-lg"
                  unoptimized
                />
              </div>
              <div className="border-t border-gray-100 px-5 py-4">
                <p className="text-xs text-gray-500 italic leading-relaxed">
                  Hit/miss at optimal pair (Hₛ=q90, SSH_total=q55). Green = compound condition met within [D-2, D+1 00Z].
                  Red = not met. Events sorted by date within sector.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* ── Figures TC4-S3 and TC4-S4 side by side ───────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <div className="grid gap-8 md:grid-cols-2">
              <div>
                <div className="flex flex-wrap items-center gap-3 mb-2">
                  <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">fig_TC4_S3</span>
                  <h3 className="text-base font-bold text-gray-900">Capture Lag Distribution</h3>
                </div>
                <p className="mb-4 text-xs text-gray-600">
                  Of the 42 hits: most (36%) are captured on the event day itself (D 00Z); 31% on D-1
                  (antecedent forcing); 19% on D-2; 14% via the D+1 operational tolerance.
                </p>
                <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
                  <div className="p-4">
                    <Image
                      src="/figures/tc4_summary/fig_TC4_S3_lag_distribution.png"
                      alt="Figure TC4-S3 — Capture lag distribution"
                      width={600} height={500}
                      className="w-full h-auto rounded-lg"
                      unoptimized
                    />
                  </div>
                </div>
              </div>
              <div>
                <div className="flex flex-wrap items-center gap-3 mb-2">
                  <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">fig_TC4_S4</span>
                  <h3 className="text-base font-bold text-gray-900">POD by Coastal Sector</h3>
                </div>
                <p className="mb-4 text-xs text-gray-600">
                  POD disaggregated by coastal sector at the optimal pair. Reveals whether detection
                  performance is geographically uniform or sector-dependent.
                </p>
                <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
                  <div className="p-4">
                    <Image
                      src="/figures/tc4_summary/fig_TC4_S4_sector_pod.png"
                      alt="Figure TC4-S4 — POD by coastal sector"
                      width={900} height={500}
                      className="w-full h-auto rounded-lg"
                      unoptimized
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── What comes next ───────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-4 text-xl font-bold text-gray-900">What these results feed into</h2>
            <div className="rounded-xl border border-gray-200 bg-white p-5">
              <ul className="space-y-2">
                {[
                  { arrow: '→', text: 'Step 5 (Storm Catalog Generation): the optimal threshold pair from tab_TC4_optimal_pair.csv defines the exceedance thresholds used to identify independent storm episodes across the full 32-year series at all coastal grid points.' },
                  { arrow: '→', text: 'Step 6 (Compound Event Detection): compound events are identified as temporal overlaps between Hₛ and SSH_total storm episodes in the catalogs produced by Step 5.' },
                  { arrow: '→', text: 'Scientific paper: the CSI grid scan provides the empirical justification for the chosen detection thresholds, replacing the arbitrary q90 assumption of the preliminary analysis.' },
                ].map((s, i) => (
                  <li key={i} className="flex gap-2 text-sm text-gray-600">
                    <span className="text-blue-600 font-bold flex-shrink-0">{s.arrow}</span>
                    <span>{s.text}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* ── Navigation ────────────────────────────────────────────────────── */}
        <div className="bg-white py-12">
          <div className="mx-auto max-w-5xl px-6 flex items-center justify-between">
            <Link
              href="/results/tidal-sensitivity"
              className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Tidal Sensitivity Analysis
            </Link>
            <Link
              href="/results"
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 transition-colors font-medium"
            >
              All Results
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
