import { useEffect, useState } from "react";
import { fetchPools, fetchStrategies, runBacktest, uploadDailyBars } from "../api/client";
import type { BacktestResult, StockPool, StrategyTemplate } from "../types";
import { Charts } from "./Charts";
import { ResultSummary } from "./ResultSummary";
import { StrategyPanel } from "./StrategyPanel";
import { Tables } from "./Tables";

export function Workbench() {
  const [strategies, setStrategies] = useState<StrategyTemplate[]>([]);
  const [pools, setPools] = useState<StockPool[]>([]);
  const [result, setResult] = useState<BacktestResult>();
  const [status, setStatus] = useState("正在加载策略与股票池...");
  const [error, setError] = useState<string>();

  useEffect(() => {
    let isMounted = true;

    Promise.all([fetchStrategies(), fetchPools()])
      .then(([loadedStrategies, loadedPools]) => {
        if (!isMounted) return;
        setStrategies(loadedStrategies);
        setPools(loadedPools);
        setStatus("准备就绪");
      })
      .catch((loadError: unknown) => {
        if (!isMounted) return;
        setError(loadError instanceof Error ? loadError.message : "加载策略与股票池失败");
        setStatus("加载失败");
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const handleRun = async () => {
    setError(undefined);
    setStatus("回测运行中...");
    try {
      const backtestResult = await runBacktest({
        strategy_id: strategies[0]?.strategy_id ?? "momentum_top_n",
        pool_id: pools[0]?.pool_id ?? "csi300",
        start_date: "2024-01-01",
        end_date: "2024-12-31",
        parameters: { top_n: 2, rebalance: "monthly", weighting: "equal" },
        costs: {
          commission_rate: 0.0003,
          stamp_tax_rate: 0.001,
          slippage_bps: 5,
          min_lot_size: 100,
        },
      });
      setResult(backtestResult);
      setStatus(backtestResult.status === "completed" ? "回测完成" : `回测状态：${backtestResult.status}`);
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "回测运行失败");
      setStatus("回测失败");
    }
  };

  const handleUpload = async (file: File) => {
    setError(undefined);
    setStatus("正在上传数据文件...");
    try {
      const uploadResult = await uploadDailyBars(file);
      setStatus(`上传完成：${uploadResult.rows} 行，${uploadResult.symbols} 个标的`);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "数据上传失败");
      setStatus("上传失败");
    }
  };

  return (
    <section className="workbench">
      <StrategyPanel strategies={strategies} pools={pools} onRun={handleRun} onUpload={handleUpload} />
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
