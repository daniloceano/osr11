import { projectMeta } from '@/content/project';

export default function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-gray-50 py-12">
      <div className="mx-auto max-w-5xl px-6">
        <div className="grid gap-8 md:grid-cols-3">
          {/* Project ID */}
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">
              Project
            </p>
            <p className="text-sm font-semibold text-gray-900">OSR11</p>
            <p className="mt-1 text-xs leading-relaxed text-gray-600">
              Compound Coastal Flooding — Joint Wave–Surge Extremes on the South Atlantic
              Eastern Coast of Brazil
            </p>
          </div>

          {/* Team */}
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">
              Research Team
            </p>
            <ul className="space-y-1">
              {projectMeta.authors.map((author) => (
                <li key={author} className="text-xs text-gray-600">
                  {author}
                </li>
              ))}
            </ul>
            <p className="mt-2 text-xs text-gray-500">{projectMeta.institution}</p>
          </div>

          {/* Cite / Data */}
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500">
              Data Sources
            </p>
            <ul className="space-y-1 text-xs text-gray-600">
              <li>WAVERYS · GLORYS12 — Copernicus Marine Service (CMEMS)</li>
              <li>ERA5 — ECMWF / Copernicus Climate Change Service</li>
              <li>Reported events — Leal et al. (2024), Civil Defense SC</li>
              <li>S2ID / Atlas Digital de Desastres — Brazilian Federal Government</li>
              <li>IBGE — Instituto Brasileiro de Geografia e Estatística</li>
            </ul>
          </div>
        </div>

        <div className="mt-8 border-t border-gray-200 pt-6 flex flex-wrap items-center justify-between gap-4">
          <p className="text-xs text-gray-500">
            Results presented are preliminary and subject to revision.
            Do not cite without consulting the authors.
          </p>
          <p className="text-xs text-gray-400">
            Built with Next.js · IAG-USP · {new Date().getFullYear()}
          </p>
        </div>
      </div>
    </footer>
  );
}
