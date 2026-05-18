import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("renders the lab heading", () => {
    const markup = renderToStaticMarkup(<App />);

    expect(markup).toContain("A股量化策略实验室");
  });
});
