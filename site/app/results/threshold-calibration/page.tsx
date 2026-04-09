import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';

export const metadata = {
  title: 'Step 2 — Threshold Calibration — OSR11',
  description:
    'Empirically calibrating compound event detection thresholds via five sub-analyses: exploratory data analysis, preliminary compound analysis, tidal sensitivity, CSI grid scan (diagnostic), and PU composite calibration (final). Both methods independently select q90/q90 as the optimal threshold pair.',
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
              (Step 2e, final) that independently confirms q90/q90 using an expanded events database
              and a composite score designed for under-reported impact databases.
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
                  <h3 className="text-xs font-semibold text-emerald-800 mb-1.5">Calibrated threshold pair — confirmed by Steps 2d and 2e</h3>
                  <div className="flex gap-4 text-xs text-emerald-700">
                    <div><span className="font-bold text-base text-emerald-900">q90</span><br />Hₛ threshold</div>
                    <div className="self-center text-emerald-400">×</div>
                    <div><span className="font-bold text-base text-emerald-900">q90</span><br />SSH_total threshold</div>
                  </div>
                  <p className="mt-2 text-xs text-emerald-600">
                    Step 2d (CSI): H=21, M=70, F=1 298, CSI=0.0151<br />
                    Step 2e (PU): H=15, M=41, U=1 267, R_pos=0.268
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
                  label: 'The optimal threshold is q90/q90 — but the skill is low.',
                  text: 'The CSI grid scan finds that the highest CSI across all 81 pairs occurs at the most restrictive combination tested: Hₛ=q90, SSH_total=q90 (CSI=0.0151, POD=0.23, FAR=0.984). No combination in the q50–q90 range achieves a meaningful trade-off between sensitivity and specificity. Compound daily exceedances are ~62× more frequent than reported disaster events.',
                },
                {
                  label: 'The high false alarm rate is structural, not a calibration failure.',
                  text: 'Even at q90/q90, 1 298 compound episodes are flagged with no matching reported event. This likely reflects the incompleteness of the Civil Defense database (under-reporting, missing dates, spatially patchy coverage) rather than spurious oceanic detections. The ocean signal is real; it is the observational record that is sparse. This distinction is critical for interpreting subsequent steps.',
                },
                {
                  label: 'Step 2e independently confirms q90/q90 — two methods, two databases, same answer.',
                  text: 'The PU composite calibration (Step 2e) performs an independent threshold sweep using the expanded documentary events database (56 events, 1998–2020) and a composite score that treats unmatched detections as unlabeled rather than as false alarms. It also selects q90/q90, confirming the CSI result from Step 2d. The calibrated threshold pair from tab_TC5_optimal_pair_pu.csv is passed to Step 3 (Storm Catalog Generation).',
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
              <p className="text-xs text-gray-500 mb-3">Expanded database · 56 events · 1998–2020 · PU composite score · 14 municipalities</p>
              <p className="text-sm text-gray-600 leading-relaxed mb-4 flex-1">
                Independent threshold sweep using a positive-unlabeled (PU) composite score
                designed for under-reported impact databases. Unmatched compound detections are
                treated as unlabeled examples rather than false alarms, with each episode receiving
                a confidence weight qᵢ based on external evidence, physical intensity, and
                contextual coherence. Confirms q90/q90 as the optimal pair — robust across all
                weight, alpha, and B_target sensitivity experiments.
              </p>
              <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 mb-4 text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div><span className="text-gray-500">Optimal pair</span><br /><span className="font-bold text-gray-800">q90 / q90</span></div>
                  <div><span className="text-gray-500">Recall (R_pos)</span><br /><span className="font-bold text-gray-800">0.268 — H=15 / P=56</span></div>
                  <div><span className="text-gray-500">Unmatched episodes</span><br /><span className="font-bold text-gray-800">1 267</span></div>
                  <div><span className="text-gray-500">Convergence with 2d</span><br /><span className="font-bold text-emerald-700">✓ q90/q90 confirmed</span></div>
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
