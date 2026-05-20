import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { Tables } from "../components/Tables";
import type { BacktestResult } from "../types";

const result: BacktestResult = {
  run_id: "run-1",
  status: "completed",
  result: {
    metrics: {},
    equity_curve: [],
    positions: [
      { trade_date: "2024-01-02", symbol: "OLD.SZ", weight: 0.5, market_value: 9000 },
      { trade_date: "2024-01-03", symbol: "000001.SZ", weight: 0.5, market_value: 12000 },
    ],
    trades: [{ trade_date: "2024-01-02", symbol: "600000.SH", side: "sell", price: 9.8 }],
    logs: ["loaded 2 symbols", "completed"],
  },
};

afterEach(() => {
  cleanup();
});

describe("Tables", () => {
  it("renders holdings, trades, and logs as actual rows", () => {
    render(<Tables result={result} />);

    expect(screen.getByRole("table", { name: "当前持仓" })).toBeInTheDocument();
    expect(screen.getByText("000001.SZ")).toBeInTheDocument();
    expect(screen.getByText("12000")).toBeInTheDocument();
    expect(screen.queryByText("OLD.SZ")).not.toBeInTheDocument();
    expect(screen.getByRole("table", { name: "交易流水" })).toBeInTheDocument();
    expect(screen.getByText("600000.SH")).toBeInTheDocument();
    expect(screen.getByText("sell")).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "运行日志" })).toBeInTheDocument();
    expect(screen.getByText("loaded 2 symbols")).toBeInTheDocument();
  });

  it("shows no current holdings when final equity date has no positions", () => {
    render(
      <Tables
        result={{
          ...result,
          result: {
            ...result.result!,
            equity_curve: [
              { trade_date: "2024-01-02", equity: 100000 },
              { trade_date: "2024-01-03", equity: 99000 },
            ],
            positions: [{ trade_date: "2024-01-02", symbol: "STALE.SZ", market_value: 9000 }],
          },
        }}
      />,
    );

    expect(screen.getByRole("table", { name: "当前持仓" })).toBeInTheDocument();
    expect(screen.queryByText("STALE.SZ")).not.toBeInTheDocument();
    expect(screen.getByText("暂无数据")).toBeInTheDocument();
  });
});
