# A Share Quant Lab Cinematic Glass UI Refresh

Date: 2026-05-25

## Goal

Upgrade the existing A Share Quant Lab workbench from a plain functional dashboard into a more professional and premium dark interface. The refresh should make the app feel like a high-end quant strategy command center while preserving the current MVP workflow: configure strategy inputs on the left, run a daily backtest, and inspect metrics, charts, positions, trades, and logs on the right.

The visual direction is Cinematic Glass: dark blue-black surfaces, layered translucent panels, subtle ambient light, crisp financial status colors, and restrained motion. The implementation must keep data readability, accessibility, and test stability ahead of decorative effects.

## Scope

This refresh includes:

- A product-level header for brand, run status, and compact context.
- A polished sticky strategy control panel with clearer grouping and stronger interaction states.
- A richer result dashboard with glass metric cards, chart panels, legends, professional empty states, and improved table styling.
- A semantic dark design token system in CSS variables.
- Motion and hover states using opacity and transform only.
- Responsive behavior for desktop, tablet, and narrow mobile widths.
- Focus states, contrast, and reduced-motion support.

This refresh does not include:

- Backend API changes.
- New strategy templates or backtest engine behavior.
- Replacing the existing SVG chart implementation with ECharts.
- Theme switching UI. The default experience is dark.
- Large dependency additions unless a current dependency is already available and clearly useful.

## Design System

### Visual Language

The UI should feel like a cinematic trading terminal, not a game or cyberpunk shell. Use deep layered backgrounds, quiet glow, and thin glass borders. Avoid saturated neon, constant animation, scanlines, glitch effects, and low-contrast gray-on-gray text.

Core traits:

- Background: dark blue-black gradient with subtle radial ambient lights.
- Surfaces: translucent panels with `backdrop-filter`, thin borders, and top-edge highlights.
- Radius: controlled and consistent, mostly 12px to 18px.
- Density: compact enough for analytics, with enough spacing to distinguish groups.
- Icons: no emoji as structural icons. If icons are needed, use CSS shapes or existing dependencies only.
- Typography: technical but readable, with mono-style numerals for metrics and tables.

### Color Tokens

Use semantic CSS variables rather than one-off hex values in components:

- `--bg`: `#020617`
- `--bg-soft`: `#07111f`
- `--surface`: `rgba(15, 23, 42, 0.72)`
- `--surface-strong`: `rgba(15, 23, 42, 0.92)`
- `--surface-muted`: `rgba(30, 41, 59, 0.62)`
- `--border`: `rgba(148, 163, 184, 0.22)`
- `--border-strong`: `rgba(125, 211, 252, 0.34)`
- `--text`: `#f8fafc`
- `--text-muted`: `#94a3b8`
- `--text-soft`: `#cbd5e1`
- `--accent`: `#60a5fa`
- `--accent-strong`: `#818cf8`
- `--positive`: `#22c55e`
- `--negative`: `#ef4444`
- `--warning`: `#f59e0b`
- `--focus`: `#38bdf8`

Financial semantics must remain consistent:

- Positive return, buy markers, and success states use green.
- Drawdown, sell markers, and error states use red.
- Loading, warnings, and execution states use amber.
- Primary calls to action use blue/indigo.

### Typography

Prefer `Fira Sans` for UI copy and `Fira Code` for headings, metrics, and tabular data. Load with `font-display: swap` through Google Fonts if the project is already comfortable with external font loading. Provide local fallbacks:

- Sans: `"Fira Sans", "IBM Plex Sans", system-ui, sans-serif`
- Mono: `"Fira Code", "JetBrains Mono", ui-monospace, SFMono-Regular, monospace`

Numbers in KPI cards, chart labels, and tables should use tabular figures.

## Layout

### Shell

The app should become a full-screen cockpit:

- `body` and root fill the viewport.
- `.workbench` becomes a vertical shell with header plus content grid.
- Main content uses a desktop grid of `320px minmax(0, 1fr)`.
- The left panel is sticky on desktop and becomes normal flow on small screens.
- The right result panel keeps its current hierarchy but gains stronger grouping.

### Header

Add a top header above the control/result grid:

- Brand block: `A Share Quant Lab` and a concise subtitle such as `Cinematic strategy workbench`.
- Status cluster: current load or action status in a pill, plus optional small context chips for default pool/date range.
- Header must not contain hidden behavior; it is informational only.

### Control Panel

Keep current form controls and callbacks. Improve presentation:

- Add a compact eyebrow label such as `Strategy Console`.
- Group fields visually without increasing interaction complexity.
- Make primary run button visually dominant.
- Make secondary actions subordinate but still clear.
- File input should look intentional, not browser-default-only.
- Keep all labels visible. Do not rely on placeholders.
- Controls must remain at least 44px high where practical.

### Results

The result panel should read as a mission-control dashboard:

- Result header with title, status pill, and error block when needed.
- Metric cards with label, value, and small descriptive captions.
- Chart panels with internal titles, legends, and polished empty states.
- Tables with sticky headers, row hover, mono numbers, and horizontal scroll containment.

## Component Changes

### `Workbench`

Add an app-level header before the existing two-column content. Preserve all existing state handling and API behavior.

Recommended structure:

- Root section `.workbench`
- Header `.app-header`
- Content grid `.workbench-grid`
- Existing `StrategyPanel`
- Existing `.result-panel`

Status text should be reused in the header and result area. The visual state can be inferred from `actionError`, `loadError`, and whether status contains loading/running text.

### `StrategyPanel`

Keep the component API unchanged. Improve markup only where it helps styling or accessibility:

- Add a panel header with title and short description.
- Wrap major sections in lightweight groups if needed.
- Add `disabled` to the save-pool button when no custom symbols exist.
- Keep the run button name exactly `运行回测` so current tests remain meaningful.
- Preserve every `aria-label` used by tests.

### `ResultSummary`

Keep the existing metric values. Add semantic class names for positive, negative, neutral, or warning emphasis where possible:

- Total return and annual return: green when positive, red when negative.
- Max drawdown: red when negative.
- Sharpe: blue or neutral.
- Win rate: blue/green depending on value.

No new data should be required.

### `Charts`

Keep SVG charts. Improve visual affordances:

- Add panel headings outside SVG or within a wrapper.
- Add a compact legend for equity, drawdown, price, buy, and sell markers.
- Use CSS variables for stroke/fill colors.
- Empty states should include a short title and secondary instruction.
- Preserve existing SVG `aria-label` values.

### `Tables`

Keep the current table logic. Improve the visual frame:

- Add table subtitles or row count metadata if cheap and useful.
- Keep sticky table headers.
- Use hover and focus states.
- Continue horizontal scroll for narrow widths.
- Keep table `aria-label` equal to title.

## Interaction And Accessibility

Requirements:

- Visible focus rings for buttons, selects, inputs, textareas, and file controls.
- Smooth hover/focus transitions between 150ms and 300ms.
- `prefers-reduced-motion: reduce` disables page entrance and hover lift animations.
- Text contrast must be sufficient on glass surfaces.
- Errors use red plus text, not color alone.
- Loading/running state uses visible text and status styling.
- Tables remain accessible as real tables.
- No content should overflow the viewport horizontally except inside intended table scroll containers.

## Responsive Behavior

Breakpoints:

- `> 1100px`: two-column cockpit with sticky left panel.
- `700px - 1100px`: single column with header and result panels stacked, charts can remain two columns if space allows.
- `< 700px`: single column, metric cards use two or one columns, chart and table panels stack.

Rules:

- Use `min-height: 100dvh`.
- Keep page padding responsive with `clamp()`.
- Use `minmax(0, 1fr)` on grids to avoid overflow.
- Tables scroll horizontally within their card.

## Testing And Verification

Automated checks:

- Run frontend tests with `npm test`.
- Run frontend build with `npm run build`.
- Run backend tests only if UI changes unexpectedly touch shared project config.

Visual checks:

- Start the Vite dev server.
- Inspect the workbench at desktop width.
- Inspect mobile/narrow width.
- Confirm header, sticky panel, metric cards, chart empty states, chart result states, and table scroll behavior.
- Confirm no horizontal page overflow.

## Acceptance Criteria

- The app opens to a premium dark Cinematic Glass quant dashboard.
- Existing backtest, upload, and custom pool flows still work.
- Existing test-visible labels and button names still render.
- Empty states are polished and informative.
- Result states are more professional after a successful run.
- Controls have visible hover and focus states.
- The layout is usable at 375px width.
- Motion is restrained and respects reduced-motion preference.
- No unrelated backend or data-model changes are introduced.
