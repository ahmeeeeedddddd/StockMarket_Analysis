import { useState, useEffect } from 'react';
import { Link } from 'react-router';
import { ArrowLeft, AlertTriangle, AlertCircle, Filter } from 'lucide-react';
import { fetchAlerts, Alert } from '../utils/stockData';

const STOCKS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META'];

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
          <div className="font-mono mb-4" style={{ fontSize: '2.25rem', fontWeight: 700, color: '#E8EAF0' }}>
            Alerts History
            <span className="ml-4 font-normal" style={{ fontSize: '1rem', color: '#8B92A8' }}>
              ({filteredAlerts.length} total)
            </span>
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
              className="rounded border border-border px-3 py-2 font-mono"
              style={{ fontSize: '0.875rem', color: '#E8EAF0', backgroundColor: '#1A1F2E' }}
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
              className="rounded border border-border px-3 py-2 font-mono"
              style={{ fontSize: '0.875rem', color: '#E8EAF0', backgroundColor: '#1A1F2E' }}
            >
              <option value="ALL">All Severities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
        </div>

        <div className="rounded-lg border border-border overflow-hidden" style={{ backgroundColor: '#0D1117' }}>
          <table className="w-full">
            <thead>
              <tr className="border-b border-border" style={{ backgroundColor: '#161B22' }}>
                <th className="font-mono text-left py-3 px-4" style={{ fontSize: '0.75rem', fontWeight: 700, color: '#8B92A8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Time</th>
                <th className="font-mono text-left py-3 px-4" style={{ fontSize: '0.75rem', fontWeight: 700, color: '#8B92A8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Stock</th>
                <th className="font-mono text-left py-3 px-4" style={{ fontSize: '0.75rem', fontWeight: 700, color: '#8B92A8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Alert Type</th>
                <th className="font-mono text-left py-3 px-4" style={{ fontSize: '0.75rem', fontWeight: 700, color: '#8B92A8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Message</th>
                <th className="font-mono text-left py-3 px-4" style={{ fontSize: '0.75rem', fontWeight: 700, color: '#8B92A8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Severity</th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-20 text-center font-mono" style={{ color: '#484F58', fontStyle: 'italic' }}>
                    No alerts found for the selected filters.
                  </td>
                </tr>
              ) : (
                filteredAlerts.map((alert, idx) => (
                  <tr
                    key={`${alert.symbol}-${alert.time}-${idx}`}
                    className="border-b border-border transition-colors hover:bg-[#21262D]"
                  >
                    <td className="font-mono py-3 px-4" style={{ fontSize: '0.875rem', color: '#C9D1D9' }}>
                      {new Date(alert.time).toLocaleString()}
                    </td>
                    <td className="font-mono py-3 px-4 font-bold" style={{ fontSize: '0.875rem', color: '#F0F6FC' }}>
                      {alert.symbol}
                    </td>
                    <td className="font-mono py-3 px-4" style={{ fontSize: '0.875rem', color: '#8B92A8' }}>
                      {alert.alert_type}
                    </td>
                    <td className="font-mono py-3 px-4" style={{ fontSize: '0.875rem', color: '#8B92A8' }}>
                      {alert.message}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        {alert.severity === 'high' ? (
                          <AlertCircle className="h-4 w-4" style={{ color: '#F85149' }} />
                        ) : (
                          <AlertTriangle className="h-4 w-4" style={{ color: '#D29922' }} />
                        )}
                        <span
                          className="font-mono px-2 py-0.5 rounded"
                          style={{
                            fontSize: '0.625rem',
                            fontWeight: 700,
                            textTransform: 'uppercase',
                            backgroundColor: alert.severity === 'high' ? 'rgba(248, 81, 73, 0.1)' : 
                                            alert.severity === 'medium' ? 'rgba(210, 153, 34, 0.1)' : 
                                            'rgba(63, 185, 80, 0.1)',
                            color: alert.severity === 'high' ? '#F85149' : 
                                   alert.severity === 'medium' ? '#D29922' : '#3FB950'
                          }}
                        >
                          {alert.severity}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
