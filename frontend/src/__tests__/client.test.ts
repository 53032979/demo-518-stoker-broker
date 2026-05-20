import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchStrategies, runBacktest, uploadDailyBars } from "../api/client";
import type { BacktestPayload } from "../types";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api client", () => {
  it("loads strategies", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [{ strategy_id: "momentum_top_n", name: "动量 Top N" }],
      }),
    );

    const result = await fetchStrategies();

    expect(result[0].strategy_id).toBe("momentum_top_n");
  });

  it("posts backtest payloads as JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ run_id: "run-1", status: "completed" }),
    });
    vi.stubGlobal("fetch", fetchMock);
    const payload: BacktestPayload = {
      strategy_id: "momentum_top_n",
      pool_id: "csi300",
      start_date: "2024-01-01",
      end_date: "2024-01-31",
      parameters: { top_n: 5 },
      costs: {
        commission_rate: 0.0003,
        stamp_tax_rate: 0.001,
        slippage_bps: 1,
        min_lot_size: 100,
      },
    };

    await runBacktest(payload);

    const [, init] = fetchMock.mock.calls[0];
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/backtests",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(payload),
      }),
    );
    expect(new Headers(init.headers).get("Content-Type")).toBe("application/json");
  });

  it("uploads daily bars as multipart form data", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        status: "validated",
        rows: 1,
        symbols: 1,
        start_date: "2024-01-02",
        end_date: "2024-01-02",
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await uploadDailyBars(new File(["symbol,trade_date\n"], "daily.csv", { type: "text/csv" }));

    const [, init] = fetchMock.mock.calls[0];
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/data/uploads",
      expect.objectContaining({ method: "POST" }),
    );
    expect(init.body).toBeInstanceOf(FormData);
    expect(init.headers).toBeUndefined();
  });
});
