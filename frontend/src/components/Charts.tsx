import type { BacktestResult } from "../types";

type Props = {
  result?: BacktestResult;
};

export function Charts({ result }: Props) {
  const hasResult = result?.result?.equity_curve?.length;
  return (
    <section className="chart-grid">
      <div className="chart-box">{hasResult ? "资金曲线 / 回撤曲线" : "运行回测后显示资金曲线"}</div>
      <div className="chart-box">{hasResult ? "K线 + 买卖点" : "运行回测后显示K线买卖点"}</div>
    </section>
  );
}
