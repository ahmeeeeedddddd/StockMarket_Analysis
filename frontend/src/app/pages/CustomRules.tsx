import { useState, useEffect } from 'react';
import { Plus, Trash2, Bell, TrendingUp, TrendingDown, Zap } from 'lucide-react';

interface Rule {
  id: number;
  symbol: string;
  rule_type: string;
  threshold: number;
  window_sec: number;
}

const STOCKS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META'];

export default function CustomRules() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [symbol, setSymbol] = useState('AAPL');
  const [type, setType] = useState('price_above');
  const [threshold, setThreshold] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchRules = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/rules');
      if (!res.ok) {
        console.error('API responded with error:', res.status);
        setRules([]);
        return;
      }
      const data = await res.json();
      setRules(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error('Failed to fetch rules', e);
      setRules([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const addRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!threshold) return;

    try {
      setLoading(true);
      const res = await fetch('http://localhost:8000/api/rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol,
          rule_type: type,
          threshold: parseFloat(threshold),
          window_sec: 60,
        }),
      });

      if (res.ok) {
        alert(`Successfully activated ${type} rule for ${symbol}!`);
        setThreshold('');
        await fetchRules();
      } else {
        const errorData = await res.json().catch(() => ({}));
        alert(`Failed to activate rule: ${errorData.detail || res.statusText}`);
      }
    } catch (e) {
      console.error('Failed to add rule', e);
      alert('Failed to connect to the backend server. Is the pipeline running?');
    } finally {
      setLoading(false);
    }
  };

  const deleteRule = async (id: number) => {
    try {
      await fetch(`http://localhost:8000/api/rules/${id}`, { method: 'DELETE' });
      fetchRules();
    } catch (e) {
      console.error('Failed to delete rule', e);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      <div className="flex items-center gap-3">
        <div className="p-3 rounded-xl bg-primary/10 text-primary">
          <Bell className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100">Custom Alert Rules</h1>
          <p className="text-slate-400 mt-1">Define your own market thresholds and get notified instantly.</p>
        </div>
      </div>

      <div className="grid md:grid-cols-[1fr_1.5fr] gap-8">
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm self-start">
          <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
            <Plus className="w-4 h-4 text-primary" />
            Create New Rule
          </h2>
          
          <form onSubmit={addRule} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2 text-left">Stock Symbol</label>
              <select 
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all cursor-pointer"
              >
                {STOCKS.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2 text-left">Condition</label>
              <select 
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all cursor-pointer"
              >
                <option value="price_above">Price goes above</option>
                <option value="price_below">Price goes below</option>
                <option value="volume_above">Volume exceeds</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2 text-left">Threshold Value</label>
              <div className="relative">
                <input 
                  type="number"
                  step="any"
                  value={threshold}
                  onChange={(e) => setThreshold(e.target.value)}
                  placeholder="e.g. 500.00"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                />
              </div>
            </div>

            <button 
              type="submit"
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-3 rounded-xl shadow-lg shadow-primary/20 transition-all active:scale-95 flex items-center justify-center gap-2"
            >
              <Zap className="w-4 h-4" />
              Activate Rule
            </button>
          </form>
        </div>

        <div className="space-y-4">
          <h2 className="text-lg font-semibold flex items-center gap-2 px-2">
            <Zap className="w-4 h-4 text-primary" />
            Active Watchlist ({rules.length})
          </h2>
          
          {loading ? (
            <div className="text-center py-12 text-slate-500">Loading rules...</div>
          ) : rules.length === 0 ? (
            <div className="text-center py-12 bg-slate-900/30 border border-dashed border-slate-800 rounded-2xl text-slate-500">
              No active rules. Create one to start monitoring.
            </div>
          ) : (
            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
              {rules.map((rule) => (
                <div 
                  key={rule.id}
                  className="group bg-slate-900/50 border border-slate-800 hover:border-slate-700 rounded-xl p-4 flex items-center justify-between transition-all"
                >
                  <div className="flex items-center gap-4">
                    <div className={`p-2.5 rounded-lg ${
                      (rule.rule_type || '').includes('above') ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                    }`}>
                      {rule.rule_type === 'price_above' && <TrendingUp className="w-5 h-5" />}
                      {rule.rule_type === 'price_below' && <TrendingDown className="w-5 h-5" />}
                      {(rule.rule_type === 'volume_above' || rule.rule_type === 'volume_spike') && <Zap className="w-5 h-5" />}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-100">{rule.symbol}</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                          {(rule.rule_type || 'unknown').replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-sm text-slate-400 mt-0.5">
                        Alert at <span className="text-slate-200 font-mono">
                          {(rule.rule_type || '').includes('volume') ? (rule.threshold || 0).toLocaleString() : `$${(rule.threshold || 0).toFixed(2)}`}
                        </span>
                      </p>
                    </div>
                  </div>
                  <button 
                    onClick={() => deleteRule(rule.id)}
                    className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
