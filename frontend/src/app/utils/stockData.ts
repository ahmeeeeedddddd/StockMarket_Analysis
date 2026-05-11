export interface StockData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume?: number;
  high?: number;
  low?: number;
  vwap?: number;
  ema?: number;
}

export interface Candle {
  time: string | number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  vwap?: number;
  trade_count?: number;
  anomaly_type?: string | null;
  severity?: 'normal' | 'mild' | 'critical';
  anomaly_value?: number | null;
  ma?: number;
  std?: number;
  upper?: number;
  lower?: number;
  z_score?: number;
}

export interface Alert {
  time: string | number;
  symbol: string;
  alert_type: string;
  severity: 'normal' | 'mild' | 'critical' | string;
  message: string;
  trigger_price: number;
  expected_value?: number;
  actual_value?: number;
}

export interface HeatmapData {
  symbol: string;
  timeline: { time: string; severity: 'normal' | 'mild' | 'critical' }[];
}

export interface DeepDiveData {
  symbol: string;
  candles: Candle[];
  historical: Candle[];
}

const API_BASE = 'http://localhost:8000/api';

export async function fetchLatestPrice(symbol: string): Promise<StockData | null> {
  try {
    const res = await fetch(`${API_BASE}/price/${symbol}`);
    if (!res.ok) return null;
    const data = await res.json();
    return {
      symbol,
      price: data.price,
      change: 0, // Backend doesn't return these directly, might need calculation
      changePercent: 0,
    };
  } catch (error) {
    console.error("Failed to fetch price", error);
    return null;
  }
}

export async function fetchCandles(symbol: string, windowSec: number, limit: number = 60): Promise<Candle[]> {
  try {
    const res = await fetch(`${API_BASE}/candlesticks?symbol=${symbol}&window_sec=${windowSec}&limit=${limit}`);
    if (!res.ok) return [];
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch candles", error);
    return [];
  }
}

export async function fetchAlerts(symbol?: string, limit: number = 50): Promise<Alert[]> {
  try {
    const url = symbol && symbol !== 'ALL' 
        ? `${API_BASE}/alerts?symbol=${symbol}&limit=${limit}`
        : `${API_BASE}/alerts?limit=${limit}`;
    const res = await fetch(url);
    if (!res.ok) return [];
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch alerts", error);
    return [];
  }
}

export function calculateEMA(candles: Candle[], period = 20): number[] {
  const emas: number[] = [];
  if (candles.length === 0) return emas;
  
  const multiplier = 2 / (period + 1);
  let ema = candles.slice(0, period).reduce((sum, c) => sum + c.close, 0) / Math.min(period, candles.length);

  for (let i = 0; i < candles.length; i++) {
    if (i < period) {
      emas.push(ema);
    } else {
      ema = (candles[i].close - ema) * multiplier + ema;
      emas.push(ema);
    }
  }

  return emas;
}

export function isMarketOpen(): boolean {
  const now = new Date();
  const day = now.getDay();
  const hours = now.getHours();
  const minutes = now.getMinutes();
  const totalMinutes = hours * 60 + minutes;

  const isWeekday = day >= 1 && day <= 5;
  const marketOpen = 9 * 60 + 30;
  const marketClose = 16 * 60;

  return isWeekday && totalMinutes >= marketOpen && totalMinutes < marketClose;
}

export async function fetchHeatmap(): Promise<HeatmapData[]> {
  try {
    const res = await fetch(`${API_BASE}/heatmap`);
    if (!res.ok) return [];
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch heatmap", error);
    return [];
  }
}

export async function fetchDeepDive(symbol: string): Promise<DeepDiveData | null> {
  try {
    const res = await fetch(`${API_BASE}/deep-dive/${symbol}`);
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch deep dive", error);
    return null;
  }
}
