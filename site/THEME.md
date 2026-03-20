# OSR11 Site Theme Guide

## Clean Scientific White Theme

The site uses a clean, professional white theme suitable for scientific publication and presentation.

### Color Palette

#### Backgrounds
- **Primary background:** `bg-white` (#ffffff)
- **Secondary background:** `bg-gray-50` (#f9fafb)
- **Tertiary background:** `bg-gray-100` (#f3f4f6)

#### Text
- **Primary text:** `text-gray-900` (#111827)
- **Secondary text:** `text-gray-700` (#374151)
- **Tertiary text:** `text-gray-600` (#4b5563)
- **Muted text:** `text-gray-500` (#6b7280)

#### Accents
- **Primary accent:** `text-blue-600` / `bg-blue-600` (#2563eb)
- **Hover accent:** `hover:bg-blue-700` (#1d4ed8)
- **Light accent bg:** `bg-blue-50` (#eff6ff)

#### Borders
- **Primary border:** `border-gray-200` (#e5e7eb)
- **Secondary border:** `border-gray-300` (#d1d5db)

#### Status Colors
- **Warning/Progress:** `bg-amber-50`, `text-amber-700`, `border-amber-200`
- **Success:** `bg-green-50`, `text-green-700`, `border-green-200`

### Typography

- **Font Family:** Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto
- **Font Smoothing:** antialiased
- **Line Height:** 1.6 (body), tighter for headings

### Component Patterns

#### Cards
```tsx
className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
```

#### Buttons
```tsx
// Primary
className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"

// Secondary
className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-700 hover:bg-gray-50"
```

#### Section Headers
```tsx
<h2 className="text-3xl font-bold text-gray-900">Title</h2>
<p className="text-gray-600">Subtitle or description</p>
```

#### Navigation
- **Background:** `bg-white/95 backdrop-blur-sm`
- **Border:** `border-b border-gray-200`
- **Active state:** `bg-blue-50 text-blue-600`
- **Hover state:** `hover:bg-gray-100`

### Shadows

- **Subtle shadow:** `shadow-sm` (0 1px 2px rgba(0,0,0,0.05))
- **Card shadow:** `shadow` (0 1px 3px rgba(0,0,0,0.1))
- **Elevated shadow:** `shadow-lg` (0 10px 15px rgba(0,0,0,0.1))

### Scientific Figure Containers

Use the `.figure-container` class defined in `globals.css`:

```tsx
<div className="figure-container">
  <Image src="/figures/..." alt="..." />
  <p className="figure-caption">Figure 1. Caption text...</p>
</div>
```

This provides:
- White background
- Subtle border
- Appropriate padding and spacing
- Consistent shadow

### Accessibility

- Maintain WCAG AA contrast ratios:
  - Gray-900 on white: 16.59:1 ✓
  - Gray-600 on white: 5.74:1 ✓
  - Blue-600 on white: 8.59:1 ✓
- Use semantic HTML elements
- Include aria-labels where appropriate
- Ensure keyboard navigation works

### Responsive Design

- Mobile-first approach using Tailwind breakpoints:
  - `sm:` 640px
  - `md:` 768px
  - `lg:` 1024px
  - `xl:` 1280px

## Migration from Dark Theme

The site was migrated from a dark theme (slate-950 background) to this clean white theme. Key conversions:

| Dark Theme | Light Theme |
|------------|-------------|
| `bg-slate-950` | `bg-white` |
| `bg-slate-900` | `bg-gray-50` |
| `bg-slate-800` | `bg-gray-100` |
| `text-slate-100` | `text-gray-900` |
| `text-slate-400` | `text-gray-600` |
| `text-sky-400` | `text-blue-600` |
| `border-slate-800` | `border-gray-200` |

## Brand Guidelines

### Logo/Icon
- Icon: Cloud with rain/waves (SVG)
- Color: Blue-600 on Blue-50 background
- Border: Blue-600/40 opacity

### Project Name
- Display: **OSR11**
- Full name: "Compound Coastal Flooding — Joint Wave–Surge Extremes"
- Always maintain the branding consistency

## Future Enhancements

Potential additions to consider:

- [ ] Dark mode toggle (optional)
- [ ] Print-optimized CSS
- [ ] PDF export styling for figures
- [ ] Citation formatting utilities
- [ ] Interactive plot theming to match site

---

**Last Updated:** January 2025  
**Framework:** Next.js 16 + Tailwind CSS 4
