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
      <h3>{title}</h3>
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
  const positions = result?.result?.positions ?? [];
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
