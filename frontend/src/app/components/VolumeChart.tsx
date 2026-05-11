import React from 'react';
import Plot from 'react-plotly.js';
import { Candle } from '../utils/stockData';

interface VolumeChartProps {
  candles: Candle[];
}

export function VolumeChart({ candles }: VolumeChartProps) {
  if (!candles || candles.length === 0) return null;

  const times = candles.map((c) => new Date(c.time));
  const volumes = candles.map((c) => c.volume);
  const colors = candles.map((c) => (c.close >= c.open ? 'rgba(0, 200, 83, 0.6)' : 'rgba(255, 59, 59, 0.6)'));

  return (
    <Plot
      data={[
        {
          x: times,
          y: volumes,
          type: 'bar',
          marker: { color: colors },
          name: 'Volume'
        }
      ]}
      layout={{
        autosize: true,
        margin: { l: 50, r: 10, t: 10, b: 30 },
        paper_bgcolor: '#0D1117',
        plot_bgcolor: '#0D1117',
        font: {
          family: 'monospace',
          color: '#8B92A8',
          size: 12
        },
        xaxis: {
          gridcolor: 'rgba(255,255,255,0.05)',
          type: 'date',
          tickformat: '%H:%M'
        },
        yaxis: {
          gridcolor: 'rgba(255,255,255,0.05)',
          fixedrange: false
        },
        showlegend: false
      }}
      config={{
        responsive: true,
        displayModeBar: false
      }}
      style={{ width: '100%', height: '100%' }}
      useResizeHandler={true}
    />
  );
}
