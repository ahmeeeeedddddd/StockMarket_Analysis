import { useState, useEffect } from 'react';
import { Link } from 'react-router';
import { ArrowLeft, AlertTriangle, AlertCircle, Filter } from 'lucide-react';
import { fetchAlerts, Alert } from '../utils/stockData';

const STOCKS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA'];

export function AlertsHistory() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [filterSymbol, setFilterSymbol] = useState<string>('ALL');
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');

  useEffect(() => {
    const loadAlerts = async () => {
      const liveAlerts = await fetchAlerts(undefined, 200);
      setAlerts(liveAlerts);
    };

    loadAlerts();

    const interval = setInterval(loadAlerts, 10000);
    return () => clearInterval(interval);
  }, []);

  const filteredAlerts = alerts.filter((alert) => {
    if (filterSymbol !== 'ALL' && alert.symbol !== filterSymbol) return false;
    if (filterSeverity !== 'ALL' && alert.severity !== filterSeverity) return false;
    return true;
  });

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
          <div className="font-mono mb-4" style={{ fontSize: '2rem', fontWeight: 600, color: '#E8EAF0' }}>
            Alerts History
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-5 w-5" style={{ color: '#8B92A8' }} />
              <span className="font-mono" style={{ fontSize: '0.875rem', color: '#8B92A8' }}>
                Filter:
              </span>
            </div>

            <select
              value={filterSymbol}
              onChange={(e) => setFilterSymbol(e.target.value)}
              className="rounded border border-border bg-input-background px-3 py-2 font-mono"
              style={{ fontSize: '0.875rem', color: '#E8EAF0' }}
            >
              <option value="ALL">All Stocks</option>
              {STOCKS.map((symbol) => (
                <option key={symbol} value={symbol}>
                  {symbol}
                </option>
              ))}
            </select>

            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="rounded border border-border bg-input-background px-3 py-2 font-mono"
              style={{ fontSize: '0.875rem', color: '#E8EAF0' }}
            >
              <option value="ALL">All Severities</option>
              <option value="WARNING">Warning</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border" style={{ backgroundColor: '#1A1F2E' }}>
                <th
                  className="font-mono text-left py-3 px-4"
                  style={{ fontSize: '0.875rem', fontWeight: 600, color: '#8B92A8' }}
                >
                  Time
                </th>
                <th
                  className="font-mono text-left py-3 px-4"
                  style={{ fontSize: '0.875rem', fontWeight: 600, color: '#8B92A8' }}
                >
                  Stock
                </th>
                <th
                  className="font-mono text-left py-3 px-4"
                  style={{ fontSize: '0.875rem', fontWeight: 600, color: '#8B92A8' }}
                >
                  Alert Type
                </th>
                <th
                  className="font-mono text-left py-3 px-4"
                  style={{ fontSize: '0.875rem', fontWeight: 600, color: '#8B92A8' }}
                >
                  Value
                </th>
                <th
                  className="font-mono text-left py-3 px-4"
                  style={{ fontSize: '0.875rem', fontWeight: 600, color: '#8B92A8' }}
                >
                  Severity
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.map((alert, idx) => (
                <tr
                  key={`${alert.symbol}-${alert.time}-${idx}`}
                  className="border-b border-border transition-colors hover:bg-secondary"
                  style={{
                    backgroundColor: alert.severity === 'CRITICAL' ? 'rgba(255, 59, 59, 0.05)' : 'transparent',
                  }}
                >
                  <td
                    className="font-mono tabular-nums py-3 px-4"
                    style={{ fontSize: '0.875rem', color: '#E8EAF0' }}
                  >
                    {new Date(alert.time).toLocaleString()}
                  </td>
                  <td
                    className="font-mono py-3 px-4"
                    style={{ fontSize: '0.875rem', fontWeight: 600, color: '#E8EAF0' }}
                  >
                    {alert.symbol}
                  </td>
                  <td className="font-mono py-3 px-4" style={{ fontSize: '0.875rem', color: '#8B92A8' }}>
                    {alert.alert_type}
                  </td>
                  <td
                    className="font-mono tabular-nums py-3 px-4"
                    style={{ fontSize: '0.875rem', color: '#E8EAF0' }}
                  >
                    {alert.message}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      {alert.severity === 'CRITICAL' ? (
                        <AlertCircle className="h-4 w-4" style={{ color: '#FF3B3B' }} />
                      ) : (
                        <AlertTriangle className="h-4 w-4" style={{ color: '#FFC107' }} />
                      )}
                      <span
                        className="font-mono px-2 py-0.5 rounded"
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          backgroundColor: alert.severity === 'CRITICAL' ? '#FF3B3B' : '#FFC107',
                          color: '#0A0E1A',
                        }}
                      >
                        {alert.severity}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
