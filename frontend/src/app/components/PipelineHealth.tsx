import { useState, useEffect } from 'react';
import { Activity, ShieldCheck, ShieldAlert, Cpu } from 'lucide-react';

interface ServiceHealth {
  service_name: string;
  last_heartbeat: string;
  status: string;
  metrics: {
    mps?: number;
    total_processed?: number;
  };
}

export function PipelineHealth() {
  const [health, setHealth] = useState<ServiceHealth[]>([]);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/health');
        const data = await res.json();
        setHealth(data);
      } catch (e) {
        console.error('Failed to fetch health', e);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatus = (lastHeartbeat: string) => {
    const last = new Date(lastHeartbeat).getTime();
    const now = new Date().getTime();
    return (now - last) < 30000 ? 'healthy' : 'dead';
  };

  return (
    <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 flex flex-col gap-3 h-full overflow-hidden">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
          <Activity className="w-3 h-3" />
          Pipeline Pulse
        </h3>
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[10px] text-emerald-500/80 font-bold uppercase tracking-tighter">Live Monitor</span>
        </div>
      </div>

      <div className="space-y-2.5 overflow-y-auto custom-scrollbar pr-1">
        {health.length === 0 ? (
          <div className="text-[10px] text-slate-600 text-center py-4 italic">Waiting for telemetry...</div>
        ) : (
          health.map((s) => {
            const status = getStatus(s.last_heartbeat);
            return (
              <div 
                key={s.service_name}
                className="flex items-center justify-between bg-slate-950/50 border border-slate-800/50 rounded-lg px-3 py-2 transition-all hover:bg-slate-800/30"
              >
                <div className="flex items-center gap-2.5">
                  <div className={`p-1.5 rounded-md ${
                    status === 'healthy' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-500'
                  }`}>
                    {status === 'healthy' ? <ShieldCheck className="w-3.5 h-3.5" /> : <ShieldAlert className="w-3.5 h-3.5" />}
                  </div>
                  <div>
                    <p className="text-[11px] font-bold text-slate-200 capitalize leading-none mb-0.5">{s.service_name}</p>
                    <p className="text-[9px] text-slate-500 font-mono tracking-tighter uppercase">
                      {status === 'healthy' ? 'Active' : 'Offline'}
                    </p>
                  </div>
                </div>
                
                {status === 'healthy' && s.metrics.mps !== undefined && (
                  <div className="text-right">
                    <div className="flex items-center gap-1 justify-end">
                      <Cpu className="w-2.5 h-2.5 text-primary/60" />
                      <span className="text-[11px] font-mono font-bold text-primary">
                        {s.metrics.mps}
                      </span>
                    </div>
                    <p className="text-[8px] text-slate-600 font-bold uppercase tracking-tighter">MPS</p>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
