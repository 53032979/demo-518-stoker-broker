import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
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
    parameter_schema: {
      type: "object",
      properties: {
        top_n: { type: "integer", title: "持仓数量", minimum: 1 },
        lookback: { type: "integer", title: "回看窗口", minimum: 1 },
        rebalance: { type: "string", title: "调仓频率", enum: ["weekly", "monthly"] },
        weighting: { type: "string", title: "权重方式", enum: ["equal", "score"] },
      },
    },
    default_parameters: { top_n: 2, lookback: 60, rebalance: "monthly", weighting: "equal" },
    required_fields: [],
  },
  {
    strategy_id: "value_low_pe",
    name: "低估值策略",
    category: "value",
    description: "",
    parameter_schema: {
      type: "object",
      properties: {
        top_n: { type: "integer", title: "持仓数量", minimum: 1 },
        weighting: { type: "string", title: "权重方式", enum: ["equal", "cap"] },
        weights: {
          type: "object",
          title: "因子权重",
          properties: {
            value: { type: "number", title: "价值权重" },
            quality: { type: "number", title: "质量权重" },
          },
        },
      },
    },
    default_parameters: { top_n: 4, weighting: "cap", weights: { value: 0.8, quality: 0.2 } },
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

function completedBacktest(totalReturn: number) {
  return okJson({
    run_id: `run-${totalReturn}`,
    status: "completed",
    result: {
      metrics: {
        total_return: totalReturn,
        annual_return: 0.18,
        max_drawdown: -0.08,
        sharpe: 1.23,
        win_rate: 0.55,
      },
      equity_curve: [
        { trade_date: "2024-01-31", equity: 1 },
        { trade_date: "2024-02-29", equity: 1 + totalReturn },
      ],
      price_bars: [
        { trade_date: "2024-01-31", symbol: "000001.SZ", open: 10, high: 11, low: 9, close: 10.5 },
        { trade_date: "2024-02-29", symbol: "000001.SZ", open: 11, high: 12, low: 10, close: 11.5 },
      ],
      positions: [{ symbol: "000001.SZ", weight: 1, market_value: 12000 }],
      trades: [{ trade_date: "2024-02-01", symbol: "000001.SZ", side: "buy", price: 12.3, quantity: 1000 }],
      logs: ["done"],
    },
  });
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((innerResolve, innerReject) => {
    resolve = innerResolve;
    reject = innerReject;
  });
  return { promise, resolve, reject };
}

async function flushPromises() {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
}

function stubFetch(
  routes: Partial<{
    strategies: unknown;
    pools: unknown;
    backtest: unknown;
    upload: unknown;
    createPool: unknown;
  }> = {},
) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith("/strategies")) {
      const response = routes.strategies ?? okJson(strategies);
      if (response instanceof Error) throw response;
      return response;
    }
    if (url.endsWith("/pools") && init?.method !== "POST") {
      const response = routes.pools ?? okJson(pools);
      if (response instanceof Error) throw response;
      return response;
    }
    if (url.endsWith("/backtests")) {
      return routes.backtest ?? completedBacktest(0.12);
    }
    if (url.endsWith("/data/uploads")) {
      return routes.upload ?? okJson({ status: "validated", rows: 12, symbols: 3, start_date: "2024-01-01", end_date: "2024-01-31" });
    }
    if (url.endsWith("/pools") && init?.method === "POST") {
      return routes.createPool ?? okJson({ pool_id: "custom-1", name: "自定义股票池", pool_type: "custom", symbols: ["000001.SZ"] });
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
    fireEvent.change(screen.getByLabelText("持仓数量"), { target: { value: "7.8" } });
    fireEvent.change(screen.getByLabelText("权重方式"), { target: { value: "equal" } });
    fireEvent.change(screen.getByLabelText("佣金率"), { target: { value: "0.0005" } });
    fireEvent.change(screen.getByLabelText("滑点bps"), { target: { value: "8" } });
    fireEvent.click(screen.getByRole("button", { name: "运行回测" }));

    await waitFor(() => expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith("/backtests"))).toBe(true));
    expect(backtestPayload(fetchMock)).toMatchObject({
      strategy_id: "value_low_pe",
      pool_id: "zz500",
      start_date: "2024-02-01",
      end_date: "2024-10-31",
      parameters: { top_n: 7, weighting: "equal", weights: { value: 0.8, quality: 0.2 } },
      costs: { commission_rate: 0.0005, stamp_tax_rate: 0.001, slippage_bps: 8, min_lot_size: 100 },
    });
  });

  it("resets parameters to the selected strategy defaults", async () => {
    const fetchMock = stubFetch();
    render(<Workbench />);

    await screen.findByText("低估值策略");
    fireEvent.change(screen.getByLabelText("策略模板"), { target: { value: "value_low_pe" } });
    fireEvent.click(screen.getByRole("button", { name: "运行回测" }));

    await waitFor(() => expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith("/backtests"))).toBe(true));
    expect(backtestPayload(fetchMock)).toMatchObject({
      strategy_id: "value_low_pe",
      parameters: { top_n: 4, weighting: "cap", weights: { value: 0.8, quality: 0.2 } },
    });
  });

  it("keeps the latest run result when an earlier run finishes later", async () => {
    const firstRun = deferred<ReturnType<typeof completedBacktest>>();
    const secondRun = deferred<ReturnType<typeof completedBacktest>>();
    let runCount = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/strategies")) return okJson(strategies);
        if (url.endsWith("/pools")) return okJson(pools);
        if (url.endsWith("/backtests")) {
          runCount += 1;
          return runCount === 1 ? firstRun.promise : secondRun.promise;
        }
        return errorJson("Unexpected request");
      }),
    );
    render(<Workbench />);

    await screen.findByText("准备就绪");
    fireEvent.click(screen.getByRole("button", { name: "运行回测" }));
    fireEvent.click(screen.getByRole("button", { name: "运行回测" }));

    await act(async () => {
      secondRun.resolve(completedBacktest(0.22));
      await flushPromises();
    });
    expect(await screen.findByText("22.00%")).toBeInTheDocument();

    await act(async () => {
      firstRun.resolve(completedBacktest(0.01));
      await flushPromises();
    });
    expect(screen.getByText("22.00%")).toBeInTheDocument();
    expect(screen.queryByText("1.00%")).not.toBeInTheDocument();
  });

  it("keeps late load errors hidden after a successful run", async () => {
    const strategyLoad = deferred<ReturnType<typeof errorJson>>();
    const poolLoad = deferred<ReturnType<typeof errorJson>>();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/strategies")) return strategyLoad.promise;
        if (url.endsWith("/pools")) return poolLoad.promise;
        if (url.endsWith("/backtests")) return completedBacktest(0.12);
        return errorJson("Unexpected request");
      }),
    );
    render(<Workbench />);

    fireEvent.click(screen.getByRole("button", { name: "运行回测" }));
    expect(await screen.findByText("回测完成")).toBeInTheDocument();

    await act(async () => {
      strategyLoad.resolve(errorJson("late strategy unavailable"));
      poolLoad.resolve(errorJson("late pool unavailable"));
      await flushPromises();
    });

    expect(screen.getByText("回测完成")).toBeInTheDocument();
    expect(screen.queryByText(/late strategy unavailable/)).not.toBeInTheDocument();
    expect(screen.queryByText(/late pool unavailable/)).not.toBeInTheDocument();
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
    expect(screen.getByLabelText("资金曲线与回撤")).toBeInTheDocument();
    expect(screen.getAllByText("000001.SZ").length).toBeGreaterThan(0);
    expect(screen.getByText("buy")).toBeInTheDocument();
    expect(screen.getByText("done")).toBeInTheDocument();
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
    const fetchMock = stubFetch({
      upload: okJson({
        status: "validated",
        rows: 12,
        symbols: 3,
        start_date: "2024-01-01",
        end_date: "2024-01-31",
        pool: { pool_id: "upload-1", name: "上传股票池", pool_type: "custom", symbols: ["600000.SH"] },
      }),
    });
    render(<Workbench />);

    await screen.findByText("准备就绪");
    fireEvent.change(screen.getByLabelText("本地数据文件"), {
      target: { files: [new File(["symbol,trade_date\n"], "daily.csv", { type: "text/csv" })] },
    });

    expect(await screen.findByText("上传完成：12 行，3 个标的")).toBeInTheDocument();
    expect(screen.getByLabelText("股票池")).toHaveValue("upload-1");

    fireEvent.click(screen.getByRole("button", { name: "运行回测" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith("/backtests"))).toBe(true));
    expect(backtestPayload(fetchMock)).toMatchObject({ pool_id: "upload-1" });
  });

  it("saves and selects a custom pool", async () => {
    const fetchMock = stubFetch();
    render(<Workbench />);

    await screen.findByText("准备就绪");
    fireEvent.change(screen.getByLabelText("自定义股票池标的"), { target: { value: "000001.SZ\n600000.SH" } });
    fireEvent.click(screen.getByRole("button", { name: "保存股票池" }));

    await waitFor(() =>
      expect(fetchMock.mock.calls.some(([input, init]) => String(input).endsWith("/pools") && init?.method === "POST")).toBe(true),
    );
    expect(screen.getByLabelText("股票池")).toHaveValue("custom-1");
    expect(screen.getByText("自定义股票池")).toBeInTheDocument();
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
