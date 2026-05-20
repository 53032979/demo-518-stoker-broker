import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Workbench } from "../components/Workbench";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Workbench", () => {
  it("renders the main regions", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/strategies")) {
          return {
            ok: true,
            json: async () => [
              {
                strategy_id: "momentum_top_n",
                name: "动量 Top N",
                category: "momentum",
                description: "",
                parameter_schema: {},
                default_parameters: {},
                required_fields: [],
              },
            ],
          };
        }
        if (url.endsWith("/pools")) {
          return {
            ok: true,
            json: async () => [{ pool_id: "csi300", name: "沪深300", pool_type: "index", symbols: ["000001.SZ"] }],
          };
        }
        return {
          ok: true,
          json: async () => ({ run_id: "run-1", status: "completed" }),
        };
      }),
    );

    render(<Workbench />);

    expect(screen.getByText("策略配置")).toBeInTheDocument();
    expect(screen.getByText("回测结果")).toBeInTheDocument();
    expect(await screen.findByText("动量 Top N")).toBeInTheDocument();
    expect(screen.getByText("沪深300")).toBeInTheDocument();
  });
});
