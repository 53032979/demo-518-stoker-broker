import type { BacktestResult } from "../types";

type Props = {
  result?: BacktestResult;
};

function columns(rows: Array<Record<string, unknown>>, preferred: string[]) {
  const found = new Set<string>();
  rows.forEach((row) => Object.keys(row).forEach((key) => found.add(key)));
  const ordered = preferred.filter((key) => found.has(key));
  const rest = [...found].filter((key) => !ordered.includes(key));
  return [...ordered, ...rest].slice(0, 6);
}

function formatCell(value: unknown) {
  if (value === null || value === undefined || value === "") return "--";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(4).replace(/0+$/, "").replace(/\.$/, "");
  return String(value);
}

function finalEquityDate(result?: BacktestResult) {
  const dates = (result?.result?.equity_curve ?? [])
    .map((row) => (typeof row.trade_date === "string" ? row.trade_date : undefined))
    .filter((date): date is string => Boolean(date))
    .sort();
  return dates[dates.length - 1];
}

function currentRows(rows: Array<Record<string, unknown>>, finalDate?: string) {
  if (finalDate) {
    return rows.filter((row) => String(row.trade_date) === finalDate);
  }
  const datedRows = rows.filter((row) => typeof row.trade_date === "string");
  if (!datedRows.length) return rows;
  const sortedDates = datedRows
    .map((row) => String(row.trade_date))
    .sort();
  const latestDate = sortedDates[sortedDates.length - 1];
  return rows.filter((row) => String(row.trade_date) === latestDate);
}

function DataTable({
  title,
  rows,
  preferredColumns,
}: {
  title: string;
  rows: Array<Record<string, unknown>>;
  preferredColumns: string[];
}) {
  const visibleColumns = columns(rows, preferredColumns);
  return (
    <div className="table-card">
      <header className="table-card-header">
        <h3>{title}</h3>
        <span>{rows.length === 1 ? "1 row" : `${rows.length} rows`}</span>
      </header>
      <div className="table-scroll">
        <table aria-label={title}>
          <thead>
            <tr>
              {visibleColumns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length ? (
              rows.map((row, index) => (
                <tr key={index}>
                  {visibleColumns.map((column) => (
                    <td key={column}>{formatCell(row[column])}</td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={Math.max(visibleColumns.length, 1)}>暂无数据</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function Tables({ result }: Props) {
  const positions = currentRows(result?.result?.positions ?? [], finalEquityDate(result));
  const trades = result?.result?.trades ?? [];
  const logs = result?.result?.logs ?? [];
  return (
    <section className="table-grid">
      <DataTable title="当前持仓" rows={positions} preferredColumns={["symbol", "name", "weight", "quantity", "market_value", "cost"]} />
      <DataTable title="交易流水" rows={trades} preferredColumns={["trade_date", "symbol", "side", "price", "quantity", "amount"]} />
      <DataTable title="运行日志" rows={logs.map((entry, index) => ({ "#": index + 1, message: entry }))} preferredColumns={["#", "message"]} />
    </section>
  );
}
