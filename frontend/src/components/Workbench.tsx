import { useEffect, useRef, useState } from "react";
import { createPool, fetchPools, fetchStrategies, runBacktest, uploadDailyBars } from "../api/client";
import type { BacktestResult, StockPool, StrategyParameters, StrategyTemplate } from "../types";
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
  parameters: { top_n: 2, rebalance: "monthly", weighting: "equal" },
  costs: {
    commission_rate: 0.0003,
    stamp_tax_rate: 0.001,
    slippage_bps: 5,
    min_lot_size: 100,
  },
};

const FALLBACK_STRATEGIES: StrategyTemplate[] = [
  {
    strategy_id: FALLBACK_STRATEGY_ID,
    name: "动量 Top N",
    category: "momentum",
    description: "",
    parameter_schema: {
      type: "object",
      properties: {
        top_n: { type: "integer", title: "持仓数量", minimum: 1 },
        rebalance: { type: "string", title: "调仓频率", enum: ["weekly", "monthly"] },
        weighting: { type: "string", title: "权重方式", enum: ["equal", "score"] },
      },
    },
    default_parameters: { top_n: 2, rebalance: "monthly", weighting: "equal" },
    required_fields: [],
  },
];

const FALLBACK_POOLS: StockPool[] = [
  { pool_id: FALLBACK_POOL_ID, name: "沪深300", pool_type: "index", symbols: ["000001.SZ"] },
];

function message(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function mergePool(pools: StockPool[], pool: StockPool) {
  const exists = pools.some((candidate) => candidate.pool_id === pool.pool_id);
  return exists ? pools.map((candidate) => (candidate.pool_id === pool.pool_id ? pool : candidate)) : [...pools, pool];
}

function cloneParameters(parameters: StrategyParameters): StrategyParameters {
  return JSON.parse(JSON.stringify(parameters)) as StrategyParameters;
}

function defaultsFor(strategies: StrategyTemplate[], strategyId: string) {
  return cloneParameters(strategies.find((strategy) => strategy.strategy_id === strategyId)?.default_parameters ?? {});
}

function sameParameters(left: StrategyParameters, right: StrategyParameters) {
  return JSON.stringify(left) === JSON.stringify(right);
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
  const actionSequence = useRef(0);
  const suppressLoadError = useRef(false);

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
        setConfig((currentConfig) => {
          const strategyExists = nextStrategies.some((strategy) => strategy.strategy_id === currentConfig.strategy_id);
          const strategyId = strategyExists ? currentConfig.strategy_id : nextStrategies[0]?.strategy_id ?? FALLBACK_STRATEGY_ID;
          const shouldPreserveParameters = strategyExists && !sameParameters(currentConfig.parameters, DEFAULT_CONFIG.parameters);
          return {
            ...currentConfig,
            strategy_id: strategyId,
            pool_id: nextPools.some((pool) => pool.pool_id === currentConfig.pool_id)
              ? currentConfig.pool_id
              : nextPools[0]?.pool_id ?? FALLBACK_POOL_ID,
            parameters: shouldPreserveParameters
              ? { ...defaultsFor(nextStrategies, strategyId), ...currentConfig.parameters }
              : defaultsFor(nextStrategies, strategyId),
          };
        });

        if (strategyError && poolError) {
          setLoadStatus("配置加载失败，已使用默认配置");
          setLoadError(suppressLoadError.current ? undefined : `${strategyError}；${poolError}`);
        } else if (strategyError || poolError) {
          setLoadStatus("部分配置加载失败，已使用默认配置");
          setLoadError(suppressLoadError.current ? undefined : strategyError ?? poolError);
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
    const sequence = actionSequence.current + 1;
    actionSequence.current = sequence;
    setActionError(undefined);
    setActionStatus("回测运行中...");
    try {
      const backtestResult = await runBacktest({
        strategy_id: runConfig.strategy_id,
        pool_id: runConfig.pool_id,
        start_date: runConfig.start_date,
        end_date: runConfig.end_date,
        parameters: runConfig.parameters,
        costs: runConfig.costs,
      });
      if (actionSequence.current !== sequence) return;
      setResult(backtestResult);
      setActionStatus(backtestResult.status === "completed" ? "回测完成" : `回测状态：${backtestResult.status}`);
      setActionError(undefined);
      suppressLoadError.current = true;
      setLoadError(undefined);
    } catch (runError) {
      if (actionSequence.current !== sequence) return;
      setActionError(message(runError, "回测运行失败"));
      setActionStatus("回测失败");
    }
  };

  const handleUpload = async (file: File) => {
    const sequence = actionSequence.current + 1;
    actionSequence.current = sequence;
    setActionError(undefined);
    setActionStatus("正在上传数据文件...");
    try {
      const uploadResult = await uploadDailyBars(file);
      if (actionSequence.current !== sequence) return;
      if (uploadResult.pool) {
        setPools((currentPools) => mergePool(currentPools, uploadResult.pool as StockPool));
        setConfig((currentConfig) => ({ ...currentConfig, pool_id: uploadResult.pool?.pool_id ?? currentConfig.pool_id }));
      } else {
        try {
          const refreshedPools = await fetchPools();
          if (actionSequence.current !== sequence) return;
          setPools(refreshedPools.length > 0 ? refreshedPools : FALLBACK_POOLS);
        } catch {
          if (actionSequence.current !== sequence) return;
        }
      }
      setActionStatus(`上传完成：${uploadResult.rows} 行，${uploadResult.symbols} 个标的`);
      setActionError(undefined);
      suppressLoadError.current = true;
      setLoadError(undefined);
    } catch (uploadError) {
      if (actionSequence.current !== sequence) return;
      setActionError(message(uploadError, "数据上传失败"));
      setActionStatus("上传失败");
    }
  };

  const handleCreatePool = async (symbols: string[]) => {
    const sequence = actionSequence.current + 1;
    actionSequence.current = sequence;
    setActionError(undefined);
    setActionStatus("正在保存股票池...");
    try {
      const pool = await createPool({ name: "自定义股票池", symbols });
      if (actionSequence.current !== sequence) return;
      setPools((currentPools) => mergePool(currentPools, pool));
      setConfig((currentConfig) => ({ ...currentConfig, pool_id: pool.pool_id }));
      setActionStatus(`股票池已保存：${pool.symbols.length} 个标的`);
      setActionError(undefined);
      suppressLoadError.current = true;
      setLoadError(undefined);
    } catch (poolError) {
      if (actionSequence.current !== sequence) return;
      setActionError(message(poolError, "股票池保存失败"));
      setActionStatus("股票池保存失败");
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
        onCreatePool={handleCreatePool}
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
