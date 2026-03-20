# OSR11 Site Deployment Guide

This guide explains how to deploy and update the OSR11 scientific results website on Vercel.

## Prerequisites

- GitHub account
- Vercel account (free tier works fine) — sign up at [vercel.com](https://vercel.com)
- Git repository with this project

## Initial Deployment

### Step 1: Push to GitHub

Ensure your `site/` directory is committed and pushed to GitHub:

```bash
cd /path/to/osr11
git add site/
git commit -m "Add scientific results website"
git push origin main
```

### Step 2: Import Project to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository (authorize Vercel to access your repos if needed)
4. Select the `osr11` repository

### Step 3: Configure Build Settings

Vercel should auto-detect Next.js. Verify these settings:

- **Framework Preset:** Next.js
- **Root Directory:** `site` ← **IMPORTANT: Click "Edit" and set this to `site`**
- **Build Command:** `npm run build` (auto-detected)
- **Output Directory:** `.next` (auto-detected)
- **Install Command:** `npm install` (auto-detected)

### Step 4: Deploy

1. Click **Deploy**
2. Wait 2-3 minutes for the build to complete
3. Vercel will provide a live URL (e.g., `osr11.vercel.app`)

## Updating the Site

### Method 1: Automatic Deployment (Recommended)

Vercel automatically redeploys when you push to your repository:

```bash
# Make changes to site files
# e.g., update figures in public/figures/

git add site/
git commit -m "Update analysis figures"
git push origin main

# Vercel automatically builds and deploys (takes ~2-3 min)
```

Check deployment status at: `https://vercel.com/[your-username]/osr11`

### Method 2: Manual Deployment via Vercel Dashboard

1. Go to your project dashboard on Vercel
2. Click **"Deployments"** tab
3. Click **"Redeploy"** on the latest deployment
4. Confirm

### Method 3: Deploy from Local (Advanced)

Install Vercel CLI:

```bash
npm i -g vercel
```

Deploy from project root:

```bash
cd /path/to/osr11/site
vercel --prod
```

## Adding New Figures

After generating new analysis outputs:

1. Copy figures to `site/public/figures/`:
   ```bash
   cp outputs/south_sc_test_data_exploratory/figures/* site/public/figures/
   ```

2. Update relevant page components (e.g., `app/results/south-sc/page.tsx`)

3. Commit and push:
   ```bash
   git add site/
   git commit -m "Add new analysis figures"
   git push
   ```

4. Vercel auto-deploys in ~2-3 minutes

## Environment Variables (if needed)

If you need to configure environment variables (e.g., API keys):

1. Go to Vercel project dashboard
2. Navigate to **Settings** → **Environment Variables**
3. Add variables for Production, Preview, and Development
4. Redeploy to apply changes

## Custom Domain (Optional)

To use a custom domain like `osr11.yourdomain.com`:

1. Go to project **Settings** → **Domains**
2. Add your custom domain
3. Update DNS records as instructed by Vercel
4. Vercel automatically provisions SSL certificate

## Troubleshooting

### Build Fails

- Check build logs in Vercel dashboard
- Ensure `package.json` dependencies are correct
- Verify `Root Directory` is set to `site`

### Images Not Loading

- Ensure images are in `site/public/` directory
- Reference images as `/figures/image.png` (not `public/figures/...`)
- Check `next.config.ts` image settings

### Style Changes Not Appearing

- Clear browser cache (Cmd/Ctrl + Shift + R)
- Check if deployment completed successfully
- Verify CSS changes are committed to Git

## Local Development

Test changes locally before deploying:

```bash
cd site/
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to preview.

## Project Structure

```
site/
├── app/                  # Next.js app directory (pages)
│   ├── layout.tsx       # Root layout (metadata, body wrapper)
│   ├── page.tsx         # Home page
│   └── results/         # Results pages
├── components/          # React components
├── public/              # Static assets (served at root /)
│   └── figures/        # Analysis figures
├── lib/                 # Utility functions
├── package.json         # Dependencies
├── next.config.ts       # Next.js configuration
└── vercel.json         # Vercel deployment config

```

## Support

- Vercel Documentation: [https://vercel.com/docs](https://vercel.com/docs)
- Next.js Documentation: [https://nextjs.org/docs](https://nextjs.org/docs)
- Project Issues: Report in GitHub repository

---

**Last Updated:** January 2025  
**Vercel Framework:** Next.js 16.2.0
