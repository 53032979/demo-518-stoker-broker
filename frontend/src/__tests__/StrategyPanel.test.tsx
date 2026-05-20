import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { StrategyRunConfig } from "../components/StrategyPanel";
import { StrategyPanel } from "../components/StrategyPanel";

const config: StrategyRunConfig = {
  strategy_id: "momentum_top_n",
  pool_id: "csi300",
  start_date: "2024-01-01",
  end_date: "2024-12-31",
  top_n: 2,
};

describe("StrategyPanel", () => {
  it("renders strategy and pool options", () => {
    render(
      <StrategyPanel
        strategies={[
          {
            strategy_id: "momentum_top_n",
            name: "动量 Top N",
            category: "momentum",
            description: "",
            parameter_schema: {},
            default_parameters: {},
            required_fields: [],
          },
        ]}
        pools={[{ pool_id: "csi300", name: "沪深300", pool_type: "index", symbols: ["000001.SZ"] }]}
        config={config}
        onConfigChange={vi.fn()}
        onRun={vi.fn()}
      />,
    );

    expect(screen.getByText("动量 Top N")).toBeInTheDocument();
    expect(screen.getByText("沪深300")).toBeInTheDocument();
  });
});
