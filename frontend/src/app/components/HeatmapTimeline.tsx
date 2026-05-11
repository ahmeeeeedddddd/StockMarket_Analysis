import React, { useEffect, useState } from 'react';
import { fetchHeatmap, HeatmapData } from '../utils/stockData';

export function HeatmapTimeline() {
  const [data, setData] = useState<HeatmapData[]>([]);

  useEffect(() => {
    const loadData = async () => {
      const heatmap = await fetchHeatmap();
      setData(heatmap);
    };
    
    loadData();
    const interval = setInterval(loadData, 10000); // refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return '#FF3B3B'; // Red
      case 'mild': return '#FFC107';     // Yellow
      default: return '#1A1F2E';         // Gray (normal)
    }
  };

  if (!data.length) {
    return <div className="p-4 font-mono text-[#8B92A8]">Loading Heatmap...</div>;
  }

  return (
    <div className="flex flex-col gap-2 p-4">
      <div className="font-mono mb-2" style={{ fontSize: '1rem', fontWeight: 600, color: '#E8EAF0' }}>
        Anomaly Timeline
      </div>
      <div className="overflow-x-auto">
        <div className="inline-flex flex-col gap-2 min-w-full">
          {data.map((row) => (
            <div key={row.symbol} className="flex items-center gap-4">
              <div className="w-16 font-mono text-sm font-semibold" style={{ color: '#E8EAF0' }}>
                {row.symbol}
              </div>
              <div className="flex flex-1 gap-1">
                {row.timeline.map((cell, idx) => (
                  <div
                    key={idx}
                    className="flex-1 h-6 rounded-sm transition-colors duration-300"
                    style={{ backgroundColor: getSeverityColor(cell.severity) }}
                    title={`${new Date(cell.time).toLocaleTimeString()} - ${cell.severity}`}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
