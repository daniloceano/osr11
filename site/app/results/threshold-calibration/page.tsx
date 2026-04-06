import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';

export const metadata = {
  title: 'Step 2 — Threshold Calibration — OSR11',
  description:
    'Empirically calibrating compound event detection thresholds against 91 reported SC coastal disasters. Four sub-analyses: exploratory data analysis, preliminary compound analysis, tidal sensitivity (SSH vs SSH + FES2022 tide) and CSI grid scan (systematic q50–q90 optimisation).',
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
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">Full SC coast · 5 sectors · 91 events</span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">FES2022 · CSI optimisation</span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              Threshold Calibration
              <br />
              <span className="text-blue-600">Empirical Detection Framework for Compound Events</span>
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-gray-600">
              This umbrella step establishes the compound event detection thresholds used throughout
              the OSR11 pipeline. It combines four sub-analyses: exploratory data analysis (Step 2a),
              preliminary compound analysis (Step 2b), tidal sensitivity (Step 2c) introducing the
              SSH_total = SSH + FES2022 tide definition, and a systematic CSI grid scan (Step 2d) that
              identifies the optimal (Hₛ, SSH_total) threshold pair by maximising the Critical Success
              Index against the 91-event SC disaster database.
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
                  <h3 className="text-xs font-semibold text-emerald-800 mb-1.5">Optimal threshold pair (Step 2d result)</h3>
                  <div className="flex gap-4 text-xs text-emerald-700">
                    <div><span className="font-bold text-base text-emerald-900">q90</span><br />Hₛ threshold</div>
                    <div className="self-center text-emerald-400">×</div>
                    <div><span className="font-bold text-base text-emerald-900">q90</span><br />SSH_total threshold</div>
                  </div>
                  <p className="mt-2 text-xs text-emerald-600">
                    H=21, M=70, F=1 298 · POD=0.23 · FAR=0.984 · CSI=0.0151
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
                  label: 'The calibrated threshold feeds Steps 3–8.',
                  text: 'The optimal pair (q90/q90) from tab_TC4_optimal_pair.csv is passed directly to Step 3 (Storm Catalog Generation). It defines the exceedance thresholds used to identify independent compound storm episodes in the full 1993–2025 series at all coastal grid points.',
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

        {/* ── Planned analysis placeholder ──────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-14">
          <div className="mx-auto max-w-5xl px-6">
            <h2 className="mb-5 text-xl font-bold text-gray-900">Planned: False Alarm Attribution Analysis</h2>

            <div className="rounded-xl border-2 border-dashed border-gray-300 bg-gray-50 p-6">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  <StatusBadge status="planned" />
                </div>
                <div className="flex-1">
                  <h3 className="text-base font-semibold text-gray-800 mb-2">
                    Step 2e — Under-reporting investigation and false alarm reclassification
                  </h3>
                  <p className="text-sm text-gray-600 leading-relaxed mb-4">
                    The CSI grid scan labels 1 298 compound episodes as false alarms — but this
                    classification assumes the Leal et al. (2024) Civil Defense database is a
                    complete record of coastal flooding events in Santa Catarina. It is not.
                    Civil Defense reporting is voluntary, spatially uneven, and subject to
                    significant under-reporting, particularly before 2005 and in less populated
                    coastal sectors.
                  </p>
                  <p className="text-sm text-gray-600 leading-relaxed mb-4">
                    Many &ldquo;false alarms&rdquo; may in fact be real compound coastal events that
                    occurred but were not recorded. Step 2e will cross-reference the 1 298 flagged
                    episodes with:
                  </p>
                  <ul className="space-y-1.5 mb-5">
                    {[
                      'The national S2ID disaster database (broader coverage, independent source)',
                      'Atlas Digital de Desastres Naturais do Brasil (CEPED-UFSC)',
                      'Media archives and IBGE event records for coastal municipalities',
                      'Coastal tide gauge records (where available) for independent water-level validation',
                    ].map((item, i) => (
                      <li key={i} className="flex gap-2 text-xs text-gray-500">
                        <span className="text-gray-400 flex-shrink-0">—</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
                    <p className="text-xs text-amber-800 leading-relaxed">
                      <strong>Expected outcome:</strong> A fraction of the 1 298 flagged episodes
                      will be reclassified as confirmed events (reducing effective FAR), while others
                      will be confirmed spurious (pointing to physical limitations of the daily
                      compound definition). This reclassification will yield a revised CSI that
                      better reflects the true skill of the detector and may motivate adjustments to
                      the threshold pair or compound definition.
                    </p>
                  </div>
                </div>
              </div>
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
