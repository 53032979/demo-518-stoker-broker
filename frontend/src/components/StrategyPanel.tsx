import type { StockPool, StrategyTemplate } from "../types";

type Props = {
  strategies: StrategyTemplate[];
  pools: StockPool[];
  onRun: () => void;
  onUpload?: (file: File) => void;
};

export function StrategyPanel({ strategies, pools, onRun, onUpload }: Props) {
  return (
    <aside className="control-panel">
      <h2>策略配置</h2>
      <label>
        策略模板
        <select aria-label="策略模板">
          {strategies.map((strategy) => (
            <option key={strategy.strategy_id} value={strategy.strategy_id}>
              {strategy.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        股票池
        <select aria-label="股票池">
          {pools.map((pool) => (
            <option key={pool.pool_id} value={pool.pool_id}>
              {pool.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        回测区间
        <span className="date-row">
          <input aria-label="开始日期" type="date" defaultValue="2024-01-01" />
          <input aria-label="结束日期" type="date" defaultValue="2024-12-31" />
        </span>
      </label>
      <label>
        持仓数量
        <input aria-label="持仓数量" type="number" defaultValue={20} min={1} />
      </label>
      <label>
        本地数据文件
        <input
          aria-label="本地数据文件"
          type="file"
          accept=".csv,.parquet"
          onChange={(event) => {
            const file = event.currentTarget.files?.[0];
            if (file && onUpload) onUpload(file);
          }}
        />
      </label>
      <button type="button" onClick={onRun}>
        运行回测
      </button>
    </aside>
  );
}
