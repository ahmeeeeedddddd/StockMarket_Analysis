import { motion } from 'motion/react';
import { StockData } from '../utils/stockData';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface StockCardProps {
  stock: StockData;
  selected?: boolean;
  onClick?: () => void;
  flash?: boolean;
}

export function StockCard({ stock, selected, onClick, flash }: StockCardProps) {
  const isPositive = stock.change >= 0;
  const flashColor = isPositive ? '#00C853' : '#FF3B3B';

  return (
    <motion.div
      onClick={onClick}
      animate={
        flash
          ? {
              backgroundColor: [selected ? '#1A1F2E' : '#0D1117', flashColor + '20', selected ? '#1A1F2E' : '#0D1117'],
              transition: { duration: 0.3 },
            }
          : {}
      }
      className="rounded-lg border border-border p-4 transition-all cursor-pointer"
      style={{
        backgroundColor: selected ? '#1A1F2E' : '#0D1117',
        borderColor: selected ? '#00D4FF' : 'rgba(255, 255, 255, 0.1)',
      }}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="font-mono" style={{ fontSize: '1.125rem', fontWeight: 600, color: '#E8EAF0' }}>
          {stock.symbol}
        </div>
        {isPositive ? (
          <TrendingUp className="h-5 w-5" style={{ color: '#00C853' }} />
        ) : (
          <TrendingDown className="h-5 w-5" style={{ color: '#FF3B3B' }} />
        )}
      </div>

      <div className="font-mono tabular-nums mb-1" style={{ fontSize: '1.5rem', fontWeight: 600, color: '#E8EAF0' }}>
        ${stock.price.toFixed(2)}
      </div>

      <div className="flex items-center gap-2">
        <span
          className="font-mono tabular-nums"
          style={{
            fontSize: '0.875rem',
            fontWeight: 500,
            color: isPositive ? '#00C853' : '#FF3B3B',
          }}
        >
          {isPositive ? '+' : ''}
          {stock.change.toFixed(2)}
        </span>
        <span
          className="font-mono tabular-nums"
          style={{
            fontSize: '0.875rem',
            fontWeight: 500,
            color: isPositive ? '#00C853' : '#FF3B3B',
          }}
        >
          ({isPositive ? '+' : ''}
          {stock.changePercent.toFixed(2)}%)
        </span>
      </div>
    </motion.div>
  );
}
