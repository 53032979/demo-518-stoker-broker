export type StrategyTemplate = {
  strategy_id: string;
  name: string;
  category: string;
  description: string;
  parameter_schema: Record<string, unknown>;
  default_parameters: Record<string, unknown>;
  required_fields: string[];
};

export type StockPool = {
  pool_id: string;
  name: string;
  pool_type: "index" | "custom";
  symbols: string[];
};

export type BacktestPayload = {
  strategy_id: string;
  pool_id: string;
  start_date: string;
  end_date: string;
  parameters: Record<string, unknown>;
  costs: {
    commission_rate: number;
    stamp_tax_rate: number;
    slippage_bps: number;
    min_lot_size: number;
  };
};

export type BacktestResult = {
  run_id: string;
  status: "completed" | "failed" | "running" | "queued";
  result?: {
    metrics: Record<string, number>;
    equity_curve: Array<Record<string, number | string>>;
    positions: Array<Record<string, number | string>>;
    trades: Array<Record<string, number | string>>;
    logs: string[];
  };
};
