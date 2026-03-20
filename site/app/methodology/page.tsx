import Link from 'next/link';
import MethodologyFlowchart from '@/components/MethodologyFlowchart';

export const metadata = {
  title: 'Analytical Framework | OSR11',
  description: '8-step execution algorithm from data preparation to risk mapping',
};

export default function MethodologyPage() {
  return (
    <main className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="border-b border-gray-200 bg-white py-16">
        <div className="mx-auto max-w-5xl px-6">
          <Link 
            href="/"
            className="mb-6 inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 transition-colors"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Home
          </Link>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Analytical Framework
          </h1>
          <p className="text-lg text-gray-600 max-w-3xl">
            Sequential 8-step execution algorithm from data acquisition and preprocessing to final risk integration and hotspot identification
          </p>
        </div>
      </section>

      {/* Methodology Flowchart */}
      <MethodologyFlowchart />
    </main>
  );
}
