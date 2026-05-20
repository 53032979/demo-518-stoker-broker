export type StrategyParameterValue = string | number | boolean | null | Record<string, string | number | boolean | null>;

export type StrategyParameters = Record<string, StrategyParameterValue>;

export type StrategyParameterSchema = {
  type?: string;
  title?: string;
  description?: string;
  enum?: Array<string | number>;
  minimum?: number;
  maximum?: number;
  properties?: Record<string, StrategyParameterSchema>;
};

export type StrategyTemplate = {
  strategy_id: string;
  name: string;
  category: string;
  description: string;
  parameter_schema: StrategyParameterSchema;
  default_parameters: StrategyParameters;
  required_fields: string[];
};

export type StockPool = {
  pool_id: string;
  name: string;
  pool_type: "index" | "custom";
  symbols: string[];
  source?: string;
};

export type BacktestPayload = {
  strategy_id: string;
  pool_id: string;
  start_date: string;
  end_date: string;
  parameters: StrategyParameters;
  costs: {
    commission_rate: number;
    stamp_tax_rate: number;
    slippage_bps: number;
    min_lot_size: number;
  };
};

export type BacktestRowValue = number | string | null;

export type BacktestResult = {
  run_id: string;
  status: "completed" | "failed" | "running" | "queued";
  result?: {
    metrics: Record<string, number>;
    equity_curve: Array<Record<string, BacktestRowValue>>;
    positions: Array<Record<string, BacktestRowValue>>;
    trades: Array<Record<string, BacktestRowValue>>;
    logs: string[];
  };
};

export type UploadDailyBarsResult = {
  status: string;
  rows: number;
  symbols: number;
  start_date: string;
  end_date: string;
  pool?: StockPool;
};

export type CreatePoolPayload = {
  name?: string;
  symbols: string[];
};
