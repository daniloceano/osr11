# Quick Reference: Deploying OSR11 Site to Vercel

## The Problem
When trying to deploy, "site" directory wasn't appearing as an option in Vercel.

## The Solution
Vercel needs to know the Next.js app is in a subdirectory, not the repository root.

## Deployment Steps (5 minutes)

### 1. Push to GitHub
```bash
cd /path/to/osr11
git add site/
git commit -m "Add Vercel config and clean white theme"
git push origin main
```

### 2. Import to Vercel
1. Go to [vercel.com](https://vercel.com) → Sign in
2. Click **"Add New..."** → **"Project"**
3. Choose your GitHub repository `osr11`

### 3. Configure Build Settings ⚠️ CRITICAL STEP
**Before clicking Deploy:**
- Look for **"Root Directory"** setting
- Click **"Edit"** next to it
- Enter: **`site`**
- Verify other settings:
  - Framework Preset: Next.js ✓
  - Build Command: `npm run build` ✓
  - Output Directory: `.next` ✓

### 4. Deploy
Click **"Deploy"** button → Wait 2-3 minutes

### 5. Done!
You'll get a URL like: `https://osr11-xxx.vercel.app`

## Auto-Deploy
Every push to `main` branch = automatic deployment to Vercel

## Updating Figures
```bash
# After running analysis:
cp outputs/south_sc_test_data_exploratory/figures/* site/public/figures/

git add site/public/figures/
git commit -m "Update analysis figures"
git push

# Vercel auto-deploys in 2-3 min
```

## Troubleshooting

**Build fails?**
- Check Vercel dashboard → Deployments → View logs
- Ensure Root Directory is set to `site`

**Images not loading?**
- Images must be in `site/public/`
- Reference as `/figures/image.png` (no `public/` prefix)

**CSS not updating?**
- Clear browser cache (Cmd/Ctrl + Shift + R)
- Wait for deployment to complete (check Vercel dashboard)

## Documentation
- `site/DEPLOYMENT.md` — Full deployment guide
- `site/THEME.md` — Design system
- `site/README.md` — Project overview

## Support
- Vercel Docs: https://vercel.com/docs
- Next.js Docs: https://nextjs.org/docs

---

**Key Takeaway:** Always set Root Directory to `site` when deploying!
