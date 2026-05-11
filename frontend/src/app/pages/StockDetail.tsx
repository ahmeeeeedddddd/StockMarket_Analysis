import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router';
import { ArrowLeft, TrendingUp, TrendingDown } from 'lucide-react';
import { CandlestickChart } from '../components/CandlestickChart';
import {
  fetchCandles,
  fetchLatestPrice,
  calculateEMA,
  Candle,
  StockData
} from '../utils/stockData';

export function StockDetail() {
  const { symbol } = useParams<{ symbol: string }>();
  const [candles, setCandles] = useState<Candle[]>([]);
  const [vwap, setVwap] = useState<number[]>([]);
  const [ema, setEma] = useState<number[]>([]);
  const [stockInfo, setStockInfo] = useState<StockData | null>(null);

  useEffect(() => {
    if (!symbol) return;

    const loadData = async () => {
      const initialCandles = await fetchCandles(symbol, 60, 300);
      setCandles(initialCandles);
      setVwap(initialCandles.map(c => c.vwap || 0));
      setEma(calculateEMA(initialCandles));

      const priceInfo = await fetchLatestPrice(symbol);
      if (priceInfo) {
        setStockInfo(priceInfo);
      }
    };

    loadData();

    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [symbol]);

  if (!symbol || !candles.length || !stockInfo) {
    return <div className="p-6 font-mono text-[#E8EAF0]">Loading data for {symbol}...</div>;
  }

  const latestCandle = candles[candles.length - 1];
  const currentPrice = stockInfo.price;
  
  // We calculate a synthetic change if it's not provided by API
  const basePrice = candles[0].open; // roughly compare to start of window
  const change = currentPrice - basePrice;
  const changePercent = (change / basePrice) * 100;
  const isPositive = change >= 0;
  
  const currentVWAP = vwap[vwap.length - 1] || 0;
  const currentEMA = ema[ema.length - 1] || 0;

  const recentTrades = [...candles].reverse().slice(0, 10).map((candle, i) => ({
    id: i,
    time: typeof candle.time === 'number' ? new Date(candle.time).toLocaleTimeString() : new Date(candle.time).toLocaleTimeString(),
    price: candle.close,
    volume: candle.volume || candle.trade_count || 0,
  }));

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6">
        <Link to="/" className="inline-flex items-center gap-2 mb-6 transition-colors" style={{ color: '#00D4FF' }}>
          <ArrowLeft className="h-5 w-5" />
          <span className="font-mono" style={{ fontSize: '0.875rem', fontWeight: 600 }}>
            Back to Dashboard
          </span>
        </Link>

        <div className="mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="font-mono" style={{ fontSize: '2rem', fontWeight: 600, color: '#E8EAF0' }}>
              {symbol}
            </div>
            {isPositive ? (
              <TrendingUp className="h-8 w-8" style={{ color: '#00C853' }} />
            ) : (
              <TrendingDown className="h-8 w-8" style={{ color: '#FF3B3B' }} />
            )}
          </div>

          <div className="font-mono tabular-nums mb-2" style={{ fontSize: '3rem', fontWeight: 600, color: '#E8EAF0' }}>
            ${currentPrice.toFixed(2)}
          </div>

          <div className="flex items-center gap-3">
            <span
              className="font-mono tabular-nums"
              style={{
                fontSize: '1.25rem',
                fontWeight: 500,
                color: isPositive ? '#00C853' : '#FF3B3B',
              }}
            >
              {isPositive ? '+' : ''}
              {change.toFixed(2)}
            </span>
            <span
              className="font-mono tabular-nums"
              style={{
                fontSize: '1.25rem',
                fontWeight: 500,
                color: isPositive ? '#00C853' : '#FF3B3B',
              }}
            >
              ({isPositive ? '+' : ''}
              {changePercent.toFixed(2)}%)
            </span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="font-mono mb-1" style={{ fontSize: '0.875rem', color: '#8B92A8' }}>
              VWAP
            </div>
            <div className="font-mono tabular-nums" style={{ fontSize: '1.5rem', fontWeight: 600, color: '#00D4FF' }}>
              ${currentVWAP.toFixed(2)}
            </div>
          </div>

          <div className="rounded-lg border border-border bg-card p-4">
            <div className="font-mono mb-1" style={{ fontSize: '0.875rem', color: '#8B92A8' }}>
              EMA(20)
            </div>
            <div className="font-mono tabular-nums" style={{ fontSize: '1.5rem', fontWeight: 600, color: '#FFC107' }}>
              ${currentEMA.toFixed(2)}
            </div>
          </div>

          <div className="rounded-lg border border-border bg-card p-4">
            <div className="font-mono mb-1" style={{ fontSize: '0.875rem', color: '#8B92A8' }}>
              Day Range
            </div>
            <div className="font-mono tabular-nums" style={{ fontSize: '1.125rem', fontWeight: 600, color: '#E8EAF0' }}>
              ${latestCandle.low.toFixed(2)} - ${latestCandle.high.toFixed(2)}
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-4 mb-6" style={{ height: '500px' }}>
          <div className="font-mono mb-4" style={{ fontSize: '1.125rem', fontWeight: 600, color: '#E8EAF0' }}>
            Price Chart
          </div>
          <div className="h-[calc(100%-3rem)]">
            <CandlestickChart candles={candles} vwap={vwap} ema={ema} />
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-4">
          <div className="font-mono mb-4" style={{ fontSize: '1.125rem', fontWeight: 600, color: '#E8EAF0' }}>
            Recent Trades
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th
                    className="font-mono text-left py-3 px-4"
                    style={{ fontSize: '0.875rem', fontWeight: 600, color: '#8B92A8' }}
                  >
                    Time
                  </th>
                  <th
                    className="font-mono text-right py-3 px-4"
                    style={{ fontSize: '0.875rem', fontWeight: 600, color: '#8B92A8' }}
                  >
                    Price
                  </th>
                  <th
                    className="font-mono text-right py-3 px-4"
                    style={{ fontSize: '0.875rem', fontWeight: 600, color: '#8B92A8' }}
                  >
                    Volume
                  </th>
                </tr>
              </thead>
              <tbody>
                {recentTrades.map((trade) => (
                  <tr key={trade.id} className="border-b border-border">
                    <td
                      className="font-mono tabular-nums py-3 px-4"
                      style={{ fontSize: '0.875rem', color: '#E8EAF0' }}
                    >
                      {trade.time}
                    </td>
                    <td
                      className="font-mono tabular-nums text-right py-3 px-4"
                      style={{ fontSize: '0.875rem', color: '#E8EAF0' }}
                    >
                      ${trade.price.toFixed(2)}
                    </td>
                    <td
                      className="font-mono tabular-nums text-right py-3 px-4"
                      style={{ fontSize: '0.875rem', color: '#8B92A8' }}
                    >
                      {trade.volume.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
