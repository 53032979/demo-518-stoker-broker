import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Workbench } from "../components/Workbench";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const strategies = [
  {
    strategy_id: "momentum_top_n",
    name: "动量 Top N",
    category: "momentum",
    description: "",
    parameter_schema: {},
    default_parameters: {},
    required_fields: [],
  },
  {
    strategy_id: "value_low_pe",
    name: "低估值策略",
    category: "value",
    description: "",
    parameter_schema: {},
    default_parameters: {},
    required_fields: [],
  },
];

const pools = [
  { pool_id: "csi300", name: "沪深300", pool_type: "index", symbols: ["000001.SZ"] },
  { pool_id: "zz500", name: "中证500", pool_type: "index", symbols: ["000905.SH"] },
];

function okJson(value: unknown) {
  return {
    ok: true,
    json: async () => value,
  };
}

function errorJson(message: string) {
  return {
    ok: false,
    json: async () => ({ message }),
    statusText: message,
  };
}

function stubFetch(
  routes: Partial<{
    strategies: unknown;
    pools: unknown;
    backtest: unknown;
    upload: unknown;
  }> = {},
) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith("/strategies")) {
      const response = routes.strategies ?? okJson(strategies);
      if (response instanceof Error) throw response;
      return response;
    }
    if (url.endsWith("/pools")) {
      const response = routes.pools ?? okJson(pools);
      if (response instanceof Error) throw response;
      return response;
    }
    if (url.endsWith("/backtests")) {
      return (
        routes.backtest ??
        okJson({
          run_id: "run-1",
          status: "completed",
          result: {
            metrics: { total_return: 0.12, annual_return: 0.18, max_drawdown: -0.08, sharpe: 1.23, win_rate: 0.55 },
            equity_curve: [{ trade_date: "2024-01-31", equity: 1.12 }],
            positions: [{ symbol: "000001.SZ", weight: 1 }],
            trades: [{ symbol: "000001.SZ", side: "buy" }],
            logs: ["done"],
          },
        })
      );
    }
    if (url.endsWith("/data/uploads")) {
      return routes.upload ?? okJson({ status: "validated", rows: 12, symbols: 3, start_date: "2024-01-01", end_date: "2024-01-31" });
    }
    return errorJson("Unexpected request");
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function backtestPayload(fetchMock: ReturnType<typeof stubFetch>) {
  const call = fetchMock.mock.calls.find(([input]) => String(input).endsWith("/backtests"));
  expect(call).toBeDefined();
  return JSON.parse((call?.[1] as RequestInit).body as string);
}

describe("Workbench", () => {
  it("renders the main regions", async () => {
    stubFetch();

    render(<Workbench />);

    expect(screen.getByText("策略配置")).toBeInTheDocument();
    expect(screen.getByText("回测结果")).toBeInTheDocument();
    expect(await screen.findByText("动量 Top N")).toBeInTheDocument();
    expect(screen.getByText("沪深300")).toBeInTheDocument();
  });

  it("posts selected controls in the backtest payload", async () => {
    const fetchMock = stubFetch();
    render(<Workbench />);

    await screen.findByText("低估值策略");
    fireEvent.change(screen.getByLabelText("策略模板"), { target: { value: "value_low_pe" } });
    fireEvent.change(screen.getByLabelText("股票池"), { target: { value: "zz500" } });
    fireEvent.change(screen.getByLabelText("开始日期"), { target: { value: "2024-02-01" } });
    fireEvent.change(screen.getByLabelText("结束日期"), { target: { value: "2024-10-31" } });
    fireEvent.change(screen.getByLabelText("持仓数量"), { target: { value: "7" } });
    fireEvent.click(screen.getByRole("button", { name: "运行回测" }));

    await waitFor(() => expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith("/backtests"))).toBe(true));
    expect(backtestPayload(fetchMock)).toMatchObject({
      strategy_id: "value_low_pe",
      pool_id: "zz500",
      start_date: "2024-02-01",
      end_date: "2024-10-31",
      parameters: { top_n: 7, rebalance: "monthly", weighting: "equal" },
    });
  });

  it("keeps fallback controls available when config loading fails", async () => {
    stubFetch({ strategies: errorJson("strategy unavailable"), pools: errorJson("pool unavailable") });
    render(<Workbench />);

    expect(await screen.findByText("配置加载失败，已使用默认配置")).toBeInTheDocument();
    expect(screen.getByText("动量 Top N")).toBeInTheDocument();
    expect(screen.getByText("沪深300")).toBeInTheDocument();
  });

  it("shows run success results", async () => {
    stubFetch();
    render(<Workbench />);

    await screen.findByText("准备就绪");
    fireEvent.click(screen.getByRole("button", { name: "运行回测" }));

    expect(await screen.findByText("回测完成")).toBeInTheDocument();
    expect(screen.getByText("12.00%")).toBeInTheDocument();
    expect(screen.getByText("资金曲线 / 回撤曲线")).toBeInTheDocument();
    expect(screen.getAllByText("1 条")).toHaveLength(3);
  });

  it("shows run failure errors", async () => {
    stubFetch({ backtest: errorJson("run exploded") });
    render(<Workbench />);

    await screen.findByText("准备就绪");
    fireEvent.click(screen.getByRole("button", { name: "运行回测" }));

    expect(await screen.findByText("回测失败")).toBeInTheDocument();
    expect(screen.getByText("run exploded")).toBeInTheDocument();
  });

  it("shows upload success status", async () => {
    stubFetch();
    render(<Workbench />);

    await screen.findByText("准备就绪");
    fireEvent.change(screen.getByLabelText("本地数据文件"), {
      target: { files: [new File(["symbol,trade_date\n"], "daily.csv", { type: "text/csv" })] },
    });

    expect(await screen.findByText("上传完成：12 行，3 个标的")).toBeInTheDocument();
  });

  it("shows upload failure errors", async () => {
    stubFetch({ upload: errorJson("bad upload") });
    render(<Workbench />);

    await screen.findByText("准备就绪");
    fireEvent.change(screen.getByLabelText("本地数据文件"), {
      target: { files: [new File(["bad"], "daily.csv", { type: "text/csv" })] },
    });

    expect(await screen.findByText("上传失败")).toBeInTheDocument();
    expect(screen.getByText("bad upload")).toBeInTheDocument();
  });
});
