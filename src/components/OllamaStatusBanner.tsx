import React, { useState } from 'react';
import { AlertTriangle, RefreshCw, Cpu, CheckCircle2 } from 'lucide-react';
import { OllamaStatus } from '../hooks/useMeetingState';

interface BannerProps {
  status: OllamaStatus;
  onRefresh: () => void;
}

export const OllamaStatusBanner: React.FC<BannerProps> = ({ status, onRefresh }) => {
  const [isChecking, setIsChecking] = useState(false);

  const handleRetry = async () => {
    setIsChecking(true);
    await onRefresh();
    setTimeout(() => setIsChecking(false), 600);
  };

  if (status.online) {
    return (
      <div className="bg-emerald-950/40 border-b border-emerald-500/20 px-4 py-2 flex items-center justify-between text-xs text-emerald-300 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>
            Ollama Local Engine Connected (<strong className="font-semibold text-emerald-200">{status.selected_model || 'qwen2.5:7b'}</strong>) on <code className="bg-emerald-900/60 px-1.5 py-0.5 rounded">{status.url}</code>
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Cpu className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
          <span className="text-[11px] text-emerald-400/80">100% Offline AI Privacy Active</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-amber-950/80 border-b border-amber-500/30 px-4 py-3 text-amber-200 backdrop-blur-md">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-amber-100 text-sm">Ollama Local Engine Offline</p>
            <p className="text-amber-300/80 mt-0.5">
              Local LLM features (MoM generation, 90s summaries, and Stealth Prompt Bar) require Ollama running at <code className="bg-amber-900/60 px-1 py-0.5 rounded text-amber-200">{status.url}</code>.
            </p>
            <div className="mt-1 text-[11px] text-amber-400/70">
              Run <code className="bg-slate-900 px-1.5 py-0.5 rounded text-slate-200">ollama run qwen2.5:7b</code> in terminal to start Ollama.
            </div>
          </div>
        </div>
        <button
          onClick={handleRetry}
          disabled={isChecking}
          className="shrink-0 bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-500/40 px-3.5 py-1.5 rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isChecking ? 'animate-spin' : ''}`} />
          <span>{isChecking ? 'Checking...' : 'Check Connection'}</span>
        </button>
      </div>
    </div>
  );
};
