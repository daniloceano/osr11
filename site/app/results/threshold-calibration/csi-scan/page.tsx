import Image from 'next/image';
import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';
import Tc4EventSelector from '@/components/Tc4EventSelector';

export const metadata = {
  title: 'Threshold Calibration — CSI Grid Scan (Step 3b) — OSR11',
  description:
    'Systematic optimisation of Hₛ and SSH_total exceedance thresholds against the 91-event SC coastal disaster database. CSI grid scan over q50–q90 threshold pairs (every 5 percentile points) with causal/antecedent matching window.',
};

export default function CsiScanPage() {
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
              <span className="text-gray-600">CSI Grid Scan</span>
            </div>

            <div className="flex flex-wrap items-start gap-2 mb-4">
              <StatusBadge status="done" />
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Step 3b</span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Full SC coast · 5 sectors · 91 events</span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">81 threshold pairs · CSI optimisation</span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              CSI Grid Scan
              <br />
              <span className="text-blue-600">Threshold Optimisation — Hₛ × SSH_total</span>
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
                { label: 'SSH variable',    value: 'SSH_total = zos (GLORYS12 00:00 UTC) + FES2022 tide (daily max from hourly)' },
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
                Steps 2 and 4a of the OSR11 pipeline used a fixed q90 threshold for both Hₛ and SSH_total
                as a conventional starting point to build the methodology infrastructure. Step 3b asks
                whether any combination of thresholds in the q50–q90 range can do better — empirically
                calibrated against the 91-event Civil Defense database rather than chosen arbitrarily.
                <br /><br />
                Step 3b asks: <strong>which pair of (Hₛ, SSH_total) thresholds best separates the
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
                The calibrated threshold pair from Step 3b directly informs Step 4 (Storm Catalog
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
                  title: 'Reuse infrastructure from Steps 2–4a',
                  text: 'The municipality→grid association uses a centralised preprocessing reference (outputs/preprocessing/municipality_grid_ref.csv) that selects the nearest grid point with ≥80% valid data across the full time series — resolving NaN-coverage issues for northern SC municipalities. Climatological Hₛ and SSH series and the FES2022 tidal cache from Steps 2–4a are reused without modification. SSH_total = zos (GLORYS12 00:00 UTC snapshot) + FES2022 tide (daily maximum from hourly FES2022 output) is computed for each unique grid point. Hₛ uses the daily maximum from 3-hourly WAVERYS fields.',
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
                  text: 'Selection hierarchy: (1) highest CSI; (2) lowest FAR as tiebreaker (prefer less permissive solutions); (3) highest percentile sum (most restrictive pair) as second tiebreaker. The selected pair is saved to tab_TC4_optimal_pair.csv and passed to Step 4.',
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
              This is the central methodological decision of Step 3b. An observed event reported on civil
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
                  desc: 'The civil date of the reported disaster. Uses the daily maximum of Hₛ and tide within the calendar day; SSH (zos) from the 00:00 UTC GLORYS12 snapshot.',
                },
                {
                  offset: 'D+1 00Z',
                  color: 'border-orange-200 bg-orange-50',
                  label: 'Operational tolerance',
                  desc: 'Operational tolerance for late-day events. Hₛ and tide daily maxima cover the full calendar day, so late peaks on civil day D are already captured on D. This offset also catches cases where the GLORYS12 SSH 00Z snapshot of D+1 better represents the tidal setup peak.',
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
                  title: 'Mixed temporal convention — daily max Hₛ and tide, 00:00 UTC snapshot for SSH',
                  text: 'Hₛ uses the daily maximum derived from 3-hourly WAVERYS fields (8 values per day), capturing the peak wave height within each civil day. The FES2022 tidal component also uses the daily maximum from hourly FES2022 output (24 values per day). GLORYS12 SSH (zos) retains the 00:00 UTC daily snapshot, as GLORYS12 is available at daily frequency only. This mixed convention means SSH_total = zos_00Z + max_tide(day), which is physically more representative of the peak compound forcing than a pure midnight snapshot.',
                },
                {
                  icon: '⚠️',
                  title: 'Local percentile thresholds from the validated-period climatology',
                  text: 'Thresholds are computed from the validated-period climatological series (~25 years, ~1998–2023), not the full 1993–2025 record. This ensures that both the false alarm scan and the quantile computation operate on the same temporal domain. Thresholds are annual (no seasonal decomposition): q80 in winter and q80 in summer correspond to different absolute values of Hₛ and SSH_total. Seasonal thresholds would be more physically meaningful but add complexity and are deferred to a future extension.',
                },
                {
                  icon: '⚠️',
                  title: 'False alarms evaluated only at grid points with observed events',
                  text: 'The false alarm count is restricted to the 22 municipalities with Civil Defense records. Compound episodes at other coastal locations are not counted as false alarms. This keeps the evaluation domain interpretable but means the CSI may be slightly optimistic relative to a full-domain scan.',
                },
                {
                  icon: '⚠️',
                  title: 'Reported event quality and timing uncertainty',
                  text: 'The Leal et al. (2024) database is based on Civil Defense records, which may have reporting delays or missing entries. Dates are civil dates (not UTC datetimes). Daily-maximum Hₛ and tide cover the full 24-hour window of each civil day, which substantially reduces sensitivity to the exact timing of the reported event.',
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
                  { label: 'SSH_total threshold', value: 'q90', sub: '90th percentile' },
                  { label: 'Hits (H)',            value: '21',  sub: 'of 91 events captured' },
                  { label: 'Misses (M)',          value: '70',  sub: 'events not captured' },
                  { label: 'False alarms (F)',    value: '1 298', sub: 'spurious compound episodes' },
                  { label: 'POD',                value: '0.23', sub: 'H / (H + M)' },
                  { label: 'FAR',                value: '0.984', sub: 'F / (H + F)' },
                  { label: 'CSI',                value: '0.0151', sub: 'H / (H + M + F)' },
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
                The optimal pair (Hₛ=q90, SSH_total=q90) captures only <strong>21 of 91 events
                (POD=0.23)</strong> while producing <strong>1 298 false alarms</strong> — compound episodes
                in the validated-period series with no matching reported disaster. This yields a very low
                CSI (0.0151) and FAR near 1. Even at the most restrictive combination tested (q90/q90), the
                compound condition fires ~62× more often than disaster events are reported.
                The CSI grid scan confirms that no threshold pair in the q50–q90 range achieves a meaningful
                balance between POD and FAR at daily resolution with the current 91-event database.
                This is a structural result, not a method failure: simultaneous daily exceedances are far more
                common in the ocean climatology than in the disaster record, motivating either a stricter compound
                definition, episodic clustering, or a move to sub-daily (3-hourly) data where peak timing can
                be assessed more precisely.
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
                    { offset: 'D-2', label: 'Early antecedent', count: 2,  frac: '9.5%' },
                    { offset: 'D-1', label: 'Late antecedent',  count: 7,  frac: '33.3%' },
                    { offset: 'D',   label: 'Event day',        count: 9,  frac: '42.9%' },
                    { offset: 'D+1 00Z', label: 'Operational tolerance', count: 3, frac: '14.3%' },
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
                    <td className="px-4 py-2.5 text-center font-black text-gray-900">21</td>
                    <td className="px-4 py-2.5 text-center font-semibold text-gray-700">100%</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* ── Figure TC4-A1: Grid audit map ─────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">fig_TC4_A1</span>
              <h2 className="text-xl font-bold text-gray-900">Municipality → Grid Point Audit Map</h2>
            </div>
            <p className="mb-6 text-sm text-gray-600 max-w-2xl">
              Spatial audit showing which WAVERYS/GLORYS12 grid point was assigned to each of the
              22 SC municipalities with Civil Defense records. Each municipality centroid is connected
              by a line to its selected nearest grid point with ≥80% valid data across the full time
              series. Points failing the coverage threshold are flagged. Confirms that the spatial
              matching step resolves correctly across all coastal sectors, including northern SC
              (Araquari, São Francisco do Sul, Itapoá) where grid coverage is most constrained.
            </p>
            <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
              <div className="p-5">
                <Image
                  src="/figures/tc4_summary/fig_TC4_A1_grid_audit.png"
                  alt="Figure TC4-A1 — Municipality to grid point audit map"
                  width={1000} height={800}
                  className="w-full h-auto rounded-lg"
                  unoptimized
                />
              </div>
              <div className="border-t border-gray-100 px-5 py-4">
                <p className="text-xs text-gray-500 italic leading-relaxed">
                  Municipality centroids (circles) connected to their assigned WAVERYS/GLORYS12 grid point (crosses).
                  Grid points with ≥80% valid data coverage across 1993–2025 are shown in blue; flagged/insufficient
                  coverage in red. Lines indicate the municipality→grid association used throughout Step 3b.
                  Background shows the SC coastal sector divisions.
                </p>
              </div>
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
              (Hₛ=q90, SSH_total=q90). All values are clustered near zero, reflecting the structural
              dominance of false alarms at daily temporal resolution.
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
                  CSI = H / (H + M + F) for each (Hₛ, SSH_total) percentile pair. Optimal pair (Hₛ=q90, SSH_total=q90)
                  marked with ★ in the Hₛ=q90 group label. Values annotated in each cell.
                  Colourmap: YlGn (0 = white, higher = darker green).
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
                  The best POD (0.73) is achieved at q50/q50 but with the highest false alarm count.
                  At the optimal pair (q90/q90), POD = 0.23.
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
              red = missed. At the optimal pair (Hₛ=q90, SSH_total=q90), 21 events are hits and 70 are misses.
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
                  Hit/miss at optimal pair (Hₛ=q90, SSH_total=q90). Green = compound condition met within [D-2, D+1 00Z].
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
                  Of the 21 hits: most (42.9%) are captured on the event day itself; 33.3% on D-1
                  (antecedent forcing); 9.5% on D-2; 14.3% via the D+1 operational tolerance.
                  The dominance of D and D-1 offsets validates the causal window design.
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

        {/* ── Figure TC4-S5: Peak scatter ───────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">fig_TC4_S5</span>
              <h3 className="text-xl font-bold text-gray-900">Peak Hₛ vs Peak SSH_total — Causal Window</h3>
            </div>
            <p className="mb-4 text-sm text-gray-600 max-w-3xl">
              Each point represents one reported event. The x-axis shows the maximum Hₛ found
              within the causal/antecedent window [D-2, D-1, D, D+1 00Z]; the y-axis shows the
              maximum SSH_total in the same window. Points are coloured by coastal sector.
              <strong> Filled circles</strong> indicate events captured at the optimal threshold pair;{' '}
              <strong>open circles</strong> are missed events. Dashed reference lines show the
              median local threshold across all grid points. The green-shaded quadrant marks the
              region above both median thresholds.
            </p>
            <div className="mb-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800 leading-relaxed">
              <strong>Note:</strong> An event above both threshold lines is not automatically
              captured — the compound condition requires <em>simultaneous</em> exceedance of both
              variables on the same day within the causal window. A high Hₛ peak and a high
              SSH_total peak may fall on different days, preventing detection. Thresholds also vary
              by grid point; the reference lines show the median across all municipalities.
            </div>
            <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
              <div className="p-4">
                <Image
                  src="/figures/tc4_summary/fig_TC4_S5_peak_scatter.png"
                  alt="Figure TC4-S5 — Peak Hₛ vs peak SSH_total within causal window"
                  width={900} height={700}
                  className="w-full h-auto rounded-lg"
                  unoptimized
                />
              </div>
              <div className="border-t border-gray-100 px-5 py-4">
                <p className="text-xs text-gray-500 italic leading-relaxed">
                  Peak absolute values within the causal window [D-2, D-1, D, D+1 00Z] for each
                  reported event. Filled = captured at the optimal pair (Hₛ q{'{'}opt{'}'} /
                  SSH_total q{'{'}opt{'}'}); open = missed. Coloured by coastal sector.
                  Dashed lines: median of local percentile thresholds across all grid points.
                  Green zone: above both median thresholds simultaneously. Detection requires the
                  compound condition to hold on the same day — peak values in different variables
                  on different days do not trigger detection even if both exceed their thresholds.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* ── Spatial performance heatmaps (TC4-M1 / M2 / M3) ─────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-2 text-xl font-bold text-gray-900">Spatial Performance — Heatmaps per Municipality</h2>
            <p className="mb-6 text-sm text-gray-600 max-w-3xl">
              The three heatmaps below break down hits, misses, and false alarms by municipality
              (y-axis) across all 81 threshold pairs (x-axis). Each column in the x-axis represents
              one of the 81 (Hₛ, SSH_total) threshold pair combinations, grouped into nine Hₛ
              percentile bands (q50–q90); within each band, the SSH threshold varies from q50 to q90
              left-to-right. The optimal pair is marked with ★. Municipalities are ordered from
              north to south along the SC coast, with coastal sector boundaries indicated on the
              left margin.
            </p>

            <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 mb-8">
              <p className="text-xs font-semibold text-blue-800 mb-1">How to read these figures</p>
              <ul className="space-y-1 text-xs text-blue-700 list-disc list-inside">
                <li><strong>Hit rate</strong> (TC4-M1): fraction of a municipality&apos;s reported events captured by the compound condition within [D-2, D+1 00Z]. Dark green = good detection.</li>
                <li><strong>Miss rate</strong> (TC4-M2): fraction of events not captured (1 − hit rate). Dark orange/red = the method consistently misses events at that location.</li>
                <li><strong>False alarms</strong> (TC4-M3): number of compound episodes in the validated period that do not coincide with any reported event at that grid point. Darker red = more spurious detections. Municipalities that share the same grid point have identical values.</li>
                <li>Each heatmap cell aggregates all reported events for that municipality at that threshold pair. Municipalities with a single reported event will show binary 0/1 for hit/miss rate.</li>
              </ul>
            </div>

            {/* TC4-M1 */}
            <div className="mb-10">
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">fig_TC4_M1</span>
                <h3 className="text-base font-bold text-gray-900">Hit Rate per Municipality × Threshold Pair</h3>
              </div>
              <p className="mb-4 text-xs text-gray-600 max-w-3xl">
                Fraction of each municipality&apos;s reported events captured at each threshold pair.
                Values near 0 (white) indicate the compound condition is rarely met; values near 1
                (dark green) indicate consistently good capture.
              </p>
              <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
                <div className="p-4">
                  <Image
                    src="/figures/tc4_summary/fig_TC4_M1_city_hit_rate.png"
                    alt="Figure TC4-M1 — Hit rate per municipality"
                    width={1600} height={920}
                    className="w-full h-auto rounded-lg"
                    unoptimized
                  />
                </div>
                <div className="border-t border-gray-100 px-5 py-4">
                  <p className="text-xs text-gray-500 italic leading-relaxed">
                    Hit rate = H / n_events for each (municipality, threshold pair). Colourmap: YlGn.
                    Optimal pair (★) marked with red column boundary.
                  </p>
                </div>
              </div>
            </div>

            {/* TC4-M2 */}
            <div className="mb-10">
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">fig_TC4_M2</span>
                <h3 className="text-base font-bold text-gray-900">Miss Rate per Municipality × Threshold Pair</h3>
              </div>
              <p className="mb-4 text-xs text-gray-600 max-w-3xl">
                Complement of the hit rate. Municipalities that appear uniformly dark across all
                threshold pairs are structural hotspots of misses — suggesting either a different
                physical mechanism, data mismatch, or grid-point representativity issues.
              </p>
              <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
                <div className="p-4">
                  <Image
                    src="/figures/tc4_summary/fig_TC4_M2_city_miss_rate.png"
                    alt="Figure TC4-M2 — Miss rate per municipality"
                    width={1600} height={920}
                    className="w-full h-auto rounded-lg"
                    unoptimized
                  />
                </div>
                <div className="border-t border-gray-100 px-5 py-4">
                  <p className="text-xs text-gray-500 italic leading-relaxed">
                    Miss rate = 1 − hit rate = M / n_events. Colourmap: YlOrRd.
                  </p>
                </div>
              </div>
            </div>

            {/* TC4-M3 */}
            <div>
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <span className="rounded-full bg-gray-100 border border-gray-300 px-2.5 py-1 text-xs font-semibold text-gray-700">fig_TC4_M3</span>
                <h3 className="text-base font-bold text-gray-900">False Alarm Count per Municipality × Threshold Pair</h3>
              </div>
              <p className="mb-4 text-xs text-gray-600 max-w-3xl">
                Number of compound episodes at each municipality&apos;s grid point that are NOT paired
                with any observed event. Reveals geographic hotspots of spurious detections.
                Note: municipalities that share the same grid point will have identical FA counts.
              </p>
              <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
                <div className="p-4">
                  <Image
                    src="/figures/tc4_summary/fig_TC4_M3_city_false_alarms.png"
                    alt="Figure TC4-M3 — False alarms per municipality"
                    width={1600} height={920}
                    className="w-full h-auto rounded-lg"
                    unoptimized
                  />
                </div>
                <div className="border-t border-gray-100 px-5 py-4">
                  <p className="text-xs text-gray-500 italic leading-relaxed">
                    False alarm count F per (municipality, threshold pair). Colourmap: Reds.
                    More lenient thresholds produce more false alarms.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Per-event time-series figures ─────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-2 text-xl font-bold text-gray-900">Per-event Time-Series Inspection</h2>
            <p className="mb-6 text-sm text-gray-600 max-w-3xl">
              Two-panel time-series for each of the 91 reported events, showing daily-maximum Hₛ
              (top) and daily SSH_total = zos + FES2022 tide (bottom) in a 7-day window centred on
              the event date. The local percentile threshold is drawn as a dashed grey line. The blue
              band marks the causal/antecedent matching window [D-2, D-1, D, D+1 00Z].
            </p>
            <div className="mb-6 rounded-xl border border-blue-200 bg-blue-50 p-4 text-xs text-blue-800 leading-relaxed">
              <strong>How to use this tool:</strong> Select a threshold percentile (q50–q90) to
              see how the threshold lines move across the full range tested in the CSI grid scan.
              The <strong>★ optimal pair</strong> is q90/q90. Events captured at the selected
              threshold are marked <span className="font-semibold text-green-700">green ✓</span>;
              missed events are <span className="font-semibold text-red-700">red ✗</span>.
            </div>
            <Tc4EventSelector />
          </div>
        </div>

        {/* ── What comes next ───────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-4 text-xl font-bold text-gray-900">What these results feed into</h2>
            <div className="rounded-xl border border-gray-200 bg-white p-5">
              <ul className="space-y-2">
                {[
                  { arrow: '→', text: 'Step 4 (Storm Catalog Generation): the optimal threshold pair from tab_TC4_optimal_pair.csv defines the exceedance thresholds used to identify independent storm episodes across the full 32-year series at all coastal grid points.' },
                  { arrow: '→', text: 'Step 5 (Compound Event Detection): compound events are identified as temporal overlaps between Hₛ and SSH_total storm episodes in the catalogs produced by Step 4.' },
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
              href="/results/threshold-calibration/tidal-sensitivity"
              className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Tidal Sensitivity Analysis
            </Link>
            <Link
              href="/results/threshold-calibration"
              className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 transition-colors font-medium"
            >
              Threshold Calibration
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
