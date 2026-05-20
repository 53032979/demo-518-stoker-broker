import type { BacktestPayload, BacktestResult, StockPool, StrategyTemplate } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(error.message ?? "API request failed");
  }
  return response.json() as Promise<T>;
}

export function fetchStrategies(): Promise<StrategyTemplate[]> {
  return requestJson<StrategyTemplate[]>("/strategies");
}

export function fetchPools(): Promise<StockPool[]> {
  return requestJson<StockPool[]>("/pools");
}

export function runBacktest(payload: BacktestPayload): Promise<BacktestResult> {
  return requestJson<BacktestResult>("/backtests", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function uploadDailyBars(file: File): Promise<{
  status: string;
  rows: number;
  symbols: number;
  start_date: string;
  end_date: string;
}> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE}/data/uploads`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(error.message ?? "Upload failed");
  }
  return response.json();
}
