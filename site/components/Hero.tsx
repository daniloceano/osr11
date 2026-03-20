import Link from 'next/link';
import { projectMeta } from '@/content/project';

export default function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-slate-800 bg-slate-950 pt-24 pb-20">
      {/* Background grid */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            'linear-gradient(to right, #38bdf8 1px, transparent 1px), linear-gradient(to bottom, #38bdf8 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      {/* Radial gradient */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(56,189,248,0.06),transparent)]" />

      <div className="relative mx-auto max-w-5xl px-6">
        {/* Status pill */}
        <div className="mb-6 flex items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-300">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
            Research in Progress
          </span>
          <span className="text-xs text-slate-500">IAG-USP · {projectMeta.dataRange}</span>
        </div>

        {/* Title */}
        <h1 className="mb-4 text-4xl font-bold tracking-tight text-slate-100 md:text-5xl lg:text-6xl">
          Compound{' '}
          <span className="bg-gradient-to-r from-sky-400 to-cyan-300 bg-clip-text text-transparent">
            Coastal Flooding
          </span>
        </h1>

        <p className="mb-6 text-lg text-slate-400 md:text-xl max-w-3xl">
          Joint wave–surge extremes on the South Atlantic eastern coast of Brazil
        </p>

        {/* Abstract */}
        <p className="mb-8 max-w-3xl text-base leading-relaxed text-slate-400">
          This project characterises compound coastal flooding events — defined by the simultaneous or near-simultaneous
          occurrence of extreme significant wave heights and elevated storm surge / meteorological tides — along the
          Brazilian coast, using CMEMS multiyear reanalyses (GLORYS12 and WAVERYS). Current focus: southern Santa Catarina.
        </p>

        {/* Stat chips */}
        <div className="mb-8 flex flex-wrap gap-3">
          {[
            { label: 'Study Period', value: '1993–2025' },
            { label: 'Wave Data', value: 'WAVERYS (CMEMS)' },
            { label: 'Sea-Level Data', value: 'GLORYS12 (CMEMS)' },
            { label: 'Current Domain', value: 'South SC (test)' },
          ].map((stat) => (
            <div
              key={stat.label}
              className="rounded-lg border border-slate-700/60 bg-slate-900 px-4 py-2"
            >
              <div className="text-xs text-slate-500">{stat.label}</div>
              <div className="text-sm font-medium text-slate-200">{stat.value}</div>
            </div>
          ))}
        </div>

        {/* CTAs */}
        <div className="flex flex-wrap gap-3">
          <Link
            href="/results/south-sc"
            className="inline-flex items-center gap-2 rounded-lg bg-sky-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-sky-400 transition-colors"
          >
            View Preliminary Results
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
          <a
            href="#methodology"
            className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900 px-5 py-2.5 text-sm font-semibold text-slate-300 hover:bg-slate-800 transition-colors"
          >
            Methodology
          </a>
        </div>

        {/* Authors */}
        <div className="mt-12 border-t border-slate-800 pt-6">
          <p className="text-xs text-slate-500 mb-1">Authors</p>
          <p className="text-sm text-slate-400">
            {projectMeta.authors.join(' · ')}
          </p>
          <p className="mt-1 text-xs text-slate-500">{projectMeta.institution}</p>
        </div>
      </div>
    </section>
  );
}
