import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ResultSummary } from "../components/ResultSummary";

describe("ResultSummary", () => {
  it("formats core metrics", () => {
    render(
      <ResultSummary
        metrics={{ total_return: 0.12, annual_return: 0.18, max_drawdown: -0.08, sharpe: 1.23, win_rate: 0.55 }}
      />,
    );

    expect(screen.getByText("12.00%")).toBeInTheDocument();
    expect(screen.getByText("-8.00%")).toBeInTheDocument();
  });
});
