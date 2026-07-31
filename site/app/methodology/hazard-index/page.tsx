import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';

export const metadata = {
  title: 'Hazard Index — Construction and Coastal Representation | OSR11',
  description:
    'How the composite coastal Hazard Index is built: compound-event detection, the three physical components, Min–Max normalization on the 808-point native ocean grid, equal-weight aggregation, coastal rendering, and transfer to municipalities.',
};

/* ───────────────────────── shared components ───────────────────────── */

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
  step,
  eyebrow,
  title,
  children,
  tint = 'white',
}: {
  id?: string;
  step?: number;
  eyebrow?: string;
  title: string;
  children: React.ReactNode;
  tint?: 'white' | 'gray';
}) {
  return (
    <section
      id={id}
      className={`border-b border-gray-200 py-14 ${tint === 'gray' ? 'bg-gray-50' : 'bg-white'}`}
    >
      <div className="mx-auto max-w-5xl px-6">
        {eyebrow && (
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-blue-600">
            {eyebrow}
          </p>
        )}
        <h2 className="mb-5 flex items-baseline gap-3 text-2xl font-bold text-gray-900">
          {step !== undefined && (
            <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
              {step}
            </span>
          )}
          {title}
        </h2>
        {children}
      </div>
    </section>
  );
}

function FieldTable({
  rows,
}: {
  rows: { field: string; meaning: string; unit: string }[];
}) {
  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200">
      <table className="w-full border-collapse text-left text-xs">
        <thead className="bg-gray-50 text-gray-600">
          <tr>
            <th className="border-b border-gray-200 px-3 py-2 font-semibold">Field</th>
            <th className="border-b border-gray-200 px-3 py-2 font-semibold">What it measures</th>
            <th className="border-b border-gray-200 px-3 py-2 font-semibold">Unit shown on maps</th>
          </tr>
        </thead>
        <tbody className="align-top text-gray-700">
          {rows.map((row) => (
            <tr key={row.field} className="odd:bg-white even:bg-gray-50/50">
              <td className="border-b border-gray-100 px-3 py-2 font-mono text-[11px] font-semibold text-gray-900">
                {row.field}
              </td>
              <td className="border-b border-gray-100 px-3 py-2 leading-relaxed">{row.meaning}</td>
              <td className="border-b border-gray-100 px-3 py-2 text-gray-600">{row.unit}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const componentRows = [
  {
    field: 'compound_count_total',
    meaning:
      'Number of compound events detected at the grid point over the whole record. This absolute count is the frequency term of the index.',
    unit: 'events (the maps show compound_count_annual_mean, in events yr⁻¹)',
  },
  {
    field: 'mean_integrated_severity',
    meaning:
      'Mean, over the compound events at the point, of the severity integrated across the days that meet the full criterion: on each such day, 0.5·(wave excess above the local q70 threshold + level excess of SWL above the local HAT), each rescaled by the domain-wide Q05/Q95 of those daily excesses. Being a time integral it carries magnitude and persistence in a single quantity, so it is not bounded by the daily discretisation of the sea-level field.',
    unit: 'dimensionless',
  },
  {
    field: 'mean_overlap_duration · mean_compound_intensity_norm',
    meaning:
      'Diagnostics only — these are computed and published but no longer enter the index. Duration was retired because it measured the coincidence of two percentile tests rather than a physical duration, was discretised into whole days over a domain-wide range of about one day, and anticorrelated with frequency (Spearman −0.550) so the two cancelled inside the equal-weight mean. Peak intensity was superseded by the integrated form but is retained so the two can be compared.',
    unit: 'days · dimensionless',
  },
];

/* ───────────────────────── page ───────────────────────── */

export default function HazardIndexMethodologyPage() {
  return (
    <>
      <Navigation />
      <main className="pt-16">
        {/* ── Header ─────────────────────────────────────────────── */}
        <div className="border-b border-gray-200 bg-white py-16">
          <div className="mx-auto max-w-5xl px-6">
            <div className="mb-4 flex items-center gap-2 text-xs text-gray-500">
              <Link href="/" className="transition-colors hover:text-gray-700">
                Overview
              </Link>
              <Chevron />
              <Link href="/methodology" className="transition-colors hover:text-gray-700">
                Methodology
              </Link>
              <Chevron />
              <span className="text-gray-600">Hazard Index</span>
            </div>

            <div className="mb-4 flex flex-wrap items-start gap-2">
              <StatusBadge status="done" />
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                Step 4 — Risk Integration
              </span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                808 native grid points · 1993–2025
              </span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              The Coastal Hazard Index
              <br />
              <span className="text-blue-600">
                From compound events to a 0–1 composite index
              </span>
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-gray-600">
              This page is the single reference for how the Hazard Index is constructed, displayed,
              and combined with social vulnerability. The other pages summarize and link here rather
              than restating the formulas. The canonical implementation lives in{' '}
              <code className="rounded bg-gray-100 px-1 font-mono text-[11px]">
                src/04_risk_integration/hazard_index.py
              </code>
              , and every product — article figures, website layers, and the municipal risk index —
              reads from it.
            </p>
          </div>
        </div>

        {/* ── 1. Period and domain ───────────────────────────────── */}
        <Section step={1} eyebrow="Scope" title="Period and domain">
          <p className="mb-4 text-sm leading-relaxed text-gray-700">
            The index covers <strong>1993–2025</strong> and is defined on the{' '}
            <strong>808 coastal points of the native ocean grid</strong> — the same points on which
            the storm catalogs and the compound-event catalog are built. Every normalization
            described below is taken over this fixed 808-point population, which makes the index a{' '}
            <em>relative</em> measure across the Brazilian coast.
          </p>
        </Section>

        {/* ── 2. Compound event detection ────────────────────────── */}
        <Section step={2} eyebrow="Input" title="Detection of compound events" tint="gray">
          <p className="mb-4 text-sm leading-relaxed text-gray-700">
            At each grid point, significant wave height (Hₛ, WAVERYS) and <strong>tide-free</strong>{' '}
            sea level (GLORYS12 <code className="rounded bg-gray-100 px-1 font-mono text-[11px]">zos</code>)
            are catalogued independently as peaks-over-threshold episodes using the q70/q99
            thresholds calibrated in Step 2e (recalibrated 2026-07-30 on the production detector).
            A candidate <strong>compound event</strong> is an Hₛ episode and a{' '}
            <code className="rounded bg-gray-100 px-1 font-mono text-[11px]">zos</code> episode that
            overlap by at least one calendar day at the same point. The astronomical tide re-enters
            not as part of any detection threshold but as an acceptance{' '}
            <strong>gate</strong>: a candidate becomes an event only where the still-water level
            reaches the local Highest Astronomical Tide, max(SWL) &gt; HAT, with
            SWL = (zos − mean zos) + tide_daily_max.
          </p>
          <p className="mb-4 text-sm leading-relaxed text-gray-700">
            Each accepted event carries an integrated severity measured over the HAT datum;
            aggregating per grid point produces the catalog metrics that the index consumes.
            Overlap duration and peak intensity are still computed and published, as diagnostics.
          </p>
          <Link
            href="/methodology/compound-detection"
            className="inline-flex items-center gap-1 text-sm font-semibold text-blue-600 hover:underline"
          >
            Full compound-detection methodology
            <Chevron />
          </Link>
        </Section>

        {/* ── 3. Components ──────────────────────────────────────── */}
        <Section step={3} eyebrow="Components" title="The two components of the index">
          <p className="mb-4 text-sm leading-relaxed text-gray-700">
            The hazard is not reduced to how often events happen. Two catalog metrics enter the
            index, describing <strong>how often</strong> compound events occur and{' '}
            <strong>how severe</strong> they are when integrated over their duration. A third
            component, mean overlap duration, was retired on 2026-07-29; it and the peak-based
            intensity remain published as diagnostics but are not inputs to the index.
          </p>
          <FieldTable rows={componentRows} />
          <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-amber-800">
              Revision of 2026-07-27
            </p>
            <p className="mt-1.5 text-sm leading-relaxed text-amber-900">
              The intensity component previously used the <em>absolute</em> peaks of each event. It
              now uses the excess over the local q90 threshold. The absolute sea-level peak was almost
              entirely determined by the tidal regime (R² = 0.998 regressing the mean peak on the local
              threshold; 91% of the northern peak is baseline), so the term encoded the astronomical
              tide rather than event severity. The revision leaves the Hazard Index ranking largely
              intact (Spearman 0.88) but restores a southward gradient to the intensity itself, and
              cuts the worst regional clipping from 30% to 10% of events. The superseded values remain
              in the catalog as{' '}
              <code className="rounded bg-amber-100 px-1 text-xs">*_abspeak</code>.
            </p>
          </div>
        </Section>

        {/* ── 4. Displayed values ────────────────────────────────── */}
        <Section step={4} eyebrow="Presentation" title="What the component maps actually show" tint="gray">
          <p className="mb-4 text-sm leading-relaxed text-gray-700">
            The component layers of the coastal map and panels (a)–(c) of the article figure show
            the <strong>native-grid catalog values in their own units</strong>:
          </p>
          <ul className="mb-4 list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-gray-700">
            <li>frequency in <strong>events yr⁻¹</strong>;</li>
            <li>
              mean integrated severity as the <strong>dimensionless</strong> catalog metric (daily
              excesses over the local wave threshold and over HAT, rescaled domain-wide and summed
              across the full-criterion days of each event).
            </li>
            <li>
              the retired diagnostics — overlap duration in <strong>days</strong> and peak intensity
              as a <strong>dimensionless</strong> score — where a panel shows them.
            </li>
          </ul>
          <p className="text-sm leading-relaxed text-gray-700">
            No extra Min–Max scaling is applied for presentation. A reader can therefore compare a
            map value against the catalog directly, and the intensity panel is not relabelled as a
            &ldquo;normalized component score&rdquo;.
          </p>
        </Section>

        {/* ── 5. Normalization ───────────────────────────────────── */}
        <Section step={5} eyebrow="Construction" title="Normalization used to build the index">
          <p className="mb-3 text-sm leading-relaxed text-gray-700">
            The two components use fixed anchors independent of the observed sample:
          </p>
          <Eq>{`Hazard_Frequency = min(compound_count_total / 99, 1)
Hazard_Severity  = min(fillna(mean_integrated_severity, 0) / 1, 1)`}</Eq>
          <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-relaxed text-amber-900">
            <strong>This normalization is methodological.</strong> It exists only to make the two
            components commensurable inside the index. It is <em>not</em> what the component maps
            display (see step 4), and it is performed on the native ocean grid — never separately
            within municipalities.
          </p>
        </Section>

        {/* ── 6. Aggregation ─────────────────────────────────────── */}
        <Section step={6} eyebrow="Construction" title="Equal-weight aggregation" tint="gray">
          <p className="mb-3 text-sm leading-relaxed text-gray-700">
            The two normalized components are averaged with equal weights of 1/2:
          </p>
          <Eq>{`Hazard_Index_raw =
    (Hazard_Frequency + Hazard_Severity) / 2`}</Eq>
          <p className="text-sm leading-relaxed text-gray-700">
            Equal weights are an explicit modelling choice, made in the absence of impact-calibrated
            weights for the Brazilian coast. The average is still <strong>compensatory</strong> —
            a point with many mild events can reach the same score as a point with few severe ones —
            but unlike the retired duration term, frequency and integrated severity are{' '}
            <em>positively</em> correlated (Spearman +0.60, against −0.55 for the pair that was
            replaced), so the two components now reinforce each other instead of cancelling.
          </p>
        </Section>

        {/* ── 7. Final normalization ─────────────────────────────── */}
        <Section step={7} eyebrow="Construction" title="Final normalization of the Hazard Index">
          <p className="mb-3 text-sm leading-relaxed text-gray-700">
            The mean is the final index; no second Min–Max is applied:
          </p>
          <Eq>{`Hazard_Index = Hazard_Index_raw ∈ [0, 1]`}</Eq>
          <p className="text-sm leading-relaxed text-gray-700">
            Since <code className="rounded bg-gray-100 px-1 font-mono text-[11px]">Hazard_Index_raw</code>{' '}
            spans roughly 0.18–0.66 on the grid, this second step is what turns the composite into a
            readable 0–1 index. The value 0 marks the least hazardous native grid point and 1 the
            most hazardous one — not an absolute zero or an absolute maximum of coastal hazard.
          </p>
        </Section>

        {/* ── 8. Coastal representation ──────────────────────────── */}
        <Section step={8} eyebrow="Cartography" title="Coastal representation" tint="gray">
          <p className="mb-3 text-sm leading-relaxed text-gray-700">
            The index lives on ocean grid points, but is communicated along the shoreline. The
            coastal rendering is a <strong>visualization of the native-grid values</strong>: it does
            not recalculate, rescale, or smooth the index.
          </p>
          <ul className="mb-3 list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-gray-700">
            <li>
              The <strong>Natural Earth 10-m coastline</strong> is clipped to a 30-km buffer around
              the union of the coastal municipalities.
            </li>
            <li>
              The linework is reprojected to <strong>SIRGAS 2000 / Brazil Polyconic
              (EPSG:5880)</strong> and split into segments of at most <strong>5 km</strong>.
            </li>
            <li>
              Each segment is associated with the <strong>nearest native ocean grid point</strong>,
              measured between the segment midpoint and the point in the metric projection, and
              takes that point&rsquo;s values.
            </li>
          </ul>
          <p className="text-sm leading-relaxed text-gray-700">
            The same module —{' '}
            <code className="rounded bg-gray-100 px-1 font-mono text-[11px]">
              src/04_risk_integration/coastal_projection.py
            </code>{' '}
            — produces the article figure and the website layer, so both are geometrically
            identical. The exported metadata records the projection, the segment length, the
            association rule, and the distribution of segment-to-point distances.
          </p>
        </Section>

        {/* ── 9. Transfer to municipalities ──────────────────────── */}
        <Section step={9} eyebrow="Hand-off" title="Transfer to municipalities">
          <p className="text-sm leading-relaxed text-gray-700">
            Each coastal municipality is already associated with one ocean grid point by the
            external spatial-association workflow — a cartographic transfer, not an exposure
            component. The municipality <strong>receives the Hazard Index already normalized on
            the grid</strong>, and it is <strong>not renormalized</strong>, so a municipal
            Hazard Index value stays directly comparable with the coastal map and with the native
            grid. The risk product uses a separate field,{' '}
            <code className="rounded bg-gray-100 px-1 font-mono text-[11px]">Hazard_Index_mun</code>,
            which is the same transferred field without municipal rescaling.
          </p>
        </Section>

        {/* ── 10. SVI integration ────────────────────────────────── */}
        <Section step={10} eyebrow="Risk" title="Exposure, vulnerability and the integrated risk" tint="gray">
          <p className="mb-3 text-sm leading-relaxed text-gray-700">
            Risk has three components. The hazard says where compound extremes are frequent and
            severe; <strong>exposure</strong> says how many people are there; and the Social
            Vulnerability Index (SVI_Coast_2022, 0–100 from PCA on ten IBGE 2022 Census variables)
            says who would cope badly. The vulnerability term is <strong>social only</strong>: no
            physical susceptibility layer — geomorphology, terrain elevation, natural barriers,
            coastal defences, drainage — exists in this product. Exposure is the resident population
            within 10 km of the coastline, from the IBGE Grade Estatística 2022:
          </p>
          <Eq>{`pop_eff = 0.4·pop_1km + 0.3·pop_2km + 0.2·pop_5km + 0.1·pop_10km
Exposure_absolute = clip[(log₁₀(pop_eff) − 2) / (6 − 2), 0, 1]
Exposure_relative = pop_eff / pop_municipality
Exposure_Index    = √(Exposure_absolute × Exposure_relative)`}</Eq>
          <p className="mb-3 mt-3 text-sm leading-relaxed text-gray-700">
            The goalposts of 10² and 10⁶ inhabitants are <strong>fixed, not taken from the
            data</strong>, so the scale does not move when the set of municipalities changes and
            0.5 always denotes 10,000 people. The absolute count and the municipal share are paired
            because neither is exposure on its own: the count favours the metropolitan
            municipalities, the share favours the small entirely-coastal ones. Both choices follow
            the treatment INFORM gives its physical-exposure indicators.
          </p>
          <Eq>{`V = Φ(PC1 / sd(PC1, ddof=0))
Risk_Hazard = (Hazard_Index_mun × Exposure_Index × V)^(1/3)`}</Eq>
          <p className="mt-3 text-sm leading-relaxed text-gray-700">
            The <strong>geometric</strong> mean is conjunctive: a component near zero pulls the
            whole index down. That is the property the IPCC risk framework implies — without a
            hazard, or with nobody exposed, there is no potential for adverse consequences — and it
            is what an arithmetic mean would discard, letting a large population compensate for the
            absence of a physical driver. No floor or final Min–Max is applied. Exact hazard zero
            means no accepted compound event in 1993–2025, not impossibility of physical risk.
          </p>
          <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs leading-relaxed text-amber-900">
            <strong>Proximity, not impact.</strong> No water level is propagated over land anywhere
            in this workflow, so the exposure term counts residents <em>near</em> the coast under a
            stated distance criterion, never residents <em>affected</em>. It is a count of{' '}
            <em>de jure</em> residents on 31 July 2022, so the seasonal population of the resort
            municipalities is not represented.
          </p>
          <Link
            href="/results/risk-integration"
            className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-blue-600 hover:underline"
          >
            See the municipal risk maps
            <Chevron />
          </Link>
        </Section>

        {/* ── 11. Limitations ────────────────────────────────────── */}
        <Section step={11} eyebrow="For the auditor" title="Limitations">
          <div className="grid gap-4 md:grid-cols-2">
            <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-gray-700">
              <li>
                <strong>Relative and compensatory.</strong> Both Min–Max steps are taken over the
                808-point domain, so the index ranks the Brazilian coast against itself; a low
                component can be offset by a high one.
              </li>
              <li>
                <strong>Equal weights.</strong> The 1/2 weighting is an assumption, not an
                impact-calibrated result.
              </li>
              <li>
                <strong>No physical vulnerability.</strong> Vulnerability is the social index alone.
                Two stretches with the same income profile and the same hazard receive the same
                vulnerability whether they sit on a rocky cliff or on a sand plain 1 m above sea
                level.
              </li>
              <li>
                <strong>Zero-hazard municipalities.</strong> 83 of the 280 municipalities with a
                risk value draw their hazard from a grid point that accepted no compound event, so
                their <code className="rounded bg-gray-100 px-1 font-mono text-[11px]">Hazard_Index_mun</code>{' '}
                is exactly 0 and their risk rests on the 0.01 floor. They occupy ranks 191–280, and
                their ordering among themselves is set by exposure and vulnerability alone.
              </li>
            </ul>
            <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-gray-700">
              <li>
                <strong>Dimensionless intensity.</strong> The intensity component is an event-level
                dimensionless score built from the excess over the local threshold and domain-wide
                Q05/Q95 references, not a physical magnitude in metres. Because the local baseline is
                removed, it measures how anomalous an event was, not how high the water reached.
              </li>
              <li>
                <strong>Segment-to-point distance.</strong> Coastal segments are up to ~120 km from
                their nearest grid point in the widest shelf sectors; the coastal line is a display
                of the ocean value, not a nearshore calculation.
              </li>
              <li>
                <strong>Not expected damage.</strong> The index does not represent absolute expected
                damage, loss, or inundation depth.
              </li>
            </ul>
          </div>
          <p className="mt-5 rounded-lg border border-gray-300 bg-white px-4 py-3 text-xs leading-relaxed text-gray-600">
            <strong className="text-gray-800">Status.</strong> These are preliminary results,
            subject to revision — please do not cite without consulting the authors.
          </p>
        </Section>

        {/* ── Navigation ─────────────────────────────────────────── */}
        <Section eyebrow="Next" title="Where to go from here" tint="gray">
          <div className="flex flex-wrap gap-3">
            <Link
              href="/results/hazard-characterization"
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
            >
              See the coastal Hazard Index map
              <Chevron />
            </Link>
            <Link
              href="/results/risk-integration"
              className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50"
            >
              Municipal risk integration
            </Link>
            <Link
              href="/methodology"
              className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-700 transition-colors hover:bg-gray-50"
            >
              Back to the methodology pipeline
            </Link>
          </div>
        </Section>
      </main>
      <Footer />
    </>
  );
}
