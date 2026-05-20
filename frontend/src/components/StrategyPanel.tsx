import type { StockPool, StrategyTemplate } from "../types";

export type StrategyRunConfig = {
  strategy_id: string;
  pool_id: string;
  start_date: string;
  end_date: string;
  top_n: number;
};

type Props = {
  strategies: StrategyTemplate[];
  pools: StockPool[];
  config: StrategyRunConfig;
  onConfigChange: (config: StrategyRunConfig) => void;
  onRun: (config: StrategyRunConfig) => void;
  onUpload?: (file: File) => void;
};

export function StrategyPanel({ strategies, pools, config, onConfigChange, onRun, onUpload }: Props) {
  const updateConfig = (updates: Partial<StrategyRunConfig>) => {
    onConfigChange({ ...config, ...updates });
  };

  return (
    <aside className="control-panel">
      <h2>策略配置</h2>
      <label>
        策略模板
        <select aria-label="策略模板" value={config.strategy_id} onChange={(event) => updateConfig({ strategy_id: event.currentTarget.value })}>
          {strategies.map((strategy) => (
            <option key={strategy.strategy_id} value={strategy.strategy_id}>
              {strategy.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        股票池
        <select aria-label="股票池" value={config.pool_id} onChange={(event) => updateConfig({ pool_id: event.currentTarget.value })}>
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
          <input
            aria-label="开始日期"
            type="date"
            value={config.start_date}
            onChange={(event) => updateConfig({ start_date: event.currentTarget.value })}
          />
          <input
            aria-label="结束日期"
            type="date"
            value={config.end_date}
            onChange={(event) => updateConfig({ end_date: event.currentTarget.value })}
          />
        </span>
      </label>
      <label>
        持仓数量
        <input
          aria-label="持仓数量"
          type="number"
          value={config.top_n}
          min={1}
          onChange={(event) => {
            const topN = Number(event.currentTarget.value);
            updateConfig({ top_n: Number.isFinite(topN) && topN > 0 ? topN : 1 });
          }}
        />
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
      <button type="button" onClick={() => onRun(config)}>
        运行回测
      </button>
    </aside>
  );
}
