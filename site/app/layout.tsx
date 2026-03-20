import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'OSR11 — Compound Coastal Flooding | IAG-USP',
  description:
    'Scientific results site for OSR11: characterisation of compound wave–surge extreme events on the South Atlantic eastern coast of Brazil using CMEMS multiyear reanalyses.',
  keywords: [
    'compound flooding',
    'coastal hazard',
    'significant wave height',
    'storm surge',
    'South Atlantic',
    'Brazil',
    'GLORYS12',
    'WAVERYS',
    'IAG-USP',
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full bg-white text-gray-900">
        {children}
      </body>
    </html>
  );
}
