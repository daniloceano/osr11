import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';

export const metadata = {
  title: 'Threshold Calibration (CSI Grid Scan) — OSR11',
  description:
    'Systematic optimisation of Hₛ and SSH_total exceedance thresholds against the 91-event SC coastal disaster database. CSI grid scan over 81 threshold pairs (q50–q90 × q50–q90) with causal/antecedent matching window.',
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
              <StatusBadge status="in-progress" />
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
                { label: 'Threshold grid',  value: 'q50–q90 in steps of 0.05 (9 × 9 = 81 pairs)' },
                { label: 'SSH variable',    value: 'SSH_total = zos + FES2022 tide' },
                { label: 'Match window',    value: '[D-2, D-1, D, D+1 00Z] — causal/antecedent' },
                { label: 'Primary metric',  value: 'CSI = H / (H + M + F)' },
                { label: 'Local thresholds', value: 'Per grid point · full annual climatology' },
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
                  text: 'The municipality→grid association, climatological Hₛ and SSH series, and FES2022 tidal cache from Steps 2 and 3 are reused without modification. No new grid matching is performed. SSH_total = SSH + FES2022 tide (daily 00:00 UTC) is computed for each unique grid point.',
                  tag: 'Reuse',
                  tagColor: 'text-emerald-700 bg-emerald-50 border-emerald-200',
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
                  text: 'Nine percentile levels are tested for each variable: q50, q55, q60, q65, q70, q75, q80, q85, q90. This produces 81 threshold pairs. Thresholds are computed locally at each municipality\'s grid point using the full annual climatological series (1993–2025), not seasonally.',
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
                  text: 'For each unique grid point and each threshold pair: scan the full 1993–2025 series for compound days (both conditions simultaneously exceeded); cluster consecutive compound days into episodes (gap ≤ 1 day); check if each episode overlaps with any observed event\'s causal window at that grid point. Episodes that do not overlap → false alarms (F).',
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
                  title: 'Daily temporal resolution',
                  text: 'WAVERYS and GLORYS12 are daily datasets. The compound condition is checked at daily 00Z snapshots, not at hourly resolution. Intra-day timing (e.g., whether a tidal peak coincides with the wave maximum) is not resolved. The D+1 00Z tolerance partially compensates for UTC midnight mismatches.',
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
                  title: 'NaN coverage for northern SC municipalities',
                  text: 'Approximately 50% of northern SC municipalities (Araquari, São Francisco do Sul, Itapoá, etc.) have partial or complete NaN coverage due to GLORYS12 and WAVERYS grid resolution limits near complex coastal geometries. These events are treated as misses and reported in the run log.',
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

        {/* ── Results placeholder ───────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <div className="flex flex-wrap items-center gap-3 mb-4">
              <StatusBadge status="in-progress" />
              <h2 className="text-xl font-bold text-gray-900">Results</h2>
            </div>
            <p className="text-sm text-gray-600 mb-6 max-w-2xl">
              The grid scan is currently being executed. Results — including CSI heatmaps,
              the optimal threshold pair, per-event hit/miss tables, and the capture lag
              distribution — will appear here once the analysis is complete.
            </p>

            <div className="grid gap-5 md:grid-cols-2">
              {[
                {
                  code: 'fig_TC4_H1',
                  label: 'CSI Heatmap',
                  desc: 'CSI across all 81 threshold combinations. The cell with the highest CSI (marked with ★) identifies the optimal pair. A broad plateau indicates robustness; a sharp peak suggests strong dependence on the exact threshold choice.',
                },
                {
                  code: 'fig_TC4_H2 / H3',
                  label: 'FAR and POD Heatmaps',
                  desc: 'FAR increases toward the bottom-left (permissive thresholds). POD decreases toward the top-right (restrictive thresholds). Together with the CSI heatmap, these reveal the trade-off surface.',
                },
                {
                  code: 'fig_TC4_S1',
                  label: 'Ranking Scatter: POD vs FAR',
                  desc: 'Scatter plot of all 81 threshold pairs in POD–FAR space, with bubble size proportional to CSI. The optimal pair is highlighted. Pairs in the upper-left quadrant (high POD, low FAR) are preferred.',
                },
                {
                  code: 'fig_TC4_S2',
                  label: 'Per-Event Hit/Miss Chart',
                  desc: 'Horizontal bar chart showing which of the 91 events are captured (green) or missed (red) at the optimal threshold pair, sorted by sector and date. Useful for identifying systematic misses by sector or season.',
                },
                {
                  code: 'fig_TC4_S3',
                  label: 'Capture Lag Distribution',
                  desc: 'Bar chart showing at which offset (D-2, D-1, D, D+1) the compound condition was first satisfied for each hit. Reveals whether the method captures events primarily via antecedent forcing or on the event day.',
                },
                {
                  code: 'fig_TC4_S4',
                  label: 'POD by Coastal Sector',
                  desc: 'POD broken down by the five SC coastal sectors (North, Central-North, Central, Central-South, South). Reveals geographic heterogeneity in detection performance — expected given the NaN coverage differences.',
                },
              ].map((fig) => (
                <div key={fig.code} className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="rounded bg-gray-200 px-2 py-0.5 text-xs font-mono text-gray-600">
                      {fig.code}
                    </span>
                    <span className="text-sm font-semibold text-gray-700">{fig.label}</span>
                  </div>
                  <p className="text-xs text-gray-500 leading-relaxed">{fig.desc}</p>
                  <div className="mt-3 h-24 rounded-lg bg-gray-200 flex items-center justify-center">
                    <span className="text-xs text-gray-400 italic">Figure pending — analysis in progress</span>
                  </div>
                </div>
              ))}
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
