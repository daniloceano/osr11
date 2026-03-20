import { dataSources } from '@/content/datasources';
import StatusBadge from './StatusBadge';

export default function DataSourcesSection() {
  return (
    <section id="data" className="border-b border-gray-200 bg-white py-20">
      <div className="mx-auto max-w-5xl px-6">
        <div className="mb-12">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-blue-600">
            Input Data
          </p>
          <h2 className="text-3xl font-bold text-gray-900">Data Sources</h2>
          <p className="mt-3 max-w-2xl text-sm text-gray-600">
            The project relies on multiyear satellite-era reanalyses from Copernicus Marine Service (CMEMS),
            supplemented by atmospheric reanalysis (ERA5) and observational databases of reported coastal events.
          </p>
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          {dataSources.map((ds) => (
            <div
              key={ds.id}
              className="rounded-xl border border-gray-200 bg-gray-50 p-6 flex flex-col gap-4"
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-gray-800">{ds.shortName}</h3>
                  <p className="mt-0.5 text-xs text-gray-500">{ds.name}</p>
                </div>
                <StatusBadge status={ds.status} size="sm" />
              </div>

              {/* Description */}
              <p className="text-xs leading-relaxed text-gray-600">{ds.description}</p>

              {/* Variables */}
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-gray-500">
                  Variables Used
                </p>
                <ul className="space-y-1">
                  {ds.variables.map((v) => (
                    <li key={v} className="flex items-start gap-1.5 text-xs text-gray-600">
                      <span className="mt-1.5 h-1 w-1 flex-shrink-0 rounded-full bg-sky-500" />
                      {v}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Meta chips */}
              <div className="flex flex-wrap gap-2 border-t border-gray-200 pt-3">
                <div className="rounded border border-gray-300 bg-gray-100 px-2 py-1">
                  <span className="text-xs text-gray-500">Resolution: </span>
                  <span className="text-xs text-gray-700">{ds.resolution}</span>
                </div>
                <div className="rounded border border-gray-300 bg-gray-100 px-2 py-1">
                  <span className="text-xs text-gray-500">Period: </span>
                  <span className="text-xs text-gray-700">{ds.period}</span>
                </div>
              </div>

              {/* Role */}
              <div className="rounded-lg bg-gray-100/50 px-3 py-2">
                <p className="text-xs font-semibold text-gray-500 mb-0.5">Role in project</p>
                <p className="text-xs text-gray-600">{ds.role}</p>
              </div>

              {/* Stage */}
              <p className="text-xs text-gray-400">
                <span className="text-gray-500">Pipeline stage: </span>
                {ds.stage}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
