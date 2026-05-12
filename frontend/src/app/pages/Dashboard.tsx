import { useState, useEffect } from 'react';
import { Link } from 'react-router';
import { StockCard } from '../components/StockCard';
import { CandlestickChart } from '../components/CandlestickChart';
import { VolumeChart } from '../components/VolumeChart';
import { AlertsFeed } from '../components/AlertsFeed';
import { HeatmapTimeline } from '../components/HeatmapTimeline';
import { PipelineHealth } from '../components/PipelineHealth';
import {
  fetchLatestPrice,
  fetchCandles,
  fetchAlerts,
  calculateEMA,
  StockData,
  Candle,
  Alert,
} from '../utils/stockData';
import { BarChart3, Activity } from 'lucide-react';

const STOCKS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META'];
const TIMEFRAMES = [
  { label: '1m', interval: 60, count: 60 },
  { label: '5m', interval: 300, count: 60 },
  { label: '15m', interval: 900, count: 60 },
  { label: '1h', interval: 3600, count: 48 },
];

export function Dashboard() {
  const [stockData, setStockData] = useState<Record<string, StockData>>({});
  const [selectedStock, setSelectedStock] = useState('AAPL');
  const [timeframe, setTimeframe] = useState(0);
  const [candles, setCandles] = useState<Candle[]>([]);
  const [vwap, setVwap] = useState<number[]>([]);
  const [ema, setEma] = useState<number[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [flashingStocks, setFlashingStocks] = useState<Set<string>>(new Set());

  // Fetch prices
  useEffect(() => {
    const fetchPrices = async () => {
      const updated: Record<string, StockData> = {};
      const flashSet = new Set<string>();

      for (const symbol of STOCKS) {
        const data = await fetchLatestPrice(symbol);
        if (data) {
          updated[symbol] = data;
          flashSet.add(symbol);
        }
      }

      setStockData((prev) => {
        // Here we could calculate change dynamically if we wanted, 
        // but for now just populate the data
        return { ...prev, ...updated };
      });
      
      setFlashingStocks(flashSet);
      setTimeout(() => setFlashingStocks(new Set()), 300);
    };

    fetchPrices();
    const priceUpdateInterval = setInterval(fetchPrices, 3000);
    return () => clearInterval(priceUpdateInterval);
  }, []);

  // Fetch candles
  useEffect(() => {
    const fetchChartData = async () => {
      const { interval, count } = TIMEFRAMES[timeframe];
      const newCandles = await fetchCandles(selectedStock, interval, count);
      setCandles(newCandles);
      setVwap(newCandles.map(c => c.vwap || 0)); // Database returns VWAP directly
      setEma(calculateEMA(newCandles));
    };

    fetchChartData();
    const candleUpdateInterval = setInterval(fetchChartData, 5000);
    return () => clearInterval(candleUpdateInterval);
  }, [selectedStock, timeframe]);

  // Fetch alerts
  useEffect(() => {
    const fetchLiveAlerts = async () => {
      const newAlerts = await fetchAlerts(undefined, 50);
      setAlerts(newAlerts);
    };

    fetchLiveAlerts();
    const alertInterval = setInterval(fetchLiveAlerts, 8000);
    return () => clearInterval(alertInterval);
  }, []);

  return (
    <div className="h-full flex flex-col">
      <div className="grid grid-cols-7 gap-2 p-4">
        {STOCKS.map((symbol) => (
          <StockCard
            key={symbol}
            stock={stockData[symbol] || { symbol, price: 0, change: 0, changePercent: 0 }}
            selected={selectedStock === symbol}
            onClick={() => setSelectedStock(symbol)}
            flash={flashingStocks.has(symbol)}
          />
        ))}
      </div>

      <div className="flex-1 flex gap-6 px-6 pb-6 min-h-0">
        <div className="flex-1 flex flex-col gap-4 min-w-0">
          <div className="flex-1 rounded-lg border border-border bg-card p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="font-mono" style={{ fontSize: '1.125rem', fontWeight: 600, color: '#E8EAF0' }}>
                {selectedStock} Chart
              </div>
              <div className="flex gap-2">
                {TIMEFRAMES.map((tf, index) => (
                  <button
                    key={tf.label}
                    onClick={() => setTimeframe(index)}
                    className="px-3 py-1 rounded font-mono transition-all"
                    style={{
                      fontSize: '0.875rem',
                      fontWeight: 600,
                      backgroundColor: timeframe === index ? '#00D4FF' : '#1A1F2E',
                      color: timeframe === index ? '#0A0E1A' : '#8B92A8',
                    }}
                  >
                    {tf.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="h-[calc(100%-3rem)]">
              <CandlestickChart candles={candles} vwap={vwap} ema={ema} symbol={selectedStock} />
            </div>
          </div>

          <div className="h-48 rounded-lg border border-border bg-card p-4">
            <div className="font-mono mb-2" style={{ fontSize: '1rem', fontWeight: 600, color: '#E8EAF0' }}>
              Volume
            </div>
            <div className="h-[calc(100%-2rem)]">
              <VolumeChart candles={candles} />
            </div>
          </div>

          <div className="h-48 rounded-lg border border-border bg-card overflow-hidden">
            <HeatmapTimeline />
          </div>
        </div>

        <div className="w-80 flex flex-col gap-4">
          <div className="flex-1 rounded-lg border border-border bg-card p-4 overflow-hidden">
            <AlertsFeed alerts={alerts} />
          </div>
          
          <Link
            to="/alerts"
            className="flex items-center justify-center gap-2 rounded-lg border border-border bg-card p-4 transition-all hover:border-primary flex-shrink-0"
          >
            <BarChart3 className="h-5 w-5" style={{ color: '#00D4FF' }} />
            <span className="font-mono" style={{ fontSize: '0.875rem', fontWeight: 600, color: '#E8EAF0' }}>
              View All Live Alerts
            </span>
          </Link>

          <Link
            to="/health"
            className="flex items-center justify-center gap-2 rounded-lg border border-border bg-card p-2 transition-all hover:border-primary flex-shrink-0 opacity-70 hover:opacity-100"
          >
            <Activity className="h-4 w-4" style={{ color: '#00D4FF' }} />
            <span className="font-mono" style={{ fontSize: '0.75rem', fontWeight: 600, color: '#E8EAF0' }}>
              System Health
            </span>
          </Link>
        </div>
      </div>
    </div>
  );
}
