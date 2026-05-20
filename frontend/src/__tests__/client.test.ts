import { describe, expect, it, vi } from "vitest";
import { fetchStrategies } from "../api/client";

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
});
