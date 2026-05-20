import type { BacktestResult } from "../types";

type Props = {
  result?: BacktestResult;
};

export function Tables({ result }: Props) {
  const positions = result?.result?.positions ?? [];
  const trades = result?.result?.trades ?? [];
  const logs = result?.result?.logs ?? [];
  return (
    <section className="table-grid">
      <div>
        <h3>当前持仓</h3>
        <p>{positions.length} 条</p>
      </div>
      <div>
        <h3>交易流水</h3>
        <p>{trades.length} 条</p>
      </div>
      <div>
        <h3>运行日志</h3>
        <p>{logs.length} 条</p>
      </div>
    </section>
  );
}
