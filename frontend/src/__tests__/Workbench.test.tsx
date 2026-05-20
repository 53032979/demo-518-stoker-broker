import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Workbench } from "../components/Workbench";

describe("Workbench", () => {
  it("renders the main regions", () => {
    render(<Workbench />);

    expect(screen.getByText("策略配置")).toBeInTheDocument();
    expect(screen.getByText("回测结果")).toBeInTheDocument();
  });
});
