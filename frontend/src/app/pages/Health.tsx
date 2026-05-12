import { PipelineHealth } from '../components/PipelineHealth';
import { Activity, ShieldCheck, Cpu, Clock } from 'lucide-react';

export default function Health() {
  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-primary/10 text-primary">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-100">Pipeline Pulse</h1>
            <p className="text-slate-400 mt-1">Real-time telemetry and health monitoring for all system services.</p>
          </div>
        </div>
        
        <div className="flex gap-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl px-4 py-2 flex items-center gap-3">
            <Clock className="w-4 h-4 text-slate-500" />
            <div>
              <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Reporting Frequency</p>
              <p className="text-sm font-mono text-slate-200">10 Seconds</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2">
          <PipelineHealth />
        </div>
        
        <div className="space-y-6">
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              SLA Status
            </h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-400">Uptime (24h)</span>
                <span className="text-sm font-mono text-emerald-400">99.9%</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5">
                <div className="bg-emerald-500 h-1.5 rounded-full w-[99.9%]" />
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-400">Avg. Latency</span>
                <span className="text-sm font-mono text-primary">124ms</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5">
                <div className="bg-primary h-1.5 rounded-full w-[65%]" />
              </div>
            </div>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-primary" />
              System Load
            </h3>
            <p className="text-sm text-slate-400 leading-relaxed">
              All services are currently operating within normal parameters. Anomaly detection latencies are minimal.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
