import { resultCards } from '@/content/results';
import ResultCard from './ResultCard';

export default function ResultsGrid() {
  return (
    <section id="results" className="border-b border-gray-200 bg-gray-50 py-20">
      <div className="mx-auto max-w-5xl px-6">
        <div className="mb-12">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-blue-600">
            Analyses &amp; Outputs
          </p>
          <h2 className="text-3xl font-bold text-gray-900">Preliminary Results</h2>
          <p className="mt-3 max-w-2xl text-sm text-gray-700">
            The cards below summarise the methodological steps in this project — what has been
            completed, what is in progress, and what is planned. Threshold calibration, hazard
            characterization, and municipal risk integration now have detailed interactive result pages.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {resultCards.map((card) => (
            <ResultCard key={card.id} card={card} />
          ))}
        </div>
      </div>
    </section>
  );
}
