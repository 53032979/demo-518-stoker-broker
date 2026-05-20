type Props = {
  metrics?: Record<string, number>;
};

function percent(value?: number) {
  return typeof value === "number" ? `${(value * 100).toFixed(2)}%` : "--";
}

function number(value?: number) {
  return typeof value === "number" ? value.toFixed(2) : "--";
}

export function ResultSummary({ metrics }: Props) {
  return (
    <div className="metric-grid">
      <article>
        <span>总收益</span>
        <strong>{percent(metrics?.total_return)}</strong>
      </article>
      <article>
        <span>年化收益</span>
        <strong>{percent(metrics?.annual_return)}</strong>
      </article>
      <article>
        <span>最大回撤</span>
        <strong>{percent(metrics?.max_drawdown)}</strong>
      </article>
      <article>
        <span>夏普</span>
        <strong>{number(metrics?.sharpe)}</strong>
      </article>
      <article>
        <span>胜率</span>
        <strong>{percent(metrics?.win_rate)}</strong>
      </article>
    </div>
  );
}
