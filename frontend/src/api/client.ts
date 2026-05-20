import type { BacktestPayload, BacktestResult, CreatePoolPayload, StockPool, StrategyTemplate, UploadDailyBarsResult } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const { headers, ...requestInit } = init ?? {};
  const requestHeaders = new Headers(headers);
  if (!requestHeaders.has("Content-Type")) {
    requestHeaders.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...requestInit,
    headers: requestHeaders,
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

export function createPool(payload: CreatePoolPayload): Promise<StockPool> {
  return requestJson<StockPool>("/pools", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function runBacktest(payload: BacktestPayload): Promise<BacktestResult> {
  return requestJson<BacktestResult>("/backtests", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function uploadDailyBars(file: File): Promise<UploadDailyBarsResult> {
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
