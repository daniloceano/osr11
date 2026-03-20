'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navLinks = [
  { href: '/', label: 'Overview' },
  { href: '/#methodology', label: 'Methodology' },
  { href: '/#data', label: 'Data Sources' },
  { href: '/#results', label: 'Results' },
  { href: '/#progress', label: 'Progress' },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-slate-800 bg-slate-950/90 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex h-7 w-7 items-center justify-center rounded border border-sky-500/40 bg-sky-500/10">
            <svg className="h-3.5 w-3.5 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
            </svg>
          </div>
          <span className="text-sm font-semibold text-slate-200 group-hover:text-sky-400 transition-colors">
            OSR11
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded px-3 py-1.5 text-sm transition-colors ${
                pathname === link.href && !link.href.includes('#')
                  ? 'bg-sky-500/10 text-sky-400'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>

        <Link
          href="/results/south-sc"
          className="hidden md:inline-flex items-center gap-1.5 rounded border border-sky-500/40 bg-sky-500/10 px-3 py-1.5 text-sm font-medium text-sky-400 hover:bg-sky-500/20 transition-colors"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
          South SC Results
        </Link>
      </div>
    </nav>
  );
}
