import React from 'react';
import Plot from 'react-plotly.js';
import { useNavigate } from 'react-router';
import { Candle } from '../utils/stockData';

interface CandlestickChartProps {
  candles: Candle[];
  vwap: number[];
  ema: number[];
  symbol?: string;
}

export function CandlestickChart({ candles, vwap, ema, symbol }: CandlestickChartProps) {
  const navigate = useNavigate();
  if (!candles || candles.length === 0) return null;

  const times = candles.map(c => new Date(c.time));
  const open = candles.map(c => c.open);
  const high = candles.map(c => c.high);
  const low = candles.map(c => c.low);
  const close = candles.map(c => c.close);

  // Group anomalies
  const anomaliesX: Date[] = [];
  const anomaliesY: number[] = [];
  const anomaliesColor: string[] = [];
  const anomaliesText: string[] = [];
  const anomalySymbols: string[] = [];

  // Isolate the single most recent anomaly for pulsing
  let recentAnomaly: { x: Date, y: number, color: string, text: string, symbol: string } | null = null;
  
  // Find it by iterating backwards
  for (let i = candles.length - 1; i >= 0; i--) {
    const c = candles[i];
    if (c.severity && c.severity !== 'normal') {
      const isCritical = c.severity === 'critical';
      const color = isCritical ? '#FF3B3B' : '#FFC107';
      const text = `${c.anomaly_type}: $${c.anomaly_value?.toFixed(2) || c.close}`;
      const symbol = isCritical ? 'circle' : 'circle';
      const yVal = c.anomaly_value || c.close;
      
      if (!recentAnomaly) {
        recentAnomaly = { x: new Date(c.time), y: yVal, color, text, symbol };
      } else {
        anomaliesX.push(new Date(c.time));
        anomaliesY.push(yVal);
        anomaliesColor.push(color);
        anomaliesText.push(text);
        anomalySymbols.push(symbol);
      }
    }
  }

  const data: any[] = [
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
    },
    {
      x: times,
      y: vwap,
      type: 'scatter',
      mode: 'lines',
      line: { color: '#00D4FF', width: 2 },
      name: 'VWAP'
    },
    {
      x: times,
      y: ema,
      type: 'scatter',
      mode: 'lines',
      line: { color: '#FFC107', width: 2 },
      name: 'EMA(20)'
    }
  ];

  // Add historical anomalies trace
  if (anomaliesX.length > 0) {
    data.push({
      x: anomaliesX,
      y: anomaliesY,
      type: 'scatter',
      mode: 'markers',
      marker: {
        color: anomaliesColor,
        symbol: anomalySymbols,
        size: 10,
        line: { color: '#0A0E1A', width: 1 }
      },
      text: anomaliesText,
      hoverinfo: 'text',
      name: 'Anomalies'
    });
  }

  // Add the isolated most recent anomaly trace (must be last to target it via CSS)
  if (recentAnomaly) {
    data.push({
      x: [recentAnomaly.x],
      y: [recentAnomaly.y],
      type: 'scatter',
      mode: 'markers',
      marker: {
        color: recentAnomaly.color,
        symbol: recentAnomaly.symbol,
        size: 14, // Slightly larger
        line: { color: '#0A0E1A', width: 1 }
      },
      text: [recentAnomaly.text],
      hoverinfo: 'text',
      name: 'Recent Anomaly'
    });
  }

  return (
    <div className="anomaly-pulse-container h-full w-full">
      <Plot
        data={data}
        layout={{
          autosize: true,
          margin: { l: 50, r: 10, t: 10, b: 30 },
          paper_bgcolor: '#0D1117',
          plot_bgcolor: '#0D1117',
          font: { family: 'monospace', color: '#8B92A8', size: 12 },
          xaxis: { gridcolor: 'rgba(255,255,255,0.05)', rangeslider: { visible: false }, type: 'date', tickformat: '%H:%M' },
          yaxis: { gridcolor: 'rgba(255,255,255,0.05)', fixedrange: false },
          showlegend: false,
          hovermode: 'closest'
        }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={true}
        onClick={(data) => {
          if (symbol && data.points && data.points.length > 0) {
            navigate(`/deep-dive/${symbol}`);
          }
        }}
      />
    </div>
  );
}
