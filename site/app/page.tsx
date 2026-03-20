import Navigation from '@/components/Navigation';
import Hero from '@/components/Hero';
import ProjectOverview from '@/components/ProjectOverview';
import MethodologyFlowchart from '@/components/MethodologyFlowchart';
import DataSourcesSection from '@/components/DataSourcesSection';
import ResultsGrid from '@/components/ResultsGrid';
import ProgressTimeline from '@/components/ProgressTimeline';
import Footer from '@/components/Footer';

export default function Home() {
  return (
    <>
      <Navigation />
      <main>
        <Hero />
        <ProjectOverview />
        <MethodologyFlowchart />
        <DataSourcesSection />
        <ResultsGrid />
        <ProgressTimeline />
      </main>
      <Footer />
    </>
  );
}
