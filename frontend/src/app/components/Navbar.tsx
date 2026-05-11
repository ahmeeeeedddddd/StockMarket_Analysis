import { useState, useEffect } from 'react';
import { Activity } from 'lucide-react';
import { isMarketOpen } from '../utils/stockData';

export function Navbar() {
  const [time, setTime] = useState(new Date());
  const marketOpen = isMarketOpen();

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  return (
    <nav className="border-b border-border bg-card px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Activity className="h-8 w-8" style={{ color: '#00D4FF' }} />
          <h1 className="font-mono" style={{ fontSize: '1.5rem', fontWeight: 600, color: '#00D4FF' }}>
            StockPulse
          </h1>
        </div>

        <div className="flex items-center gap-6">
          <div className="font-mono tabular-nums" style={{ fontSize: '1.125rem', color: '#E8EAF0' }}>
            {formatTime(time)}
          </div>
          <div
            className="rounded px-3 py-1 font-mono"
            style={{
              fontSize: '0.875rem',
              fontWeight: 600,
              backgroundColor: marketOpen ? '#00C853' : '#FF3B3B',
              color: '#0A0E1A',
            }}
          >
            {marketOpen ? 'MARKET OPEN' : 'MARKET CLOSED'}
          </div>
        </div>
      </div>
    </nav>
  );
}
