import { useState } from "react";
import type { StockPool, StrategyParameterSchema, StrategyParameterValue, StrategyParameters, StrategyTemplate } from "../types";

export type StrategyRunConfig = {
  strategy_id: string;
  pool_id: string;
  start_date: string;
  end_date: string;
  parameters: StrategyParameters;
};

type Props = {
  strategies: StrategyTemplate[];
  pools: StockPool[];
  config: StrategyRunConfig;
  onConfigChange: (config: StrategyRunConfig) => void;
  onRun: (config: StrategyRunConfig) => void;
  onUpload?: (file: File) => void;
  onCreatePool?: (symbols: string[]) => void;
};

function cloneParameters(parameters: StrategyParameters): StrategyParameters {
  return JSON.parse(JSON.stringify(parameters)) as StrategyParameters;
}

function selectedStrategy(strategies: StrategyTemplate[], strategyId: string) {
  return strategies.find((strategy) => strategy.strategy_id === strategyId) ?? strategies[0];
}

function schemaProperties(schema: StrategyParameterSchema | undefined) {
  return schema?.properties ?? {};
}

function parameterLabel(name: string, schema: StrategyParameterSchema) {
  return schema.title ?? name;
}

function effectiveParameters(strategy: StrategyTemplate | undefined, config: StrategyRunConfig): StrategyParameters {
  return {
    ...(strategy?.default_parameters ?? {}),
    ...config.parameters,
  };
}

function coerceNumber(value: string, schema: StrategyParameterSchema) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return schema.minimum ?? 0;
  const normalized = schema.type === "integer" ? Math.floor(parsed) : parsed;
  if (typeof schema.minimum === "number" && normalized < schema.minimum) return schema.minimum;
  if (typeof schema.maximum === "number" && normalized > schema.maximum) return schema.maximum;
  return normalized;
}

function serializeSymbols(value: string) {
  return value
    .split(/[\s,;]+/)
    .map((symbol) => symbol.trim())
    .filter(Boolean);
}

function parameterValue(parameters: StrategyParameters, name: string): string | number {
  const value = parameters[name];
  return typeof value === "number" || typeof value === "string" ? value : "";
}

function nestedParameterValue(parameters: StrategyParameters, objectName: string, name: string): string | number {
  const objectValue = parameters[objectName];
  const value = typeof objectValue === "object" && objectValue ? objectValue[name] : undefined;
  return typeof value === "number" || typeof value === "string" ? value : "";
}

export function StrategyPanel({ strategies, pools, config, onConfigChange, onRun, onUpload, onCreatePool }: Props) {
  const [customSymbols, setCustomSymbols] = useState("");
  const strategy = selectedStrategy(strategies, config.strategy_id);
  const parameters = effectiveParameters(strategy, config);

  const updateConfig = (updates: Partial<StrategyRunConfig>) => {
    onConfigChange({ ...config, ...updates });
  };

  const updateParameter = (name: string, value: StrategyParameterValue) => {
    onConfigChange({
      ...config,
      parameters: {
        ...parameters,
        [name]: value,
      },
    });
  };

  const updateNestedParameter = (objectName: string, name: string, value: string | number | boolean | null) => {
    const objectValue = parameters[objectName];
    const nextObject = typeof objectValue === "object" && objectValue ? { ...objectValue } : {};
    nextObject[name] = value;
    updateParameter(objectName, nextObject);
  };

  const handleStrategyChange = (strategyId: string) => {
    const nextStrategy = selectedStrategy(strategies, strategyId);
    onConfigChange({
      ...config,
      strategy_id: strategyId,
      parameters: cloneParameters(nextStrategy?.default_parameters ?? {}),
    });
  };

  const handleCreatePool = () => {
    const symbols = serializeSymbols(customSymbols);
    if (symbols.length > 0 && onCreatePool) {
      onCreatePool(symbols);
      setCustomSymbols("");
    }
  };

  const renderParameter = (name: string, schema: StrategyParameterSchema) => {
    const label = parameterLabel(name, schema);
    if (schema.type === "object") {
      const nestedProperties = schemaProperties(schema);
      return (
        <fieldset key={name} className="parameter-group">
          <legend>{label}</legend>
          {Object.entries(nestedProperties).map(([nestedName, nestedSchema]) => (
            <label key={nestedName}>
              {parameterLabel(nestedName, nestedSchema)}
              <input
                aria-label={parameterLabel(nestedName, nestedSchema)}
                type="number"
                value={nestedParameterValue(parameters, name, nestedName)}
                step={nestedSchema.type === "integer" ? 1 : "any"}
                min={nestedSchema.minimum}
                max={nestedSchema.maximum}
                onChange={(event) => updateNestedParameter(name, nestedName, coerceNumber(event.currentTarget.value, nestedSchema))}
              />
            </label>
          ))}
        </fieldset>
      );
    }

    if (schema.type === "string" && schema.enum?.length) {
      return (
        <label key={name}>
          {label}
          <select
            aria-label={label}
            value={String(parameterValue(parameters, name))}
            onChange={(event) => updateParameter(name, event.currentTarget.value)}
          >
            {schema.enum.map((option) => (
              <option key={String(option)} value={String(option)}>
                {String(option)}
              </option>
            ))}
          </select>
        </label>
      );
    }

    if (schema.type === "integer" || schema.type === "number") {
      return (
        <label key={name}>
          {label}
          <input
            aria-label={label}
            type="number"
            value={parameterValue(parameters, name)}
            min={schema.minimum}
            max={schema.maximum}
            step={schema.type === "integer" ? 1 : "any"}
            onChange={(event) => updateParameter(name, coerceNumber(event.currentTarget.value, schema))}
          />
        </label>
      );
    }

    return (
      <label key={name}>
        {label}
        <input
          aria-label={label}
          type="text"
          value={String(parameterValue(parameters, name))}
          onChange={(event) => updateParameter(name, event.currentTarget.value)}
        />
      </label>
    );
  };

  return (
    <aside className="control-panel">
      <h2>策略配置</h2>
      <label>
        策略模板
        <select aria-label="策略模板" value={config.strategy_id} onChange={(event) => handleStrategyChange(event.currentTarget.value)}>
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
      {Object.entries(schemaProperties(strategy?.parameter_schema)).map(([name, schema]) => renderParameter(name, schema))}
      <div className="custom-pool-row">
        <label>
          自定义股票池标的
          <textarea
            aria-label="自定义股票池标的"
            rows={3}
            value={customSymbols}
            onChange={(event) => setCustomSymbols(event.currentTarget.value)}
          />
        </label>
        <button type="button" className="secondary-button" onClick={handleCreatePool}>
          保存股票池
        </button>
      </div>
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
