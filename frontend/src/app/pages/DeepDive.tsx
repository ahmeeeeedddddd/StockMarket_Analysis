import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router';
import Plot from 'react-plotly.js';
import { ArrowLeft, AlertTriangle } from 'lucide-react';
import { fetchDeepDive, DeepDiveData } from '../utils/stockData';

export function DeepDive() {
  const { symbol } = useParams<{ symbol: string }>();
  const [data, setData] = useState<DeepDiveData | null>(null);

  useEffect(() => {
    if (symbol) {
      fetchDeepDive(symbol).then(setData);
    }
  }, [symbol]);

  if (!data) {
    return <div className="p-6 font-mono text-[#E8EAF0]">Loading Anomaly Data for {symbol}...</div>;
  }

  const { candles, historical } = data;
  
  if (candles.length === 0) {
    return <div className="p-6 font-mono text-[#E8EAF0]">No data available.</div>;
  }

  // Find the most recent anomaly to populate the stat cards
  const recentAnomaly = candles.slice().reverse().find(c => c.severity !== 'normal');
  const triggerReason = recentAnomaly?.anomaly_type || "N/A";
  const devMetric = recentAnomaly?.anomaly_value 
    ? `$${recentAnomaly.anomaly_value.toFixed(2)}` 
    : "N/A";
    
  // Time arrays
  const times = candles.map(c => new Date(c.time));
  
  // Candlestick data
  const open = candles.map(c => c.open);
  const high = candles.map(c => c.high);
  const low = candles.map(c => c.low);
  const close = candles.map(c => c.close);
  
  // Bollinger Bands
  const upper = candles.map(c => c.upper);
  const lower = candles.map(c => c.lower);
  const ma = candles.map(c => c.ma);
  
  // Z-Score
  const zScore = candles.map(c => c.z_score);

  return (
    <div className="h-full overflow-y-auto p-6">
      <Link to="/" className="inline-flex items-center gap-2 mb-6 transition-colors" style={{ color: '#00D4FF' }}>
        <ArrowLeft className="h-5 w-5" />
        <span className="font-mono" style={{ fontSize: '0.875rem', fontWeight: 600 }}>
          Back to Dashboard
        </span>
      </Link>

      <div className="flex items-center gap-3 mb-6">
        <AlertTriangle className="h-8 w-8" style={{ color: '#FF3B3B' }} />
        <div className="font-mono" style={{ fontSize: '2rem', fontWeight: 600, color: '#E8EAF0' }}>
          {symbol} Anomaly Deep-Dive
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="font-mono mb-1" style={{ fontSize: '0.875rem', color: '#8B92A8' }}>
            Trigger Reason
          </div>
          <div className="font-mono" style={{ fontSize: '1.25rem', fontWeight: 600, color: '#FF3B3B' }}>
            {triggerReason}
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="font-mono mb-1" style={{ fontSize: '0.875rem', color: '#8B92A8' }}>
            Deviation Metric
          </div>
          <div className="font-mono tabular-nums" style={{ fontSize: '1.25rem', fontWeight: 600, color: '#E8EAF0' }}>
            {devMetric}
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="font-mono mb-1" style={{ fontSize: '0.875rem', color: '#8B92A8' }}>
            Duration
          </div>
          <div className="font-mono tabular-nums" style={{ fontSize: '1.25rem', fontWeight: 600, color: '#E8EAF0' }}>
            5 min (1 Candle)
          </div>
        </div>
      </div>

      {/* Zoomed Candlestick Chart */}
      <div className="rounded-lg border border-border bg-card p-4 mb-6" style={{ height: '400px' }}>
        <div className="font-mono mb-4" style={{ fontSize: '1.125rem', fontWeight: 600, color: '#E8EAF0' }}>
          Anomaly Window
        </div>
        <div className="h-[calc(100%-3rem)]">
          <Plot
            data={[
              {
                x: times,
                close: close,
                decreasing: { line: { color: '#FF3B3B' } },
                high: high,
                increasing: { line: { color: '#00C853' } },
                line: { color: 'rgba(31,119,180,1)' },
                low: low,
                open: open,
                type: 'candlestick',
                name: 'Price'
              }
            ]}
            layout={{
              autosize: true,
              margin: { l: 50, r: 10, t: 10, b: 30 },
              paper_bgcolor: '#0D1117',
              plot_bgcolor: '#0D1117',
              font: { family: 'monospace', color: '#8B92A8', size: 12 },
              xaxis: { gridcolor: 'rgba(255,255,255,0.05)', rangeslider: { visible: false }, type: 'date' },
              yaxis: { gridcolor: 'rgba(255,255,255,0.05)', fixedrange: false },
              showlegend: false
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler={true}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Bollinger Bands */}
        <div className="rounded-lg border border-border bg-card p-4" style={{ height: '350px' }}>
          <div className="font-mono mb-4" style={{ fontSize: '1.125rem', fontWeight: 600, color: '#E8EAF0' }}>
            Bollinger Bands
          </div>
          <div className="h-[calc(100%-3rem)]">
            <Plot
              data={[
                {
                  x: times,
                  y: upper,
                  type: 'scatter',
                  mode: 'lines',
                  line: { width: 0 },
                  showlegend: false,
                  hoverinfo: 'skip'
                },
                {
                  x: times,
                  y: lower,
                  type: 'scatter',
                  mode: 'lines',
                  fill: 'tonexty',
                  fillcolor: 'rgba(0, 212, 255, 0.1)', // Soft blue shaded region
                  line: { width: 0 },
                  showlegend: false,
                  hoverinfo: 'skip'
                },
                {
                  x: times,
                  y: close,
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: '#ffffff', width: 2 },
                  name: 'Price'
                },
                {
                  x: times,
                  y: ma,
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: '#FFC107', width: 1, dash: 'dot' },
                  name: 'MA(20)'
                }
              ]}
              layout={{
                autosize: true,
                margin: { l: 40, r: 10, t: 10, b: 30 },
                paper_bgcolor: '#0D1117',
                plot_bgcolor: '#0D1117',
                font: { family: 'monospace', color: '#8B92A8', size: 12 },
                xaxis: { gridcolor: 'rgba(255,255,255,0.05)', type: 'date' },
                yaxis: { gridcolor: 'rgba(255,255,255,0.05)' },
                showlegend: false
              }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler={true}
            />
          </div>
        </div>

        {/* Z-Score Chart */}
        <div className="rounded-lg border border-border bg-card p-4" style={{ height: '350px' }}>
          <div className="font-mono mb-4" style={{ fontSize: '1.125rem', fontWeight: 600, color: '#E8EAF0' }}>
            Rolling Z-Score
          </div>
          <div className="h-[calc(100%-3rem)]">
            <Plot
              data={[
                // Upper Threshold
                {
                  x: [times[0], times[times.length - 1]],
                  y: [2, 2],
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: '#FF3B3B', dash: 'dash', width: 1 },
                  hoverinfo: 'skip'
                },
                // Lower Threshold
                {
                  x: [times[0], times[times.length - 1]],
                  y: [-2, -2],
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: '#FF3B3B', dash: 'dash', width: 1 },
                  fill: 'tonexty',
                  fillcolor: 'rgba(0, 200, 83, 0.1)', // Soft green normal zone
                  hoverinfo: 'skip'
                },
                // Z-Score line
                {
                  x: times,
                  y: zScore,
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: '#FF9800', width: 2 }, // Orange line
                  name: 'Z-Score'
                }
              ]}
              layout={{
                autosize: true,
                margin: { l: 40, r: 10, t: 10, b: 30 },
                paper_bgcolor: '#0D1117',
                plot_bgcolor: '#0D1117',
                font: { family: 'monospace', color: '#8B92A8', size: 12 },
                xaxis: { gridcolor: 'rgba(255,255,255,0.05)', type: 'date' },
                yaxis: { gridcolor: 'rgba(255,255,255,0.05)', range: [-4, 4] },
                showlegend: false
              }}
              config={{ responsive: true, displayModeBar: false }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler={true}
            />
          </div>
        </div>
      </div>

      {/* History Table */}
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="font-mono mb-4" style={{ fontSize: '1.125rem', fontWeight: 600, color: '#E8EAF0' }}>
          Historical Anomalies
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-border text-left">
              <th className="font-mono py-2 text-[#8B92A8]">Time</th>
              <th className="font-mono py-2 text-[#8B92A8]">Type</th>
              <th className="font-mono py-2 text-[#8B92A8]">Value</th>
              <th className="font-mono py-2 text-[#8B92A8]">Severity</th>
            </tr>
          </thead>
          <tbody>
            {historical.map((h, i) => (
              <tr key={i} className="border-b border-border">
                <td className="font-mono py-3 text-[#E8EAF0]">{new Date(h.time).toLocaleString()}</td>
                <td className="font-mono py-3 text-[#E8EAF0]">{h.anomaly_type}</td>
                <td className="font-mono py-3 text-[#E8EAF0]">${h.anomaly_value?.toFixed(2) || h.close.toFixed(2)}</td>
                <td className="font-mono py-3">
                  <span className="px-2 py-1 rounded text-xs font-semibold" style={{
                    backgroundColor: h.severity === 'critical' ? '#FF3B3B' : '#FFC107',
                    color: '#0A0E1A'
                  }}>
                    {h.severity}
                  </span>
                </td>
              </tr>
            ))}
            {historical.length === 0 && (
              <tr>
                <td colSpan={4} className="py-4 text-center text-[#8B92A8] font-mono">No historical anomalies found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
