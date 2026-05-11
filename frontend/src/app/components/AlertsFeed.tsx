import { motion, AnimatePresence } from 'motion/react';
import { useNavigate } from 'react-router';
import { Alert } from '../utils/stockData';
import { AlertTriangle, AlertCircle } from 'lucide-react';

interface AlertsFeedProps {
  alerts: Alert[];
}

export function AlertsFeed({ alerts }: AlertsFeedProps) {
  const navigate = useNavigate();

  return (
    <div className="h-full overflow-y-auto">
      <div className="mb-4 font-mono" style={{ fontSize: '1.125rem', fontWeight: 600, color: '#E8EAF0' }}>
        Live Alerts
      </div>

      <div className="space-y-3">
        <AnimatePresence>
          {alerts.slice(0, 10).map((alert, idx) => (
            <motion.div
              key={`${alert.symbol}-${alert.time}-${idx}`}
              onClick={() => navigate(`/deep-dive/${alert.symbol}`)}
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="rounded-lg border p-3 cursor-pointer transition-transform hover:scale-[1.02]"
              style={{
                backgroundColor: '#0D1117',
                borderColor: alert.severity === 'critical' ? '#FF3B3B' : '#FFC107',
              }}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  {alert.severity === 'critical' ? (
                    <AlertCircle className="h-4 w-4" style={{ color: '#FF3B3B' }} />
                  ) : (
                    <AlertTriangle className="h-4 w-4" style={{ color: '#FFC107' }} />
                  )}
                  <span
                    className="font-mono px-2 py-0.5 rounded uppercase"
                    style={{
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      backgroundColor: alert.severity === 'critical' ? '#FF3B3B' : '#FFC107',
                      color: '#0A0E1A',
                    }}
                  >
                    {alert.severity}
                  </span>
                </div>
                <span className="font-mono tabular-nums" style={{ fontSize: '0.75rem', color: '#8B92A8' }}>
                  {new Date(alert.time).toLocaleTimeString()}
                </span>
              </div>

              <div className="flex justify-between items-end mb-1">
                <div className="font-mono" style={{ fontSize: '1rem', fontWeight: 600, color: '#E8EAF0' }}>
                  {alert.symbol}
                </div>
                <div className="font-mono text-xs" style={{ color: '#8B92A8' }}>
                  {alert.alert_type}
                </div>
              </div>

              <div className="font-mono text-xs" style={{ color: '#8B92A8' }}>
                {alert.message}
              </div>
              
              {(alert.actual_value !== undefined && alert.expected_value !== undefined) && (
                <div className="mt-2 flex items-center justify-between font-mono text-xs p-1.5 rounded bg-secondary">
                  <div className="text-[#8B92A8]">Actual: <span className="text-[#E8EAF0]">${alert.actual_value.toFixed(2)}</span></div>
                  <div className="text-[#8B92A8]">Expected: <span className="text-[#E8EAF0]">${alert.expected_value.toFixed(2)}</span></div>
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
