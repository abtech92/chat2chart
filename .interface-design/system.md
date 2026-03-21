# Design System - Data & Analysis

SQL Visualizer: chart-optimized analytics interface

## Direction

**Personality:** Data & Analysis
**Foundation:** Cool (slate)
**Depth:** Subtle shadows + borders

## Tokens

### Spacing
Base: 4px
Scale: 4, 8, 12, 16, 24, 32, 48

### Colors
```
--bg: #0f172a (dark navy)
--bg-secondary: #1e293b (slate-800)
--card: #ffffff
--card-alt: #f8fafc (slate-50)
--foreground: #0f172a (slate-900)
--secondary: #475569 (slate-600)
--muted: #94a3b8 (slate-400)
--faint: #e2e8f0 (slate-200)
--border: #e2e8f0
--accent: #6366f1 (indigo-500)
--accent-hover: #4f46e5 (indigo-600)
--success: #10b981 (emerald-500)
--warning: #f59e0b (amber-500)
--error: #ef4444 (red-500)
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05)
--shadow-md: 0 4px 12px rgba(0,0,0,0.08)
--shadow-lg: 0 8px 24px rgba(0,0,0,0.12)

Chart palette: #6366f1, #8b5cf6, #06b6d4, #10b981, #f59e0b, #ef4444, #ec4899, #14b8a6, #f97316, #64748b
```

### Radius
Scale: 6px, 8px, 12px, 16px

### Typography
Font: Inter (clean, data-readable)
Mono: 'JetBrains Mono', 'SF Mono', monospace (SQL, code, data)
Scale: 11, 12, 13, 14 (base), 16, 20, 24, 32
Weights: 400, 500, 600, 700

## Patterns

### Header
- Background: --bg (dark navy)
- Text: white
- Padding: 24px 0
- Subtle gradient or solid

### Button Primary
- Height: 40px
- Padding: 10px 20px
- Radius: 8px
- Font: 14px, 600 weight
- Background: --accent
- Hover: --accent-hover
- Shadow: --shadow-sm
- Transition: all 0.15s ease

### Card
- Border: 1px solid --border
- Padding: 20px
- Radius: 12px
- Background: white
- Shadow: --shadow-sm
- Hover: --shadow-md (interactive cards)

### Input
- Height: 44px
- Padding: 10px 16px
- Radius: 8px
- Border: 1.5px solid --faint
- Focus: border --accent, ring 3px accent/20%
- Font: 14px

### Data Table
- Header: slate-50 bg, 12px uppercase text, 600 weight
- Cell: 13px tabular-nums, 12px 16px padding
- Row hover: slate-50
- Border-bottom: 1px solid --faint
- Zebra: subtle alternate rows

### Pipeline Step
- Circle: 36px, numbered
- States: gray (pending), accent pulse (active), success (done), error (failed)
- Connector: 2px line between steps
- Label: 12px underneath

### Code Block
- Background: #1a1a2e (deep navy)
- Text: #c7d2fe (indigo-200)
- Font: mono, 12px
- Padding: 12px 16px
- Radius: 8px
- Max-height with scroll

### Badge/Tag
- Padding: 2px 8px
- Radius: 4px
- Font: 11px, 600 weight
- Variants: accent, success, warning, outline

## Decisions

| Decision | Rationale | Date |
|----------|-----------|------|
| Dark header, light content | Visual hierarchy — header anchors, content breathes | 2026-03-21 |
| Indigo accent | Professional, works with charts, not overused | 2026-03-21 |
| Inter font | Excellent tabular figures, readable at small sizes | 2026-03-21 |
| 12px radius on cards | Soft enough to feel modern, sharp enough for data | 2026-03-21 |
| Subtle shadows + borders | Cards need lift but not distraction from data | 2026-03-21 |
