import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Charts } from "../components/Charts";
import type { BacktestResult } from "../types";

const result: BacktestResult = {
  run_id: "run-1",
  status: "completed",
  result: {
    metrics: {},
    equity_curve: [
      { trade_date: "2024-01-01", equity: 1 },
      { trade_date: "2024-01-02", equity: 1.08 },
      { trade_date: "2024-01-03", equity: 1.02 },
    ],
    positions: [],
    trades: [
      { trade_date: "2024-01-01", symbol: "000001.SZ", side: "buy", price: 10 },
      { trade_date: "2024-01-03", symbol: "000001.SZ", side: "sell", price: 12 },
    ],
    logs: [],
  },
};

describe("Charts", () => {
  it("renders SVG equity, drawdown, and trade marker visuals from result data", () => {
    const { container } = render(<Charts result={result} />);

    expect(screen.getByLabelText("资金曲线与回撤")).toBeInTheDocument();
    expect(screen.getByLabelText("价格与买卖点")).toBeInTheDocument();
    expect(container.querySelector('[data-series="equity"]')).toBeInTheDocument();
    expect(container.querySelector('[data-series="drawdown"]')).toBeInTheDocument();
    expect(container.querySelectorAll('[data-marker="buy"]')).toHaveLength(1);
    expect(container.querySelectorAll('[data-marker="sell"]')).toHaveLength(1);
  });
});
