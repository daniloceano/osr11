import { resultCards } from '@/content/results';
import ResultCard from './ResultCard';

export default function ResultsGrid() {
  return (
    <section id="results" className="border-b border-slate-800 bg-[#0a0f1e] py-20">
      <div className="mx-auto max-w-5xl px-6">
        <div className="mb-12">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-sky-400">
            Analyses &amp; Outputs
          </p>
          <h2 className="text-3xl font-bold text-slate-100">Preliminary Results</h2>
          <p className="mt-3 max-w-2xl text-sm text-slate-400">
            The cards below summarise the analytical blocks in this project — what has been
            implemented, what is in progress, and what is planned. Completed and in-progress
            analyses can be accessed for detailed results and figures.
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
