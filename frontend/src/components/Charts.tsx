import type { BacktestResult } from "../types";

type Props = {
  result?: BacktestResult;
};

type Point = {
  date: string;
  value: number;
};

const WIDTH = 520;
const HEIGHT = 220;
const PADDING = 28;

function numberValue(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function stringValue(value: unknown) {
  return typeof value === "string" ? value : undefined;
}

function rowDate(row: Record<string, unknown>, fallback: string) {
  return stringValue(row.trade_date) ?? stringValue(row.date) ?? stringValue(row.datetime) ?? fallback;
}

function rowEquity(row: Record<string, unknown>) {
  return numberValue(row.equity) ?? numberValue(row.nav) ?? numberValue(row.portfolio_value) ?? numberValue(row.value);
}

function rowPrice(row: Record<string, unknown>) {
  return numberValue(row.price) ?? numberValue(row.close) ?? numberValue(row.trade_price) ?? numberValue(row.value);
}

function scale(points: Point[]) {
  const values = points.map((point) => point.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const spread = max - min || 1;
  const xStep = points.length > 1 ? (WIDTH - PADDING * 2) / (points.length - 1) : 0;
  return points.map((point, index) => ({
    ...point,
    x: PADDING + index * xStep,
    y: HEIGHT - PADDING - ((point.value - min) / spread) * (HEIGHT - PADDING * 2),
  }));
}

function pathFor(points: ReturnType<typeof scale>) {
  return points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(" ");
}

function equityPoints(result?: BacktestResult) {
  return (result?.result?.equity_curve ?? [])
    .map((row, index) => {
      const value = rowEquity(row);
      return value === undefined ? undefined : { date: rowDate(row, String(index + 1)), value };
    })
    .filter((point): point is Point => Boolean(point));
}

function drawdownPoints(points: Point[]) {
  let peak = points[0]?.value ?? 0;
  return points.map((point) => {
    peak = Math.max(peak, point.value);
    return { date: point.date, value: peak === 0 ? 0 : (point.value - peak) / peak };
  });
}

function tradePoints(result?: BacktestResult) {
  return (result?.result?.trades ?? [])
    .map((row, index) => {
      const value = rowPrice(row);
      return value === undefined
        ? undefined
        : {
            date: rowDate(row, String(index + 1)),
            value,
            side: String(row.side ?? row.action ?? "").toLowerCase(),
          };
    })
    .filter((point): point is Point & { side: string } => Boolean(point));
}

export function Charts({ result }: Props) {
  const equity = equityPoints(result);
  const drawdown = drawdownPoints(equity);
  const trades = tradePoints(result);
  const hasEquity = equity.length > 0;
  const hasTrades = trades.length > 0;
  const scaledEquity = scale(equity);
  const scaledDrawdown = scale(drawdown.length ? drawdown : [{ date: "", value: 0 }]);
  const scaledTrades = scale(trades.length ? trades : [{ date: "", value: 0 }]);

  return (
    <section className="chart-grid">
      <div className="chart-box">
        {hasEquity ? (
          <svg aria-label="资金曲线与回撤" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img">
            <line className="axis-line" x1={PADDING} y1={HEIGHT - PADDING} x2={WIDTH - PADDING} y2={HEIGHT - PADDING} />
            <line className="axis-line" x1={PADDING} y1={PADDING} x2={PADDING} y2={HEIGHT - PADDING} />
            <path data-series="drawdown" className="drawdown-line" d={pathFor(scaledDrawdown)} />
            <path data-series="equity" className="equity-line" d={pathFor(scaledEquity)} />
            <text x={PADDING} y={18}>
              资金 / 回撤
            </text>
          </svg>
        ) : (
          "运行回测后显示资金曲线"
        )}
      </div>
      <div className="chart-box">
        {hasTrades ? (
          <svg aria-label="价格与买卖点" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img">
            <line className="axis-line" x1={PADDING} y1={HEIGHT - PADDING} x2={WIDTH - PADDING} y2={HEIGHT - PADDING} />
            <line className="axis-line" x1={PADDING} y1={PADDING} x2={PADDING} y2={HEIGHT - PADDING} />
            <path data-series="price" className="price-line" d={pathFor(scaledTrades)} />
            {scaledTrades.map((point, index) => {
              const marker = trades[index]?.side.includes("sell") ? "sell" : "buy";
              return (
                <circle
                  key={`${point.date}-${index}`}
                  data-marker={marker}
                  className={marker === "sell" ? "sell-marker" : "buy-marker"}
                  cx={point.x}
                  cy={point.y}
                  r={5}
                />
              );
            })}
            <text x={PADDING} y={18}>
              价格 / 买卖点
            </text>
          </svg>
        ) : (
          "运行回测后显示K线买卖点"
        )}
      </div>
    </section>
  );
}
