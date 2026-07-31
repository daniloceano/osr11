import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';

export const metadata = {
  title: 'Step 2 — Threshold Calibration — OSR11',
  description:
    'Empirically calibrating compound event detection thresholds via five sub-analyses: exploratory data analysis, preliminary compound analysis, tidal sensitivity, CSI grid scan (diagnostic), and PU composite calibration (final). The final calibration, redone on 2026-07-30 over a 121-pair grid, selects q70/q99.',
};

export default function ThresholdCalibrationHubPage() {
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
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Step 2</span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Full SC coast · 5 sectors · 5 sub-analyses</span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">FES2022 · CSI · PU composite calibration</span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              Threshold Calibration
              <br />
              <span className="text-blue-600">Empirical Detection Framework for Compound Events</span>
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-gray-600">
              This umbrella step establishes the compound event detection thresholds used throughout
              the OSR11 pipeline. Five sub-analyses: exploratory data analysis (Step 2a), preliminary
              compound analysis (Step 2b), tidal sensitivity (Step 2c) introducing SSH_total = SSH +
              FES2022 tide, a CSI grid scan (Step 2d, diagnostic), and a PU composite calibration
              (Step 2e, final) using an expanded events database and a composite score designed for
              under-reported impact databases. Steps 2a–2d are preserved as the historical record of
              a method built on SSH_total; Step 2e was recalibrated on 2026-07-30 to score the
              production detector, and selects <strong>q70/q99</strong>.
            </p>
          </div>
        </div>

        {/* ── Scientific context ────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-4 text-xl font-bold text-gray-900">The Calibration Problem</h2>
            <div className="grid gap-6 md:grid-cols-2">
              <p className="text-sm text-gray-700 leading-relaxed">
                Before this step, compound event detection used a conventional
                q90 threshold for both Hₛ and SSH — a reasonable but arbitrary starting point.
                Step 2 asks two specific questions:
                <br /><br />
                <strong>(1) Tidal contribution.</strong> GLORYS12 SSH (zos) does not include
                astronomical tides. Should the FES2022 tide be added to form a total sea level
                (SSH_total), and if so, how does it change detection at the same q90 threshold?
                <br /><br />
                <strong>(2) Optimal threshold.</strong> Given SSH_total as the sea-level variable,
                which combination of (Hₛ, SSH_total) thresholds in the q50–q90 range best
                discriminates the 91 reported SC disasters from background ocean conditions?
                <br /><br />
                <strong>Both questions were later reopened.</strong> Audit AUD-01 established that a
                threshold applied to SSH_total selects on tidal phase rather than on storm forcing, so
                the detector was rebuilt on tide-free zos with an explicit HAT gate. Step 2e was then
                recalibrated on that detector, over a grid extended past q90. Steps 2a–2d below are
                retained unchanged as the record of the earlier method; they have <em>not</em> been
                re-run, and their q90/q90 result is no longer the calibrated pair.
              </p>
              <div className="space-y-3">
                <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
                  <h3 className="text-xs font-semibold text-blue-800 mb-1.5">SSH_total definition (canonical)</h3>
                  <code className="text-xs text-blue-700 font-mono leading-relaxed">
                    SSH_total = zos (GLORYS12, 00:00 UTC)<br />
                    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+ FES2022 tide (daily maximum)
                  </code>
                  <p className="mt-2 text-xs text-blue-600">
                    FES2022 evaluated at hourly resolution; daily max retained for consistency with
                    the Hₛ daily-maximum convention (WAVERYS 3-hourly → daily max).
                  </p>
                </div>
                <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
                  <h3 className="text-xs font-semibold text-emerald-800 mb-1.5">Calibrated threshold pair — Step 2e, 2026-07-30</h3>
                  <div className="flex gap-4 text-xs text-emerald-700">
                    <div><span className="font-bold text-base text-emerald-900">q70</span><br />Hₛ threshold</div>
                    <div className="self-center text-emerald-400">×</div>
                    <div><span className="font-bold text-base text-emerald-900">q99</span><br />tide-free zos threshold</div>
                  </div>
                  <p className="mt-2 text-xs text-emerald-600">
                    Step 2e (PU): H=28, M=119, U=831, R_pos=0.191, Score=−0.318<br />
                    Superseded: q90/q90 (Step 2d CSI, and Step 2e before recalibration)
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Sub-step cards ────────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-6 text-xl font-bold text-gray-900">Sub-analyses</h2>
            <div className="grid gap-6 md:grid-cols-2">

              {/* Sub-step 2a — Exploratory Data Analysis */}
              <div className="rounded-xl border-2 border-gray-200 bg-white p-6 flex flex-col">
                <div className="flex items-center gap-2 mb-3">
                  <StatusBadge status="done" />
                  <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Step 2a</span>
                </div>
                <h3 className="text-base font-bold text-gray-900 mb-1">Exploratory Data Analysis</h3>
                <p className="text-xs text-gray-500 mb-3">South SC test domain · spatial maps · time series · statistics</p>
                <p className="text-sm text-gray-600 leading-relaxed mb-4 flex-1">
                  First-look inspection of WAVERYS and GLORYS12 spatial distributions, temporal variability,
                  and the events database. Coastal grid-point selection and municipality–grid association.
                  Per-sector boxplots, seasonal cycles, and compound quick-look at empirical q90.
                </p>
                <Link
                  href="/results/south-sc"
                  className="flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm font-medium text-blue-700 hover:bg-blue-100 transition-colors"
                >
                  View exploratory analysis
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              </div>

              {/* Sub-step 2b — Preliminary Compound Analysis */}
              <div className="rounded-xl border-2 border-gray-200 bg-white p-6 flex flex-col">
                <div className="flex items-center gap-2 mb-3">
                  <StatusBadge status="done" />
                  <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Step 2b</span>
                </div>
                <h3 className="text-base font-bold text-gray-900 mb-1">Preliminary Compound Analysis</h3>
                <p className="text-xs text-gray-500 mb-3">Full SC coast · 5 sectors · 91 events · q90 baseline</p>
                <p className="text-sm text-gray-600 leading-relaxed mb-4 flex-1">
                  First-pass inspection of joint Hₛ and SSH exceedances at q90 during each of the 91
                  reported coastal disasters. Per-event ±3-day windows; MagicA peaks-over-threshold;
                  concomitance metrics. 22 of 91 events show concurrent SSH-only exceedances at q90.
                </p>
                <Link
                  href="/results/preliminary-compound"
                  className="flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm font-medium text-blue-700 hover:bg-blue-100 transition-colors"
                >
                  View preliminary analysis
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              </div>

              {/* Sub-step 2c — Tidal Sensitivity */}
              <div className="rounded-xl border-2 border-gray-200 bg-white p-6 flex flex-col">
                <div className="flex items-center gap-2 mb-3">
                  <StatusBadge status="done" />
                  <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Step 2c</span>
                </div>
                <h3 className="text-base font-bold text-gray-900 mb-1">Tidal Sensitivity Analysis</h3>
                <p className="text-xs text-gray-500 mb-3">SSH vs SSH + FES2022 · Daily max tide · 91 events</p>
                <p className="text-sm text-gray-600 leading-relaxed mb-4 flex-1">
                  Introduces the SSH_total = SSH + FES2022 tide variable and tests whether adding the
                  FES2022 daily-maximum tide to the GLORYS12 SSH changes compound event detection at q90.
                  The daily-max convention (hourly FES2022 → daily max) is consistent with Hₛ and
                  maximises tidal contribution relative to a midnight snapshot.
                </p>
                <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 mb-4 text-xs">
                  <div className="grid grid-cols-2 gap-2">
                    <div><span className="text-gray-500">SSH-only detections</span><br /><span className="font-bold text-gray-800">22 of 91</span></div>
                    <div><span className="text-gray-500">With tide (SSH_total)</span><br /><span className="font-bold text-gray-800">26 of 91</span></div>
                    <div><span className="text-gray-500">New detections</span><br /><span className="font-bold text-green-700">+7</span></div>
                    <div><span className="text-gray-500">Lost detections</span><br /><span className="font-bold text-red-700">−3</span></div>
                  </div>
                </div>
                <Link
                  href="/results/threshold-calibration/tidal-sensitivity"
                  className="flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm font-medium text-blue-700 hover:bg-blue-100 transition-colors"
                >
                  View tidal sensitivity analysis
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              </div>

              {/* Sub-step 2d — CSI Grid Scan */}
              <div className="rounded-xl border-2 border-gray-200 bg-white p-6 flex flex-col">
                <div className="flex items-center gap-2 mb-3">
                  <StatusBadge status="done" />
                  <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Step 2d</span>
                </div>
                <h3 className="text-base font-bold text-gray-900 mb-1">CSI Grid Scan</h3>
                <p className="text-xs text-gray-500 mb-3">q50–q90 × q50–q90 · 81 threshold pairs · causal window [D-2, D+1]</p>
                <p className="text-sm text-gray-600 leading-relaxed mb-4 flex-1">
                  Systematic sweep of 81 (Hₛ, SSH_total) threshold combinations, evaluating hits, misses,
                  and false alarms against the 91 reported disasters using an asymmetric causal/antecedent
                  matching window. Selects the pair maximising CSI. The high FAR at all thresholds (near 1)
                  is a structural result at daily resolution, not a method failure.
                </p>
                <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 mb-4 text-xs">
                  <div className="grid grid-cols-2 gap-2">
                    <div><span className="text-gray-500">Optimal pair</span><br /><span className="font-bold text-gray-800">q90 / q90</span></div>
                    <div><span className="text-gray-500">Hits / Misses</span><br /><span className="font-bold text-gray-800">21 / 70</span></div>
                    <div><span className="text-gray-500">False alarms</span><br /><span className="font-bold text-gray-800">1 298</span></div>
                    <div><span className="text-gray-500">CSI</span><br /><span className="font-bold text-gray-800">0.0151</span></div>
                  </div>
                </div>
                <Link
                  href="/results/threshold-calibration/csi-scan"
                  className="flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm font-medium text-blue-700 hover:bg-blue-100 transition-colors"
                >
                  View CSI grid scan
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* ── Key takeaways ─────────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-gray-50 py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-5 text-xl font-bold text-gray-900">What the calibration tells us</h2>
            <div className="space-y-3">
              {[
                {
                  label: 'Tide increases detection — but only modestly.',
                  text: 'Adding the FES2022 daily-maximum tide to SSH raises the concurrent detection count from 22 to 26 of 91 events (net +4). The positive mean tidal contribution (~+0.53 m) shifts SSH_total above SSH for most events, enabling 7 new detections. But the q90 threshold also shifts upward with the distribution, partially cancelling the effect. The SSH_total definition established in Step 2c is carried unchanged into Step 2d.',
                },
                {
                  label: 'Step 2d selects q90/q90 — at the edge of its grid, and with low skill.',
                  text: 'The CSI grid scan finds that the highest CSI across all 81 pairs occurs at the most restrictive combination tested: Hₛ=q90, SSH_total=q90 (CSI=0.0151, POD=0.23, FAR=0.984). No combination in the q50–q90 range achieves a meaningful trade-off between sensitivity and specificity. That the optimum sits on the boundary of the scanned range is itself a warning, and it was later confirmed to be one: the sweep simply never tested anything more restrictive.',
                },
                {
                  label: 'The high false alarm rate is structural, not a calibration failure.',
                  text: 'Even at q90/q90, 1 298 compound episodes are flagged with no matching reported event. This likely reflects the incompleteness of the Civil Defense database (under-reporting, missing dates, spatially patchy coverage) rather than spurious oceanic detections. The ocean signal is real; it is the observational record that is sparse. This distinction is critical for interpreting subsequent steps.',
                },
                {
                  label: 'The apparent agreement between 2d and 2e did not survive scrutiny.',
                  text: 'Step 2e originally also selected q90/q90, and that was read as two methods on two databases reaching the same answer. It was not independent corroboration: both sweeps stopped at q90, and both scored a detector built on SSH_total. Recalibrating Step 2e on the production detector over a grid extended to q95 and q99 moved its answer to q70/q99 and revealed that the old composite score had no interior optimum at all — Spearman(Score, accepted episodes) = −0.999, meaning it rewarded detecting less, without limit. Step 2d has not been re-run and remains a diagnostic record. The calibrated pair passed to Step 3 comes from tab_TC5_optimal_pair_pu.csv.',
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

        {/* ── Sub-step 2e card ──────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <div className="rounded-xl border-2 border-emerald-200 bg-white p-6 flex flex-col">
              <div className="flex items-center gap-2 mb-3">
                <StatusBadge status="done" />
                <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Step 2e · Final calibration</span>
              </div>
              <h3 className="text-base font-bold text-gray-900 mb-1">PU Composite Calibration</h3>
              <p className="text-xs text-gray-500 mb-3">Combined database · 147 events · 27 municipalities · 1998–2020 · PU composite score · 121 pairs</p>
              <p className="text-sm text-gray-600 leading-relaxed mb-4 flex-1">
                Threshold sweep using a positive-unlabeled (PU) composite score designed for
                under-reported impact databases. Unmatched compound detections are treated as
                unlabeled examples rather than false alarms, with each episode receiving a
                confidence weight qᵢ based on external evidence, physical intensity, and contextual
                coherence. Recalibrated on 2026-07-30 to score the production detector over a grid
                extended to q95 and q99: the selected pair is <strong>q70/q99</strong>, which matches
                the recall of the superseded q90/q90 with 62 % fewer unmatched detections.
              </p>
              <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 mb-4 text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div><span className="text-gray-500">Selected pair</span><br /><span className="font-bold text-gray-800">q70 / q99</span></div>
                  <div><span className="text-gray-500">Recall (R_pos)</span><br /><span className="font-bold text-gray-800">0.191 — H=28 / P=147</span></div>
                  <div><span className="text-gray-500">Unmatched episodes</span><br /><span className="font-bold text-gray-800">831 (against 2 214 at q90/q90)</span></div>
                  <div><span className="text-gray-500">Level percentile</span><br /><span className="font-bold text-emerald-700">q99 in 14 of 14 variants</span></div>
                </div>
              </div>
              <Link
                href="/results/threshold-calibration/pu-calibration"
                className="flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm font-medium text-blue-700 hover:bg-blue-100 transition-colors"
              >
                View PU composite calibration
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          </div>
        </div>

        {/* ── Navigation ────────────────────────────────────────────────────── */}
        <div className="bg-white py-12">
          <div className="mx-auto max-w-5xl px-6 flex items-center justify-between">
            <Link
              href="/results/preliminary-compound"
              className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Preliminary Compound Analysis
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
