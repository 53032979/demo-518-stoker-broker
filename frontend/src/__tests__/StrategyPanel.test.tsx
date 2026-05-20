import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { StrategyRunConfig } from "../components/StrategyPanel";
import { StrategyPanel } from "../components/StrategyPanel";

const config: StrategyRunConfig = {
  strategy_id: "momentum_top_n",
  pool_id: "csi300",
  start_date: "2024-01-01",
  end_date: "2024-12-31",
  parameters: { top_n: 2, rebalance: "monthly", weighting: "equal" },
  costs: { commission_rate: 0.0003, stamp_tax_rate: 0.001, slippage_bps: 5, min_lot_size: 100 },
};

const strategies = [
  {
    strategy_id: "momentum_top_n",
    name: "动量 Top N",
    category: "momentum",
    description: "",
    parameter_schema: {
      type: "object",
      properties: {
        top_n: { type: "integer", title: "持仓数量", minimum: 1 },
        lookback: { type: "integer", title: "回看窗口", minimum: 1 },
        rebalance: { type: "string", title: "调仓频率", enum: ["weekly", "monthly"] },
        weighting: { type: "string", title: "权重方式", enum: ["equal", "score"] },
        weights: {
          type: "object",
          title: "因子权重",
          properties: {
            momentum: { type: "number", title: "动量权重" },
            value: { type: "number", title: "价值权重" },
          },
        },
      },
    },
    default_parameters: {
      top_n: 3,
      lookback: 60,
      rebalance: "monthly",
      weighting: "equal",
      weights: { momentum: 0.7, value: 0.3 },
    },
    required_fields: [],
  },
  {
    strategy_id: "ma_cross",
    name: "均线交叉",
    category: "trend",
    description: "",
    parameter_schema: {
      type: "object",
      properties: {
        ma_fast: { type: "integer", title: "快线" },
        ma_slow: { type: "integer", title: "慢线" },
      },
    },
    default_parameters: { ma_fast: 5, ma_slow: 20 },
    required_fields: [],
  },
];

const pools = [{ pool_id: "csi300", name: "沪深300", pool_type: "index" as const, symbols: ["000001.SZ"] }];

afterEach(() => {
  cleanup();
});

describe("StrategyPanel", () => {
  it("renders strategy and pool options", () => {
    render(
      <StrategyPanel
        strategies={strategies}
        pools={pools}
        config={config}
        onConfigChange={vi.fn()}
        onRun={vi.fn()}
      />,
    );

    expect(screen.getByText("动量 Top N")).toBeInTheDocument();
    expect(screen.getByText("沪深300")).toBeInTheDocument();
    expect(screen.getByLabelText("持仓数量")).toHaveAttribute("step", "1");
    expect(screen.getByLabelText("佣金率")).toHaveValue(0.0003);
  });

  it("renders editable controls from the selected strategy schema", () => {
    const onConfigChange = vi.fn();
    render(
      <StrategyPanel strategies={strategies} pools={pools} config={config} onConfigChange={onConfigChange} onRun={vi.fn()} />,
    );

    expect(screen.getByLabelText("回看窗口")).toHaveValue(60);
    expect(screen.getByLabelText("调仓频率")).toHaveValue("monthly");
    expect(screen.getByLabelText("权重方式")).toHaveValue("equal");
    expect(screen.getByLabelText("动量权重")).toHaveValue(0.7);

    fireEvent.change(screen.getByLabelText("回看窗口"), { target: { value: "90" } });
    expect(onConfigChange).toHaveBeenLastCalledWith(
      expect.objectContaining({ parameters: expect.objectContaining({ top_n: 2, lookback: 90 }) }),
    );

    fireEvent.change(screen.getByLabelText("调仓频率"), { target: { value: "weekly" } });
    expect(onConfigChange).toHaveBeenLastCalledWith(
      expect.objectContaining({ parameters: expect.objectContaining({ rebalance: "weekly" }) }),
    );

    fireEvent.change(screen.getByLabelText("滑点bps"), { target: { value: "12" } });
    expect(onConfigChange).toHaveBeenLastCalledWith(
      expect.objectContaining({ costs: expect.objectContaining({ slippage_bps: 12 }) }),
    );
  });

  it("resets parameters to defaults when the strategy changes", () => {
    const onConfigChange = vi.fn();
    render(
      <StrategyPanel strategies={strategies} pools={pools} config={config} onConfigChange={onConfigChange} onRun={vi.fn()} />,
    );

    fireEvent.change(screen.getByLabelText("策略模板"), { target: { value: "ma_cross" } });

    expect(onConfigChange).toHaveBeenCalledWith({
      ...config,
      strategy_id: "ma_cross",
      parameters: { ma_fast: 5, ma_slow: 20 },
    });
  });
});
