import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("renders the workbench shell", () => {
    const markup = renderToStaticMarkup(<App />);

    expect(markup).toContain("策略配置");
    expect(markup).toContain("回测结果");
  });
});
