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

function rowSymbol(row: Record<string, unknown>) {
  return stringValue(row.symbol);
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

function displayedSymbol(result?: BacktestResult) {
  const firstTradeSymbol = rowSymbol(result?.result?.trades?.[0] ?? {});
  const firstBarSymbol = rowSymbol(result?.result?.price_bars?.[0] ?? {});
  return firstTradeSymbol ?? firstBarSymbol;
}

function tradePoints(result?: BacktestResult, symbol?: string) {
  return (result?.result?.trades ?? [])
    .filter((row) => !symbol || rowSymbol(row) === symbol)
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

function priceBars(result?: BacktestResult, symbol?: string) {
  const bars = result?.result?.price_bars ?? [];
  return bars
    .filter((row) => !symbol || rowSymbol(row) === symbol)
    .map((row, index) => {
      const open = numberValue(row.open);
      const high = numberValue(row.high);
      const low = numberValue(row.low);
      const close = numberValue(row.close);
      if (open === undefined || high === undefined || low === undefined || close === undefined) return undefined;
      return {
        date: rowDate(row, String(index + 1)),
        open,
        high,
        low,
        close,
      };
    })
    .filter((bar): bar is { date: string; open: number; high: number; low: number; close: number } => Boolean(bar));
}

export function Charts({ result }: Props) {
  const equity = equityPoints(result);
  const drawdown = drawdownPoints(equity);
  const symbol = displayedSymbol(result);
  const trades = tradePoints(result, symbol);
  const bars = priceBars(result, symbol);
  const hasEquity = equity.length > 0;
  const hasPriceBars = bars.length > 0;
  const scaledEquity = scale(equity);
  const scaledDrawdown = scale(drawdown.length ? drawdown : [{ date: "", value: 0 }]);
  const priceScaleInput = bars.flatMap((bar) => [
    { date: bar.date, value: bar.high },
    { date: bar.date, value: bar.low },
  ]);
  const scaledPrices = scale(priceScaleInput.length ? priceScaleInput : [{ date: "", value: 0 }]);
  const priceY = (value: number) => {
    const values = priceScaleInput.map((point) => point.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const spread = max - min || 1;
    return HEIGHT - PADDING - ((value - min) / spread) * (HEIGHT - PADDING * 2);
  };
  const xStep = bars.length > 1 ? (WIDTH - PADDING * 2) / (bars.length - 1) : 0;
  const tradeDateToPoint = new Map(
    trades.map((trade) => [trade.date, { ...trade, y: priceY(trade.value) }]),
  );

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
        {hasPriceBars ? (
          <svg aria-label="价格与买卖点" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img">
            <line className="axis-line" x1={PADDING} y1={HEIGHT - PADDING} x2={WIDTH - PADDING} y2={HEIGHT - PADDING} />
            <line className="axis-line" x1={PADDING} y1={PADDING} x2={PADDING} y2={HEIGHT - PADDING} />
            <path
              data-series="price"
              className="price-line"
              d={pathFor(scaledPrices.filter((_, index) => index % 2 === 0))}
            />
            {bars.map((bar, index) => {
              const x = PADDING + index * xStep;
              const candleWidth = Math.max(4, Math.min(10, xStep * 0.45 || 8));
              const openY = priceY(bar.open);
              const highY = priceY(bar.high);
              const lowY = priceY(bar.low);
              const closeY = priceY(bar.close);
              const marker = tradeDateToPoint.get(bar.date);
              return (
                <g key={`${bar.date}-${index}`}>
                  <line data-candle="wick" className="candle-wick" x1={x} x2={x} y1={highY} y2={lowY} />
                  <rect
                    data-candle="body"
                    className={bar.close >= bar.open ? "candle-up" : "candle-down"}
                    x={x - candleWidth / 2}
                    y={Math.min(openY, closeY)}
                    width={candleWidth}
                    height={Math.max(Math.abs(openY - closeY), 2)}
                  />
                  {marker ? (
                    <circle
                      data-marker={marker.side.includes("sell") ? "sell" : "buy"}
                      className={marker.side.includes("sell") ? "sell-marker" : "buy-marker"}
                      cx={x}
                      cy={marker.y}
                      r={5}
                    />
                  ) : null}
                </g>
              );
            })}
            <text x={PADDING} y={18}>
              K线 / 买卖点
            </text>
          </svg>
        ) : (
          "运行回测后显示K线买卖点"
        )}
      </div>
    </section>
  );
}
