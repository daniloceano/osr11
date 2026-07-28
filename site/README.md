# OSR11 Scientific Results Website

A clean, professional scientific results website for the OSR11 project: **Compound Coastal Flooding — Joint Wave–Surge Extremes on the South Atlantic Eastern Coast of Brazil**.

Built with Next.js 16, React 19, and Tailwind CSS 4.

## 📋 Project Overview

This site presents preliminary research results from the OSR11 project at IAG-USP, focusing on the characterization of compound wave–surge extreme events along the Brazilian coast using CMEMS multiyear reanalyses (GLORYS12 and WAVERYS).

**Current scope:** Full Brazilian coast (1993–2025), 808 coastal grid points

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
│       ├── hazard-characterization/ # Coastal Hazard Index map + per-grid-point explorer
│       ├── risk-integration/        # Exposure, vulnerability & risk panel
│       └── south-sc/                # South SC analysis results page
├── components/              # React components
│   ├── Navigation.tsx       # Top navigation bar
│   ├── Hero.tsx            # Landing hero section
│   ├── Footer.tsx          # Site footer
│   ├── FigureGallery.tsx   # Scientific figure viewer
│   ├── CoastalStormMap.tsx  # Interactive SVG storm map (808 grid points)
│   ├── CoastalHazardMap.tsx # Hazard Index and components drawn on the coastline
│   └── ...
├── content/                 # Content data (figures, project metadata)
│   ├── project.ts          # Project text and metadata
│   └── figures.ts          # Figure definitions
├── public/                  # Static assets (served at root /)
│   ├── figures/            # Analysis output figures (PNG)
│   └── data/               # JSON data for interactive maps
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

# 2. Regenerate storm maps data (after re-running Step 3)
conda run -n osr11 python -m src.site.export_storm_maps_data

# 3. Regenerate municipal risk-index data (after updating outputs/risk_index/)
python -m src.site.export_risk_index_data

# 4. Regenerate the coastal Hazard Index layers (after step 3)
python -m src.site.export_coastal_hazard_data

# 5. Update figure metadata in content/figures.ts if needed

# 6. Commit and push
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

### Risk-Index Data

The externally delivered municipal shapefile lives in `../outputs/risk_index/` and is the
only accepted upstream source. The website consumes a single product in `public/data/`:

- `risk_index_municipalities.geojson` — the municipal product
- `risk_index_metadata.json` — layer catalogue, class limits, palettes, statistics

If `../outputs/risk_index/risk_index.shp` is absent the export raises `FileNotFoundError`.
There is no fallback: an incomplete source must fail rather than publish a product
rebuilt from a previous export.

Regenerate them from the repository root:

```bash
python -m src.site.export_risk_index_data
```

The current metadata records the native-grid calculation
`Hazard_Index = norm{[norm(frequency) + norm(duration) + norm(intensity)]/3}`,
its transfer to municipalities,
`Risk_Hazard_raw = (SVI_Coast_2022 / 100) × Hazard_Index`, and
`Risk_Hazard = norm_municipal(Risk_Hazard_raw)` on a 0–1 scale. Each quantity is
published both before and after its Min–Max normalization (`Hazard_Index_raw`,
`Risk_Hazard_raw`). `Hazard_Index_mun`, the hazard renormalized over the
municipalities for equal-weight aggregations, stays in the GeoJSON properties
but is not offered as a map layer. The metadata records the single resolved DBF
alias, `SVI_Coast_` -> `SVI_Coast_2022`; the delivered `Haz_index`,
`Risk_comp` and `Risk_harza` columns are not read.
The native-grid formula itself is centralized in
`../src/04_risk_integration/hazard_index.py` and reused by the exporter and
article figures.

### Coastal Hazard Data

The coastal Hazard Index map consumes:

- `coastal_hazard_segments.geojson` — Natural Earth 10-m coastline split into
  segments of at most 5 km, each carrying the values of its nearest native
  ocean grid point, the nearest coastal municipality
  (`municipality_name`, `municipality_state`, `municipality_distance_km`), and
  `metrics_index`, the position of its grid point inside
  `hazard_characterization_grid_metrics.json`
- `coastal_hazard_metadata.json` — source file, native point count, segment
  count, projection, maximum segment length, association method, distance
  statistics, per-layer fields, units, class limits, and the shared palette
  catalog (`sequential`, `diverging`, `risk`, `month`)
- `coastal_basemap.geojson` — Natural Earth land polygons, country boundaries,
  and Brazilian state boundaries used as map context by every map on the site

Regenerate them from the repository root:

```bash
python -m src.site.export_coastal_hazard_data
```

The geospatial projection of grid values onto the coastline is centralized in
`../src/04_risk_integration/coastal_projection.py` and shared with
`make_article_coastal_hazard_components_map.py`, so the website map and the
article figure are geometrically identical. The coastal rendering never
recalculates or renormalizes the index. The map exposes four layers:
`compound_count_annual_mean` (events yr⁻¹), `mean_overlap_duration` (days),
`mean_compound_intensity_norm` (dimensionless), and `Hazard_Index` (0–1). The
first three use the discrete magma palette of the article figure; the Hazard
Index uses the green-to-red Risk Index palette, defined once in
`../src/04_risk_integration/palettes.py`.

The per-grid-point explorer below the Hazard Index map reuses the same
geometry, basemap, and palettes: it looks up each of the 87 Step 3 metrics
through `metrics_index` and colors the same coastal polylines, so both panels
are visually and geometrically identical. Shared map primitives (projection,
land/ocean/borders, discrete legend, class breaks) live in
`components/coastalMap.tsx`; the municipal risk choropleth uses them too.

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
