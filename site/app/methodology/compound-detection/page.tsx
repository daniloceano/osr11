import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';

export const metadata = {
  title: 'Compound Event Detection — Step 3 Methodology | OSR11',
  description:
    'Article-standard, auditable description of how compound coastal events are detected and catalogued along the Brazilian coast: storm-episode definition, temporal-overlap rule, and every metric computed for each compound event (intensity, overlap duration, peak lag), with formulas and assumptions.',
};

/* ───────────────────────── small helpers ───────────────────────── */

function Chevron() {
  return (
    <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  );
}

function Eq({ children }: { children: React.ReactNode }) {
  return (
    <div className="my-3 overflow-x-auto rounded-lg border border-gray-200 bg-gray-900 px-4 py-3">
      <code
        className="block whitespace-pre text-xs leading-relaxed text-gray-100 md:text-sm"
        style={{ background: 'transparent', padding: 0, borderRadius: 0 }}
      >
        {children}
      </code>
    </div>
  );
}

function Section({
  id,
  eyebrow,
  title,
  children,
  tint = 'white',
}: {
  id?: string;
  eyebrow?: string;
  title: string;
  children: React.ReactNode;
  tint?: 'white' | 'gray';
}) {
  return (
    <section id={id} className={`border-b border-gray-200 py-14 ${tint === 'gray' ? 'bg-gray-50' : 'bg-white'}`}>
      <div className="mx-auto max-w-5xl px-6">
        {eyebrow && (
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-blue-600">{eyebrow}</p>
        )}
        <h2 className="mb-5 text-2xl font-bold text-gray-900">{title}</h2>
        {children}
      </div>
    </section>
  );
}

/* ───────────────────────── metric tables ───────────────────────── */

const stormAttributes: { field: string; definition: string; formula: string; units: string }[] = [
  {
    field: 'date_start / date_end',
    definition: 'First and last calendar day of the storm episode (a maximal run of exceedance days, gap ≤ 1 day).',
    formula: 'min / max of episode dates',
    units: 'date (YYYY-MM-DD)',
  },
  {
    field: 'duration_days',
    definition: 'Number of calendar days spanned by the episode, including the ≤ 1-day internal gaps that were bridged.',
    formula: 'len(episode_dates)',
    units: 'days',
  },
  {
    field: 'peak_value',
    definition: 'Maximum value of the variable (Hₛ or SSH_total) reached within the episode.',
    formula: 'max(values over episode days)',
    units: 'm',
  },
  {
    field: 'peak_date',
    definition: 'Calendar day on which the peak value occurs (argmax of the episode values).',
    formula: 'argmax(values over episode days)',
    units: 'date',
  },
  {
    field: 'integrated_intensity',
    definition: 'Cumulative magnitude above the threshold across the episode — a discrete area-over-threshold ("storm energy" proxy).',
    formula: 'Σ max(value − threshold, 0)',
    units: 'm·day',
  },
];

const compoundAttributes: { field: string; definition: string; formula: string; units: string }[] = [
  {
    field: 'date_start / date_end',
    definition: 'Bounds of the overlap window — the calendar days shared by the Hₛ and SSH_total episodes in the group. Falls back to the union bounds only if the overlap set is empty (not reachable under the ≥ 1-day rule).',
    formula: 'min / max of (Hₛ_days ∩ SSH_days)',
    units: 'date',
  },
  {
    field: 'overlap_duration_days',
    definition: 'Number of calendar days on which both an Hₛ storm and an SSH_total storm are simultaneously active — the core measure of joint persistence.',
    formula: '|Hₛ_days ∩ SSH_days|',
    units: 'days',
  },
  {
    field: 'union_duration_days',
    definition: 'Total footprint of the compound event: any day on which either driver is active.',
    formula: '|Hₛ_days ∪ SSH_days|',
    units: 'days',
  },
  {
    field: 'n_hs_storms / n_ssh_storms',
    definition: 'How many individual Hₛ and SSH_total episodes were merged into this compound event (≥ 1 each; > 1 when several episodes chain through shared days).',
    formula: 'group cardinality',
    units: 'count',
  },
  {
    field: 'peak_hs / peak_ssh_total',
    definition: 'Largest peak value reached by any Hₛ / SSH_total episode in the group.',
    formula: 'max over grouped episodes',
    units: 'm',
  },
  {
    field: 'peak_hs_date / peak_ssh_date',
    definition: 'Dates of the governing Hₛ and SSH_total peaks (the peaks that define peak_hs and peak_ssh_total).',
    formula: 'argmax over grouped episodes',
    units: 'date',
  },
  {
    field: 'peak_lag_days',
    definition: 'Lead/lag between the wave peak and the surge peak. Sign convention: positive ⇒ Hₛ peaks before SSH_total. Diagnoses the temporal structure of the compound forcing.',
    formula: 'date(peak_hs) − date(peak_ssh_total)',
    units: 'days (signed)',
  },
  {
    field: 'hs_integrated_intensity / ssh_integrated_intensity',
    definition: 'Sum of the integrated intensities of the contributing Hₛ / SSH_total episodes.',
    formula: 'Σ integrated_intensity of grouped episodes',
    units: 'm·day',
  },
];

const gridMetrics: { field: string; definition: string; formula: string }[] = [
  {
    field: 'compound_count_total',
    definition: 'Total number of compound events detected at the grid point over 1993–2025.',
    formula: 'n compound events',
  },
  {
    field: 'compound_count_annual_mean',
    definition: 'Mean annual frequency of compound events — the primary hazard-frequency metric carried into the risk integration (Step 4).',
    formula: 'compound_count_total / n_years',
  },
  {
    field: 'mean / p95 / max overlap_duration',
    definition: 'Distribution of joint persistence (overlap days) across the grid point’s compound events.',
    formula: 'mean, 95th pct, max of overlap_duration_days',
  },
  {
    field: 'mean_peak_lag_days',
    definition: 'Average wave–surge peak lag, averaged over events with a defined lag.',
    formula: 'mean(peak_lag_days)',
  },
  {
    field: 'mean / p95 / max compound_intensity_norm',
    definition: 'Distribution of normalized compound intensity (see §6) across the grid point’s events — feeds the Hazard_Index.',
    formula: 'mean, 95th pct, max of compound_intensity_norm',
  },
];

/* ───────────────────────── page ───────────────────────── */

export default function CompoundDetectionPage() {
  return (
    <>
      <Navigation />
      <main className="pt-16">
        {/* ── Header ─────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-16">
          <div className="mx-auto max-w-5xl px-6">
            <div className="mb-4 flex items-center gap-2 text-xs text-gray-500">
              <Link href="/" className="transition-colors hover:text-gray-700">Overview</Link>
              <Chevron />
              <Link href="/methodology" className="transition-colors hover:text-gray-700">Methodology</Link>
              <Chevron />
              <span className="text-gray-600">Compound Event Detection</span>
            </div>

            <div className="mb-4 flex flex-wrap items-start gap-2">
              <StatusBadge status="done" />
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                Step 3 — Hazard Characterization
              </span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                808 grid points · 1993–2025
              </span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                Auditable specification
              </span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              Compound Event Detection
              <br />
              <span className="text-blue-600">How wave–surge events are catalogued and measured</span>
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-gray-600">
              This page is the article-standard specification of Step 3: how compound coastal events are
              identified from the metocean record and every metric computed for them, with explicit
              formulas, units, and assumptions. It is written for human audit — each definition maps
              one-to-one onto the production code referenced in §7.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              {[
                { label: 'Drivers', value: 'Hₛ (WAVERYS) and SSH_total = GLORYS12 zos + FES2022 tide (daily max)' },
                { label: 'Threshold', value: 'q90 / q90 — local, from the full 1993–2025 climatology (Step 2e)' },
                { label: 'Episode gap', value: '≤ 1 non-exceedance day bridges an episode' },
                { label: 'Compound rule', value: 'Hₛ and SSH_total episodes overlap by ≥ 1 calendar day' },
                { label: 'Grouping', value: 'Union-find on shared days (chains episodes into one event)' },
                { label: 'Scale', value: '~404k Hₛ + ~325k SSH_total storms → ~96k compound events' },
              ].map((m) => (
                <div key={m.label} className="rounded-lg border border-gray-300/60 bg-gray-50 px-3 py-2">
                  <div className="text-xs text-gray-500">{m.label}</div>
                  <div className="max-w-xs text-xs font-medium text-gray-800">{m.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── 0. Two-stage framing ───────────────────────────────── */}
        <Section eyebrow="Orientation" title="Calibration and detection are two distinct stages" tint="gray">
          <p className="mb-4 text-sm leading-relaxed text-gray-700">
            A recurring source of confusion is the difference between how thresholds were
            <em> chosen</em> and how compound events are <em>defined</em>. They are separate stages with
            separate rules:
          </p>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
              <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-amber-700">
                Step 2 — Calibration (threshold selection)
              </p>
              <p className="text-sm leading-relaxed text-gray-700">
                Candidate thresholds are scored by matching joint exceedances to reported coastal
                disasters within an asymmetric <strong>causal/antecedent window</strong>{' '}
                <code className="rounded bg-white px-1 text-xs">[D-2, D-1, D, D+1 00Z]</code>.
                This window is a <em>matching tolerance</em> between model and disaster records — it is
                <strong> not</strong> part of the compound-event definition. Outcome: Hₛ=q90, SSH_total=q90.
              </p>
            </div>
            <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
              <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-emerald-700">
                Step 3 — Detection (this page)
              </p>
              <p className="text-sm leading-relaxed text-gray-700">
                The calibrated thresholds are applied to the full 1993–2025 record. Compound events are
                defined purely by <strong>temporal overlap of storm episodes</strong> (≥ 1 shared calendar
                day) at each grid point. No disaster database and no causal window enter here — this is an
                unsupervised characterization of the metocean record.
              </p>
            </div>
          </div>
        </Section>

        {/* ── 1. Stage A: storm catalogs ─────────────────────────── */}
        <Section eyebrow="Stage A · Step 3.1" title="Building the single-variable storm catalogs">
          <p className="mb-3 text-sm leading-relaxed text-gray-700">
            Hₛ and SSH_total are catalogued <strong>independently</strong> at every coastal grid point. A
            "storm" is a peaks-over-threshold (POT) episode built in three deterministic steps.
          </p>

          <ol className="space-y-4 text-sm text-gray-700">
            <li>
              <p className="font-semibold text-gray-900">1. Local threshold (q90)</p>
              <p className="leading-relaxed">
                For each grid point and variable, the threshold is the 90th percentile of the entire
                daily series (1993–2025). Thresholds are <strong>local</strong> (computed per grid point),
                so an episode reflects conditions extreme <em>for that location</em>, not a coast-wide
                absolute level. The percentile (q90) is inherited unchanged from the Step 2e calibration.
              </p>
              <Eq>{`thr = quantile(series_daily, 0.90)   # per grid point, per variable`}</Eq>
            </li>
            <li>
              <p className="font-semibold text-gray-900">2. Exceedance mask</p>
              <p className="leading-relaxed">
                A boolean daily mask marks days at or above the threshold. Missing days (NaN) are treated
                as non-exceedances (never spurious storms).
              </p>
              <Eq>{`mask[d] = (value[d] >= thr)   # NaN -> False`}</Eq>
            </li>
            <li>
              <p className="font-semibold text-gray-900">3. Episode clustering (gap-tolerant)</p>
              <p className="leading-relaxed">
                Consecutive exceedance days are merged into one episode. Two exceedance days belong to the
                same episode if separated by at most <strong>one</strong> non-exceedance day
                (<code className="rounded bg-gray-100 px-1 text-xs">EPISODE_MAX_GAP_DAYS = 1</code>). This
                bridges the brief sub-threshold dips that would otherwise fragment a single physical storm.
                The same rule was used in the Step 2e calibration, so catalog statistics are consistent
                with the threshold selection.
              </p>
              <Eq>{`same episode  ⇔  (day_i − day_{i-1}) ≤ EPISODE_MAX_GAP_DAYS + 1`}</Eq>
            </li>
          </ol>

          <p className="mt-5 mb-2 text-sm font-semibold text-gray-900">Attributes stored per storm episode</p>
          <MetricTable rows={stormAttributes} cols={['Field', 'Definition', 'Formula', 'Units']} />
        </Section>

        {/* ── 2. Stage B: compound detection ─────────────────────── */}
        <Section eyebrow="Stage B · Step 3.2" title="Detecting compound events: the overlap rule" tint="gray">
          <p className="mb-3 text-sm leading-relaxed text-gray-700">
            At each grid point, the Hₛ and SSH_total catalogs are compared day-by-day. A compound event is
            a group of Hₛ and SSH_total episodes connected through shared calendar days.
          </p>
          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <p className="mb-2 text-sm font-semibold text-gray-900">Definition</p>
            <p className="text-sm leading-relaxed text-gray-700">
              A compound event exists when an Hₛ episode and an SSH_total episode share{' '}
              <strong>at least one calendar day</strong>. If several episodes chain together (e.g. one long
              SSH_total storm overlapping two separate Hₛ storms), they are merged into a single compound
              event by <strong>union-find</strong> grouping on the shared days. Episodes with no overlap
              are classified as <code className="rounded bg-gray-100 px-1 text-xs">Hs_only</code> or{' '}
              <code className="rounded bg-gray-100 px-1 text-xs">SSH_total_only</code>.
            </p>
            <Eq>{`compound  ⇔  (Hₛ_days ∩ SSH_total_days) ≠ ∅      (≥ 1 shared calendar day)

union-find:  episodes sharing any day collapse into one compound event
classes:     { Hs_only , SSH_total_only , compound }`}</Eq>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <MiniCard title="Why temporal overlap?" body="At the regional scale, wave generation and surge are driven by the same synoptic systems; co-occurrence in time is the operational signature of a compound driver (Zscheischler et al. 2020)." />
            <MiniCard title="Why union-find?" body="It guarantees a clean partition: each storm belongs to exactly one compound event, and chained overlaps are not double-counted." />
            <MiniCard title="Daily resolution" body="Both datasets are daily, so overlap is resolved to the calendar day. Sub-daily lead/lag within a day cannot be distinguished (see §8)." />
          </div>

          <p className="mt-6 mb-2 text-sm font-semibold text-gray-900">Attributes computed per compound event</p>
          <MetricTable rows={compoundAttributes} cols={['Field', 'Definition', 'Formula', 'Units']} />
        </Section>

        {/* ── 3. Per-grid-point summary ──────────────────────────── */}
        <Section eyebrow="Aggregation" title="Per-grid-point summary metrics">
          <p className="mb-4 text-sm leading-relaxed text-gray-700">
            The individual compound events at a grid point are summarized into the metrics that populate
            the interactive hazard maps and feed the municipal risk integration (Step 4). Empty grid points
            (no compound events) carry explicit nulls rather than zeros for distributional fields.
          </p>
          <MetricTable rows={gridMetrics} cols={['Metric', 'Definition', 'Formula']} />
        </Section>

        {/* ── 4. Intensity normalization ─────────────────────────── */}
        <Section eyebrow="Key metric" title="Normalized compound intensity — definition and assumptions" tint="gray">
          <p className="mb-3 text-sm leading-relaxed text-gray-700">
            Compound intensity must combine two variables on different physical scales (wave height in
            metres vs. total sea level in metres, but with very different dynamic ranges). Each driver is
            therefore rescaled to a common [0, 1] range using <strong>domain-wide</strong> reference
            quantiles, then averaged with equal weight.
          </p>
          <Eq>{`# Domain-wide references (over ALL compound-event peaks, all grid points)
Hₛ_low  = Q05(all peak_hs)        Hₛ_high  = Q95(all peak_hs)
SSH_low = Q05(all peak_ssh_total) SSH_high = Q95(all peak_ssh_total)

# Per-event normalization (clipped to [0, 1])
hs_norm  = clip( (peak_hs        − Hₛ_low ) / (Hₛ_high  − Hₛ_low ), 0, 1)
ssh_norm = clip( (peak_ssh_total − SSH_low) / (SSH_high − SSH_low), 0, 1)

compound_intensity_norm = 0.5 · (hs_norm + ssh_norm)`}</Eq>

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-gray-200 bg-white p-4">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">Assumptions</p>
              <ul className="list-disc space-y-1.5 pl-5 text-sm text-gray-700">
                <li><strong>Equal weighting (0.5 / 0.5):</strong> wave and surge are treated as equally important contributors to compound severity, absent site-specific impact weights.</li>
                <li><strong>Q05–Q95 references:</strong> the 5th–95th percentiles of observed compound peaks define the dynamic range, making intensity robust to a handful of outliers at either tail.</li>
                <li><strong>Domain-wide (not local) scaling:</strong> a single reference range is used across the whole coast so that intensity is comparable between grid points and municipalities.</li>
                <li><strong>Clipping to [0, 1]:</strong> peaks beyond Q05/Q95 saturate at 0 or 1, so intensity is a bounded, interpretable severity score.</li>
              </ul>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white p-4">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">Interpretation</p>
              <p className="text-sm leading-relaxed text-gray-700">
                A value near <strong>1.0</strong> means both drivers peaked near the upper end of their
                coast-wide observed range during the event; near <strong>0.0</strong> means both were only
                marginally above threshold. Because scaling is domain-wide, a high value at one
                municipality is directly comparable to a high value at another — which is what makes the
                metric usable inside the cross-municipal Hazard_Index.
              </p>
            </div>
          </div>
        </Section>

        {/* ── 5. Downstream dependence note ──────────────────────── */}
        <Section eyebrow="Downstream use" title="From compound events to dependence structure">
          <p className="text-sm leading-relaxed text-gray-700">
            The <code className="rounded bg-gray-100 px-1 text-xs">(peak_hs, peak_ssh_total)</code> pairs of
            the compound events are the sample for the wave–surge dependence analysis (Step 3.7): Kendall’s
            τ and Spearman’s ρ (rank correlation) and the extremal coefficients χ and χ̄ (joint-tail
            association). Stable estimation requires a minimum of <strong>20 compound events</strong> per
            grid point for χ/χ̄ and <strong>5 pairs</strong> for τ/ρ; points below these counts return
            nulls with metadata. This keeps the dependence portrait consistent with the compound-event
            definition above — only genuinely co-occurring extremes contribute.
          </p>
        </Section>

        {/* ── 6. Assumptions & limitations ───────────────────────── */}
        <Section eyebrow="For the auditor" title="Assumptions and limitations" tint="gray">
          <div className="grid gap-4 md:grid-cols-2">
            <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-gray-700">
              <li><strong>Daily temporal resolution.</strong> Co-occurrence is resolved to the calendar day; sub-daily phasing of wave and surge peaks within a day is not resolvable, and peak_lag_days is therefore an integer-day quantity.</li>
              <li><strong>Local q90 thresholds.</strong> "Extreme" is relative to each grid point’s own climatology, not an absolute hazard level; comparisons across points are about <em>relative</em> exceedance.</li>
              <li><strong>SSH_total construction.</strong> Total sea level is GLORYS12 zos at 00:00 UTC plus the FES2022 daily-maximum astronomical tide — it does not include wave setup or river/runoff contributions.</li>
            </ul>
            <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-gray-700">
              <li><strong>Gap tolerance.</strong> The 1-day episode gap and the ≥ 1-day overlap rule are deliberate, calibration-consistent choices; sensitivity to the gap was checked in Step 2e and found stable at q90/q90.</li>
              <li><strong>Equal-weight intensity.</strong> The 0.5/0.5 wave–surge weighting is a modelling assumption, not an impact-calibrated weight; site-specific damage functions could re-weight it.</li>
              <li><strong>Reanalysis basis.</strong> Catalogs inherit any biases of WAVERYS, GLORYS12, and FES2022; they characterize the reanalysed ocean, not in-situ observations.</li>
            </ul>
          </div>
        </Section>

        {/* ── 7. Provenance / reproducibility ────────────────────── */}
        <Section eyebrow="Reproducibility" title="Code provenance — every rule maps to a script">
          <p className="mb-4 text-sm leading-relaxed text-gray-700">
            The definitions on this page are not prose approximations; each maps to a specific function in
            the production pipeline (<code className="rounded bg-gray-100 px-1 text-xs">src/03_storm_catalog_generation/</code>).
          </p>
          <div className="overflow-x-auto rounded-xl border border-gray-200">
            <table className="w-full border-collapse text-left text-xs">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  <th className="border-b border-gray-200 px-3 py-2 font-semibold">Rule on this page</th>
                  <th className="border-b border-gray-200 px-3 py-2 font-semibold">Source</th>
                </tr>
              </thead>
              <tbody className="text-gray-700">
                {[
                  ['Local q90 threshold + exceedance mask + episode clustering (gap ≤ 1)', '01_storm_catalogs/segmentation.py'],
                  ['Per-storm attributes (peak, duration, integrated intensity)', '01_storm_catalogs/metrics.py'],
                  ['Overlap rule, union-find grouping, compound attributes, intensity normalization', '02_compound_detection/detection.py'],
                  ['EPISODE_MAX_GAP_DAYS = 1; threshold source (Step 2e); SSH_total definition', 'config/analysis_config.py'],
                  ['Per-grid-point persistence aggregation', '03_duration_persistence/persistence.py'],
                  ['Wave–surge dependence (τ, ρ, χ, χ̄) from compound pairs', '07_dependence/dependence.py'],
                  ['Calibration matching window [D-2…D+1 00Z] (Step 2 only)', '02_threshold_calibration/04_csi_grid_scan/windows.py'],
                ].map(([rule, src]) => (
                  <tr key={src} className="odd:bg-white even:bg-gray-50/50">
                    <td className="border-b border-gray-100 px-3 py-2">{rule}</td>
                    <td className="border-b border-gray-100 px-3 py-2 font-mono text-[11px] text-gray-600">{src}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/results/hazard-characterization"
              className="inline-flex items-center gap-1.5 rounded-lg border border-blue-300 bg-blue-50 px-4 py-2 text-sm font-semibold text-blue-700 transition-colors hover:bg-blue-100"
            >
              See the interactive hazard maps
              <Chevron />
            </Link>
            <Link
              href="/methodology"
              className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50"
            >
              Back to the methodology pipeline
            </Link>
          </div>
        </Section>

        {/* ── References ─────────────────────────────────────────── */}
        <Section eyebrow="References" title="Key references" tint="gray">
          <ul className="space-y-2 text-sm leading-relaxed text-gray-700">
            <li>Zscheischler, J. et al. (2020). A typology of compound weather and climate events. <em>Nature Reviews Earth &amp; Environment</em>, 1, 333–347.</li>
            <li>Camus, P. et al. (2021). Compound coastal flooding potential. (Wave–surge co-occurrence framing.)</li>
            <li>Ledford, A. W. &amp; Tawn, J. A. (1996). Statistics for near independence in multivariate extreme values. <em>Biometrika</em>, 83(1), 169–187.</li>
            <li>Coles, S. G., Heffernan, J. E. &amp; Tawn, J. A. (1999). Dependence measures for extreme value analyses. <em>Extremes</em>, 2, 339–365.</li>
          </ul>
        </Section>
      </main>
      <Footer />
    </>
  );
}

/* ───────────────────────── shared components ───────────────────────── */

function MetricTable({
  rows,
  cols,
}: {
  rows: { field: string; definition: string; formula: string; units?: string }[];
  cols: string[];
}) {
  const showUnits = cols.length === 4;
  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200">
      <table className="w-full border-collapse text-left text-xs">
        <thead className="bg-gray-50 text-gray-600">
          <tr>
            <th className="border-b border-gray-200 px-3 py-2 font-semibold">{cols[0]}</th>
            <th className="border-b border-gray-200 px-3 py-2 font-semibold">{cols[1]}</th>
            <th className="border-b border-gray-200 px-3 py-2 font-semibold">{cols[2]}</th>
            {showUnits && <th className="border-b border-gray-200 px-3 py-2 font-semibold">{cols[3]}</th>}
          </tr>
        </thead>
        <tbody className="align-top text-gray-700">
          {rows.map((r) => (
            <tr key={r.field} className="odd:bg-white even:bg-gray-50/50">
              <td className="border-b border-gray-100 px-3 py-2 font-mono text-[11px] font-semibold text-gray-900">{r.field}</td>
              <td className="border-b border-gray-100 px-3 py-2 leading-relaxed">{r.definition}</td>
              <td className="border-b border-gray-100 px-3 py-2 font-mono text-[11px] text-gray-600">{r.formula}</td>
              {showUnits && <td className="border-b border-gray-100 px-3 py-2 text-gray-600">{r.units}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MiniCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <p className="mb-1 text-sm font-semibold text-gray-900">{title}</p>
      <p className="text-xs leading-relaxed text-gray-600">{body}</p>
    </div>
  );
}
