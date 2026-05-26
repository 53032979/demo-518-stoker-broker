import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ResultSummary } from "../components/ResultSummary";

describe("ResultSummary", () => {
  it("formats core metrics", () => {
    const { container } = render(
      <ResultSummary
        metrics={{ total_return: 0.12, annual_return: 0.18, max_drawdown: -0.08, sharpe: 1.23, win_rate: 0.55 }}
      />,
    );

    expect(screen.getByText("12.00%")).toBeInTheDocument();
    expect(screen.getByText("-8.00%")).toBeInTheDocument();
    expect(screen.getByText("总收益").closest("article")).toHaveClass("metric-positive");
    expect(screen.getByText("最大回撤").closest("article")).toHaveClass("metric-negative");
    expect(container.querySelectorAll(".metric-card")).toHaveLength(5);
  });
});
