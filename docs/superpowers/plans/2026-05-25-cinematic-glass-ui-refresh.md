# Cinematic Glass UI Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh the existing A Share Quant Lab React workbench into a premium dark Cinematic Glass quant dashboard without changing backend behavior.

**Architecture:** Keep the current component boundaries and API client behavior. Add semantic presentational markup in `Workbench`, `StrategyPanel`, `ResultSummary`, `Charts`, and `Tables`, then replace the existing plain CSS with token-driven dark glass styling.

**Tech Stack:** React 18, TypeScript, Vite, Vitest, Testing Library, CSS variables, existing SVG charts.

---

## Scope Check

The approved spec is one focused UI refresh for the existing single-page workbench. It does not require backend changes, new dependencies, or chart library replacement.

## File Structure

- Modify `frontend/src/__tests__/Workbench.test.tsx`: assert the new product header and status surface render.
- Modify `frontend/src/__tests__/StrategyPanel.test.tsx`: assert the strategy console heading and disabled custom-pool save state.
- Modify `frontend/src/__tests__/ResultSummary.test.tsx`: assert semantic metric emphasis classes.
- Modify `frontend/src/__tests__/Charts.test.tsx`: assert chart panel headings, legends, and polished empty states.
- Modify `frontend/src/__tests__/Tables.test.tsx`: assert table metadata is present while preserving real table roles.
- Modify `frontend/src/components/Workbench.tsx`: add app shell header and content grid wrapper.
- Modify `frontend/src/components/StrategyPanel.tsx`: add presentational section wrappers and disable save when no symbols are entered.
- Modify `frontend/src/components/ResultSummary.tsx`: add semantic metric card metadata and tone classes.
- Modify `frontend/src/components/Charts.tsx`: add chart card wrappers, legends, and empty state markup.
- Modify `frontend/src/components/Tables.tsx`: add row count metadata and stronger table card structure.
- Modify `frontend/src/styles.css`: implement Cinematic Glass dark tokens, responsive layout, focus states, motion, charts, and tables.

## Task 1: Add UI Refresh Tests

**Files:**
- Modify: `frontend/src/__tests__/Workbench.test.tsx`
- Modify: `frontend/src/__tests__/StrategyPanel.test.tsx`
- Modify: `frontend/src/__tests__/ResultSummary.test.tsx`
- Modify: `frontend/src/__tests__/Charts.test.tsx`
- Modify: `frontend/src/__tests__/Tables.test.tsx`

- [x] **Step 1: Add focused failing assertions**

Add assertions for these behaviors:

```tsx
expect(screen.getByText("A Share Quant Lab")).toBeInTheDocument();
expect(screen.getByText("Cinematic strategy workbench")).toBeInTheDocument();
expect(screen.getByText("Strategy Console")).toBeInTheDocument();
expect(screen.getByRole("button", { name: "保存股票池" })).toBeDisabled();
expect(screen.getByText("资金曲线")).toBeInTheDocument();
expect(screen.getByText("运行回测后显示资金曲线")).toBeInTheDocument();
expect(screen.getByText("2 rows")).toBeInTheDocument();
```

- [x] **Step 2: Run targeted tests and verify RED**

Run:

```bash
npm test -- --run frontend/src/__tests__/Workbench.test.tsx frontend/src/__tests__/StrategyPanel.test.tsx frontend/src/__tests__/ResultSummary.test.tsx frontend/src/__tests__/Charts.test.tsx frontend/src/__tests__/Tables.test.tsx
```

Expected: fail because the new header, console label, disabled state, chart headings, and table metadata do not exist yet.

## Task 2: Implement Presentational Markup

**Files:**
- Modify: `frontend/src/components/Workbench.tsx`
- Modify: `frontend/src/components/StrategyPanel.tsx`
- Modify: `frontend/src/components/ResultSummary.tsx`
- Modify: `frontend/src/components/Charts.tsx`
- Modify: `frontend/src/components/Tables.tsx`

- [x] **Step 1: Add shell and panel markup**

Implement:

```tsx
<section className="workbench">
  <header className="app-header">...</header>
  <div className="workbench-grid">...</div>
</section>
```

Keep all existing API calls, callbacks, labels, and button names.

- [x] **Step 2: Add metric, chart, and table metadata**

Implement semantic cards, chart legends, empty-state wrappers, and row-count metadata without changing data calculations.

- [x] **Step 3: Run targeted tests and verify GREEN**

Run the same targeted test command from Task 1.

Expected: pass.

## Task 3: Implement Cinematic Glass Styling

**Files:**
- Modify: `frontend/src/styles.css`

- [x] **Step 1: Replace plain dashboard styling**

Implement CSS variables, dark shell, glass surfaces, responsive grids, focus rings, button states, chart colors, table scroll containment, and `prefers-reduced-motion`.

- [x] **Step 2: Run frontend tests**

Run:

```bash
npm test
```

Expected: all frontend tests pass.

- [x] **Step 3: Run frontend build**

Run:

```bash
npm run build
```

Expected: TypeScript and Vite build complete successfully.

## Task 4: Visual Verification

**Files:**
- No source file edits unless visual verification finds a bug.

- [x] **Step 1: Start dev server**

Run:

```bash
npm run dev -- --port 5173
```

Expected: Vite serves the app on `http://127.0.0.1:5173/`.

- [x] **Step 2: Inspect desktop and mobile layouts**

Use the browser to inspect:

```text
http://127.0.0.1:5173/
```

Check desktop and narrow widths for no horizontal page overflow, readable controls, visible focus states, chart empty states, and table scroll containment.

- [x] **Step 3: Fix any visual defects and rerun verification**

If CSS or markup changes are needed, rerun:

```bash
npm test
npm run build
```

Expected: all checks remain green.

## Execution Notes

- Targeted UI tests passed after implementation.
- Full frontend test suite passed with `npm test -- --run`.
- Production build passed with `npm run build`.
- Browser verification covered desktop, narrow mobile width, empty state, and completed backtest result state.
