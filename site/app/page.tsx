import Navigation from '@/components/Navigation';
import Hero from '@/components/Hero';
import ProjectOverview from '@/components/ProjectOverview';
import ProgressTimeline from '@/components/ProgressTimeline';
import Footer from '@/components/Footer';

export default function Home() {
  return (
    <>
      <Navigation />
      <main>
        <Hero />
        <ProjectOverview />
        <ProgressTimeline />
      </main>
      <Footer />
    </>
  );
}
