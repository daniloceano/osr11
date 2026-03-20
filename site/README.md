# OSR11 Scientific Results Website

A clean, professional scientific results website for the OSR11 project: **Compound Coastal Flooding — Joint Wave–Surge Extremes on the South Atlantic Eastern Coast of Brazil**.

Built with Next.js 16, React 19, and Tailwind CSS 4.

## 📋 Project Overview

This site presents preliminary research results from the OSR11 project at IAG-USP, focusing on the characterization of compound wave–surge extreme events along the Brazilian coast using CMEMS multiyear reanalyses (GLORYS12 and WAVERYS).

**Current scope:** Southern Santa Catarina test domain (1993–2025)

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open browser to http://localhost:3000
```

The page auto-updates as you edit files in `app/` or `components/`.

### Build for Production

```bash
npm run build
npm start
```

## 📂 Project Structure

```
site/
├── app/                      # Next.js App Router pages
│   ├── layout.tsx           # Root layout (metadata, global wrapper)
│   ├── page.tsx             # Home page
│   ├── globals.css          # Global styles and theme
│   └── results/             
│       └── south-sc/        # South SC analysis results page
│           └── page.tsx
├── components/              # React components
│   ├── Navigation.tsx       # Top navigation bar
│   ├── Hero.tsx            # Landing hero section
│   ├── Footer.tsx          # Site footer
│   ├── FigureGallery.tsx   # Scientific figure viewer
│   └── ...
├── content/                 # Content data (figures, project metadata)
│   ├── project.ts          # Project text and metadata
│   └── figures.ts          # Figure definitions
├── public/                  # Static assets (served at root /)
│   └── figures/            # Analysis output figures (PNG)
├── lib/                     # Utility functions
├── DEPLOYMENT.md           # Vercel deployment guide
├── THEME.md                # Design system documentation
└── package.json            # Dependencies and scripts
```

## 🎨 Design System

The site uses a **clean scientific white theme** optimized for readability and professional presentation:

- **Background:** White with subtle gray accents
- **Typography:** Inter font family, optimized line heights
- **Accent color:** Blue-600 (#2563eb)
- **Components:** Minimalist cards, subtle shadows, clear hierarchy

See **[THEME.md](./THEME.md)** for complete design guidelines.

## 📤 Deployment

### Deploy to Vercel (Recommended)

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for step-by-step instructions.

**Quick summary:**

1. Push code to GitHub
2. Import repository in Vercel
3. **Set Root Directory to `site`** ← Important!
4. Deploy

Vercel auto-deploys on every push to `main`.

### Alternative Deployment

The site can be deployed to any Next.js-compatible hosting:

- **Vercel** (recommended, zero-config)
- **Netlify** (requires build config)
- **AWS Amplify**
- **Self-hosted** (requires Node.js server)

## 🔄 Updating Results

After running the analysis pipeline and generating new figures:

```bash
# 1. Copy figures from outputs to site
cp -r outputs/south_sc_test_data_exploratory/figures/* site/public/figures/

# 2. Update figure metadata in content/figures.ts if needed

# 3. Commit and push
git add site/
git commit -m "Update analysis figures"
git push

# Vercel auto-deploys in ~2-3 minutes
```

## 📊 Adding New Analysis Sections

To add a new analysis page (e.g., Central SC):

1. Create page directory:
   ```bash
   mkdir -p app/results/central-sc
   ```

2. Create `page.tsx`:
   ```tsx
   import Navigation from '@/components/Navigation';
   import FigureGallery from '@/components/FigureGallery';
   import Footer from '@/components/Footer';

   export default function CentralSCPage() {
     return (
       <>
         <Navigation />
         <main>
           {/* Your content */}
         </main>
         <Footer />
       </>
     );
   }
   ```

3. Add figures to `content/figures.ts`

4. Update navigation links in `components/Navigation.tsx`

## 🛠️ Tech Stack

- **Framework:** [Next.js 16](https://nextjs.org/) (App Router)
- **React:** 19.2
- **Styling:** [Tailwind CSS 4](https://tailwindcss.com/)
- **Language:** TypeScript 5
- **Linting:** ESLint
- **Deployment:** Vercel

## 📝 Content Management

### Project Metadata

Edit `content/project.ts` to update:
- Authors
- Institution
- Project description
- Methodology text
- Data sources

### Figure Definitions

Edit `content/figures.ts` to:
- Add/remove figures
- Update captions
- Change figure groupings
- Modify metadata

### Styling

- Global styles: `app/globals.css`
- Tailwind config: `tailwind.config.ts` (if needed)
- Component styles: Inline Tailwind classes

## 🧪 Development Tips

### Hot Reload

Next.js automatically reloads when you save files. No manual refresh needed.

### Component Development

Components are in `components/`. Import with `@/components/ComponentName`.

### Image Optimization

Place images in `public/`. Reference as `/path/to/image.png` (no `public/` prefix).

Next.js automatically optimizes images via `next/image`.

### TypeScript

The project is fully typed. Use `npm run lint` to check for issues.

## 📚 Documentation

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** — How to deploy and update the site
- **[THEME.md](./THEME.md)** — Design system and color palette
- **[Next.js Docs](https://nextjs.org/docs)** — Framework documentation
- **[Tailwind CSS Docs](https://tailwindcss.com/docs)** — Styling utilities

## 🤝 Contributing

This is a research project website. For questions or suggestions, contact the project authors.

## 📄 License

Research project © 2025 IAG-USP. Results are preliminary and subject to revision.

---

**Authors:** Danilo Couto de Souza, Iury Sousa, Pedro da Silva Peixoto  
**Institution:** Instituto de Astronomia, Geofísica e Ciências Atmosféricas, Universidade de São Paulo  
**Contact:** IAG-USP

## Learn More About Next.js

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API
- [Learn Next.js](https://nextjs.org/learn) - interactive Next.js tutorial
- [Next.js GitHub](https://github.com/vercel/next.js) - feedback and contributions welcome

