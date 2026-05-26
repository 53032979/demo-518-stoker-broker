type Props = {
  metrics?: Record<string, number>;
};

function percent(value?: number) {
  return typeof value === "number" ? `${(value * 100).toFixed(2)}%` : "--";
}

function number(value?: number) {
  return typeof value === "number" ? value.toFixed(2) : "--";
}

function tone(value: number | undefined, positiveIsGood = true) {
  if (typeof value !== "number") return "metric-neutral";
  if (value === 0) return "metric-neutral";
  const isPositive = value > 0;
  return isPositive === positiveIsGood ? "metric-positive" : "metric-negative";
}

export function ResultSummary({ metrics }: Props) {
  const cards = [
    {
      label: "总收益",
      caption: "Portfolio return",
      value: percent(metrics?.total_return),
      tone: tone(metrics?.total_return),
    },
    {
      label: "年化收益",
      caption: "Annualized",
      value: percent(metrics?.annual_return),
      tone: tone(metrics?.annual_return),
    },
    {
      label: "最大回撤",
      caption: "Risk drawdown",
      value: percent(metrics?.max_drawdown),
      tone: tone(metrics?.max_drawdown),
    },
    {
      label: "夏普",
      caption: "Risk adjusted",
      value: number(metrics?.sharpe),
      tone: "metric-accent",
    },
    {
      label: "胜率",
      caption: "Winning trades",
      value: percent(metrics?.win_rate),
      tone: tone(metrics?.win_rate === undefined ? undefined : metrics.win_rate - 0.5),
    },
  ];

  return (
    <div className="metric-grid">
      {cards.map((card) => (
        <article key={card.label} className={`metric-card ${card.tone}`}>
          <span>{card.label}</span>
          <strong>{card.value}</strong>
          <small>{card.caption}</small>
        </article>
      ))}
    </div>
  );
}
