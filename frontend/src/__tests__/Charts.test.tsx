import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
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
    price_bars: [
      { trade_date: "2024-01-01", symbol: "000001.SZ", open: 9, high: 11, low: 8.8, close: 10 },
      { trade_date: "2024-01-02", symbol: "000001.SZ", open: 10, high: 12, low: 9.8, close: 11 },
      { trade_date: "2024-01-03", symbol: "000001.SZ", open: 11, high: 12.5, low: 10.8, close: 12 },
    ],
    positions: [],
    trades: [
      { trade_date: "2024-01-01", symbol: "000001.SZ", side: "buy", price: 10 },
      { trade_date: "2024-01-03", symbol: "000001.SZ", side: "sell", price: 12 },
    ],
    logs: [],
  },
};

afterEach(() => {
  cleanup();
});

describe("Charts", () => {
  it("renders polished empty chart states before a backtest run", () => {
    render(<Charts />);

    expect(screen.getByText("资金曲线")).toBeInTheDocument();
    expect(screen.getByText("K线买卖点")).toBeInTheDocument();
    expect(screen.getByText("运行回测后显示资金曲线")).toBeInTheDocument();
    expect(screen.getByText("运行回测后显示K线买卖点")).toBeInTheDocument();
  });

  it("renders SVG equity, drawdown, and trade marker visuals from result data", () => {
    const { container } = render(<Charts result={result} />);

    expect(screen.getByLabelText("资金曲线与回撤")).toBeInTheDocument();
    expect(screen.getByLabelText("价格与买卖点")).toBeInTheDocument();
    expect(screen.getByText("权益曲线")).toBeInTheDocument();
    expect(screen.getByText("回撤")).toBeInTheDocument();
    expect(screen.getByText("买入")).toBeInTheDocument();
    expect(screen.getByText("卖出")).toBeInTheDocument();
    expect(container.querySelector('[data-series="equity"]')).toBeInTheDocument();
    expect(container.querySelector('[data-series="drawdown"]')).toBeInTheDocument();
    expect(container.querySelectorAll('[data-candle="body"]')).toHaveLength(3);
    expect(container.querySelectorAll('[data-marker="buy"]')).toHaveLength(1);
    expect(container.querySelectorAll('[data-marker="sell"]')).toHaveLength(1);
  });

  it("uses only displayed symbol trades for K-line markers", () => {
    const { container } = render(
      <Charts
        result={{
          ...result,
          result: {
            ...result.result!,
            trades: [
              { trade_date: "2024-01-01", symbol: "000001.SZ", side: "buy", price: 10 },
              { trade_date: "2024-01-02", symbol: "OTHER.SZ", side: "sell", price: 99 },
            ],
          },
        }}
      />,
    );

    expect(container.querySelectorAll('[data-marker="buy"]')).toHaveLength(1);
    expect(container.querySelectorAll('[data-marker="sell"]')).toHaveLength(0);
  });
});
