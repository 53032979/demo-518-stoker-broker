import { useEffect, useState } from "react";
import { fetchPools, fetchStrategies, runBacktest, uploadDailyBars } from "../api/client";
import type { BacktestResult, StockPool, StrategyTemplate } from "../types";
import { Charts } from "./Charts";
import { ResultSummary } from "./ResultSummary";
import { StrategyPanel, type StrategyRunConfig } from "./StrategyPanel";
import { Tables } from "./Tables";

const FALLBACK_STRATEGY_ID = "momentum_top_n";
const FALLBACK_POOL_ID = "csi300";
const DEFAULT_CONFIG: StrategyRunConfig = {
  strategy_id: FALLBACK_STRATEGY_ID,
  pool_id: FALLBACK_POOL_ID,
  start_date: "2024-01-01",
  end_date: "2024-12-31",
  top_n: 2,
};

const FALLBACK_STRATEGIES: StrategyTemplate[] = [
  {
    strategy_id: FALLBACK_STRATEGY_ID,
    name: "动量 Top N",
    category: "momentum",
    description: "",
    parameter_schema: {},
    default_parameters: {},
    required_fields: [],
  },
];

const FALLBACK_POOLS: StockPool[] = [
  { pool_id: FALLBACK_POOL_ID, name: "沪深300", pool_type: "index", symbols: ["000001.SZ"] },
];

function message(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

export function Workbench() {
  const [strategies, setStrategies] = useState<StrategyTemplate[]>(FALLBACK_STRATEGIES);
  const [pools, setPools] = useState<StockPool[]>(FALLBACK_POOLS);
  const [config, setConfig] = useState<StrategyRunConfig>(DEFAULT_CONFIG);
  const [result, setResult] = useState<BacktestResult>();
  const [loadStatus, setLoadStatus] = useState("正在加载策略与股票池...");
  const [loadError, setLoadError] = useState<string>();
  const [actionStatus, setActionStatus] = useState<string>();
  const [actionError, setActionError] = useState<string>();

  useEffect(() => {
    let isMounted = true;

    Promise.allSettled([fetchStrategies(), fetchPools()])
      .then(([strategyResult, poolResult]) => {
        if (!isMounted) return;

        const nextStrategies =
          strategyResult.status === "fulfilled" && strategyResult.value.length > 0 ? strategyResult.value : FALLBACK_STRATEGIES;
        const nextPools = poolResult.status === "fulfilled" && poolResult.value.length > 0 ? poolResult.value : FALLBACK_POOLS;
        const strategyError =
          strategyResult.status === "fulfilled"
            ? strategyResult.value.length === 0
              ? "策略模板为空"
              : undefined
            : message(strategyResult.reason, "策略模板加载失败");
        const poolError =
          poolResult.status === "fulfilled"
            ? poolResult.value.length === 0
              ? "股票池为空"
              : undefined
            : message(poolResult.reason, "股票池加载失败");

        setStrategies(nextStrategies);
        setPools(nextPools);
        setConfig((currentConfig) => ({
          ...currentConfig,
          strategy_id: nextStrategies.some((strategy) => strategy.strategy_id === currentConfig.strategy_id)
            ? currentConfig.strategy_id
            : nextStrategies[0]?.strategy_id ?? FALLBACK_STRATEGY_ID,
          pool_id: nextPools.some((pool) => pool.pool_id === currentConfig.pool_id)
            ? currentConfig.pool_id
            : nextPools[0]?.pool_id ?? FALLBACK_POOL_ID,
        }));

        if (strategyError && poolError) {
          setLoadStatus("配置加载失败，已使用默认配置");
          setLoadError(`${strategyError}；${poolError}`);
        } else if (strategyError || poolError) {
          setLoadStatus("部分配置加载失败，已使用默认配置");
          setLoadError(strategyError ?? poolError);
        } else {
          setLoadStatus("准备就绪");
          setLoadError(undefined);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleRun = async (runConfig: StrategyRunConfig) => {
    setActionError(undefined);
    setActionStatus("回测运行中...");
    try {
      const backtestResult = await runBacktest({
        strategy_id: runConfig.strategy_id,
        pool_id: runConfig.pool_id,
        start_date: runConfig.start_date,
        end_date: runConfig.end_date,
        parameters: { top_n: runConfig.top_n, rebalance: "monthly", weighting: "equal" },
        costs: {
          commission_rate: 0.0003,
          stamp_tax_rate: 0.001,
          slippage_bps: 5,
          min_lot_size: 100,
        },
      });
      setResult(backtestResult);
      setActionStatus(backtestResult.status === "completed" ? "回测完成" : `回测状态：${backtestResult.status}`);
      setActionError(undefined);
      setLoadError(undefined);
    } catch (runError) {
      setActionError(message(runError, "回测运行失败"));
      setActionStatus("回测失败");
    }
  };

  const handleUpload = async (file: File) => {
    setActionError(undefined);
    setActionStatus("正在上传数据文件...");
    try {
      const uploadResult = await uploadDailyBars(file);
      setActionStatus(`上传完成：${uploadResult.rows} 行，${uploadResult.symbols} 个标的`);
      setActionError(undefined);
      setLoadError(undefined);
    } catch (uploadError) {
      setActionError(message(uploadError, "数据上传失败"));
      setActionStatus("上传失败");
    }
  };

  const status = actionStatus ?? loadStatus;
  const error = actionError ?? loadError;

  return (
    <section className="workbench">
      <StrategyPanel
        strategies={strategies}
        pools={pools}
        config={config}
        onConfigChange={setConfig}
        onRun={handleRun}
        onUpload={handleUpload}
      />
      <section className="result-panel">
        <header className="result-header">
          <h2>回测结果</h2>
          <p className="status-line">{status}</p>
        </header>
        {error ? <p className="error-text">{error}</p> : null}
        <ResultSummary metrics={result?.result?.metrics} />
        <Charts result={result} />
        <Tables result={result} />
      </section>
    </section>
  );
}
