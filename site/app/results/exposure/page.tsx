import Link from 'next/link';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';
import StatusBadge from '@/components/StatusBadge';
import ExposureClient from './ExposureClient';

export const metadata = {
  title: 'Coastal Population Exposure | OSR11',
  description:
    'Resident population and occupied households within distance bands of the Brazilian coastline, from the IBGE Grade Estatistica 2022, with the candidate normalisations of the exposure term.',
};

export default function ExposurePage() {
  return (
    <>
      <Navigation />
      <main className="pt-16">
        <div className="border-b border-gray-200 bg-white py-16">
          <div className="mx-auto max-w-6xl px-6">
            <div className="mb-4 flex items-center gap-2 text-xs text-gray-500">
              <Link href="/" className="transition-colors hover:text-gray-700">Overview</Link>
              <ChevronSvg />
              <Link href="/results" className="transition-colors hover:text-gray-700">Results</Link>
              <ChevronSvg />
              <span className="text-gray-600">Population Exposure</span>
            </div>

            <div className="mb-4 flex flex-wrap items-start gap-2">
              <StatusBadge status="done" />
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                IBGE Grade Estatística 2022 · 200 m urban / 1 km rural
              </span>
              <span className="rounded-full border border-gray-300 bg-gray-50 px-2.5 py-1 text-xs text-gray-600">
                Cumulative bands · adopted weights 0.4 / 0.3 / 0.2 / 0.1
              </span>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">
              Population Exposure
              <br />
              <span className="text-blue-600">Who lives near the coast</span>
            </h1>
            <p className="mt-3 max-w-3xl text-sm text-gray-600">
              The step between the physical hazard and the integrated risk. The hazard says where
              compound wave and sea-level extremes are frequent, long and intense; the vulnerability
              index says who would cope badly with them. Neither says how many people are there.
              This page counts them, from the census grid. Neither how many people live near the
              coast nor how coastal a municipality is answers the question alone, so the adopted
              term uses an effective population built from all four cumulative distance bands.
              Alternative normalisations stay on the map for comparison only.
            </p>
          </div>
        </div>

        <div className="border-b border-gray-200 bg-gray-50 py-10">
          <div className="mx-auto max-w-6xl px-6">
            <h2 className="mb-4 text-lg font-bold text-gray-900">What is on the map</h2>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
              <ModuleCard
                color="#2171b5"
                title="Adopted Exposure Index"
                body="Uses pop_eff from the cumulative 1, 2, 5 and 10 km bands in both the absolute and relative components."
              />
              <ModuleCard
                color="#d94801"
                title="E — log₁₀ and rank"
                body="The two single-facet candidates. One leaves exposure inert in the index, the other neutralises social vulnerability."
              />
              <ModuleCard
                color="#756bb1"
                title="Effective share"
                body="pop_eff divided by municipal population; the relative half of the adopted exposure criterion."
              />
              <ModuleCard
                color="#737373"
                title="Raw counts"
                body="Population and occupied households within 10 km, on log-spaced classes, plus the absolute half of E (INFORM)."
              />
            </div>
            <p className="mt-4 text-xs text-gray-500">
              Hovering a municipality shows the raw counts in every distance band —{' '}
              <span className="font-mono">1, 2, 5, 10 km</span> and the municipality as a whole —
              each with the share of the municipal total in per cent, next to every normalised
              value, so the derived number can always be traced back to the population behind it.
              It also shows <span className="font-mono">pop_eff</span>, which is a weighted
              exposure proxy rather than a literal inhabitant count.
            </p>
          </div>
        </div>

        <div className="py-10">
          <div className="mx-auto max-w-6xl px-6">
            <ExposureClient />
          </div>
        </div>

        <div className="border-t border-gray-200 bg-gray-50 py-10">
          <div className="mx-auto max-w-6xl px-6">
            <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="text-lg font-bold text-gray-900">Methodology &amp; Caveats</h2>
              <Link
                href="/results/risk-integration"
                className="inline-flex items-center gap-1 text-sm font-semibold text-blue-600 hover:underline"
              >
                Next: risk integration
                <ChevronSvg />
              </Link>
            </div>
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
                <p>
                  <strong className="text-gray-800">Source and attribution.</strong> Population and
                  occupied households come from the IBGE Grade Estatística 2022, whose cells measure
                  200 m in urban census tracts and 1 km in rural ones. The counts are a direct
                  totalisation of census microdata over the household coordinates of the CNEFE — not
                  a modelled disaggregation, which is what distinguishes this source from the global
                  gridded population products. Cells are attributed by centroid, both to a
                  municipality and to a distance band, which keeps the totals additive at the cost
                  of a discretisation error bounded by half a cell diagonal. Distances are measured
                  in EPSG:5880, the same metric projection the coastal hazard projection uses.
                </p>
                <p>
                  <strong className="text-gray-800">Cumulative-band decision.</strong>{' '}
                  The adopted population is <span className="font-mono">pop_eff = 0.4·pop_1km +
                  0.3·pop_2km + 0.2·pop_5km + 0.1·pop_10km</span>. Because the bands are
                  cumulative, the equivalent weights by ring are 1.0 at 0–1 km, 0.6 at 1–2 km,
                  0.3 at 2–5 km and 0.1 at 5–10 km. This quantity is an effective/weighted
                  population, not a literal number of distinct inhabitants.
                </p>
                <p>
                  <strong className="text-gray-800">Absolute and relative together.</strong> The
                  count favours the metropolitan municipalities; the share of the municipal
                  population inside the band favours the small, entirely coastal ones — Bombinhas
                  and Santos both reach 100 %, though one holds 25 thousand people and the other
                  418 thousand. Neither facet alone is exposure, so the recommended term computes
                  both and pairs them, following the treatment INFORM gives its physical-exposure
                  indicators. Both halves are published as their own layers.
                </p>
                <p>
                  <strong className="text-gray-800">Why the normalisation is a scientific choice.</strong>{' '}
                  Min–Max is an affine rescaling: it changes a variable&apos;s range and not its
                  shape. The coastal population count is skewed above 7, so under Min–Max it stays
                  that skewed inside 0–1 and about nine municipalities in ten fall below 0.05 — the
                  term would carry a nominal weight of one third and almost no influence. The
                  logarithm repairs the shape but compresses differences; the percentile rank
                  discriminates everywhere but discards magnitude. The three are kept in the data
                  file so the claim can be checked rather than taken on trust.
                </p>
              </div>
              <div className="space-y-3 text-xs text-gray-600 leading-relaxed">
                <p>
                  <strong className="text-gray-800">Proximity is not impact.</strong> No water level
                  is propagated over land anywhere in this workflow, so nothing here is an
                  inundation extent. These are residents <em>near</em> the coast under a stated
                  distance criterion, never residents <em>affected</em>. The 10 km band is
                  inclusive by design, which errs towards over-counting.
                </p>
                <p>
                  <strong className="text-gray-800">Census time and definition.</strong> The count
                  is of <em>de jure</em> residents on 31 July 2022, a single instant set against 33
                  years of metocean record. The seasonal population of the resort municipalities of
                  the South and Southeast — precisely where the compound hazard is highest — is not
                  represented. IBGE also excludes the two coarsest geocoding levels from the grid,
                  which removes 0.028&nbsp;% of the national population, unevenly by region and most
                  in the North.
                </p>
                <p>
                  <strong className="text-gray-800">Status.</strong> The cumulative-band exposure term is part of
                  the published risk index, which is the geometric mean of hazard, exposure and
                  vulnerability. Results are preliminary — do not cite without consulting the
                  authors.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}

function ChevronSvg() {
  return (
    <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  );
}

function ModuleCard({ color, title, body }: { color: string; title: string; body: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3">
      <div className="mb-1.5 flex items-center gap-2">
        <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
        <h3 className="text-xs font-bold text-gray-900">{title}</h3>
      </div>
      <p className="text-[10px] leading-relaxed text-gray-500">{body}</p>
    </div>
  );
}
