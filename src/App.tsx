import React, { useState, useEffect } from 'react';
import { Mic, EyeOff, FileText, Webhook, Shield, Radio, Sparkles, Command } from 'lucide-react';
import { useMeetingState } from './hooks/useMeetingState';
import { OllamaStatusBanner } from './components/OllamaStatusBanner';
import { StealthPromptBar } from './components/StealthPromptBar';
import { LiveTranscriptionView } from './components/LiveTranscriptionView';
import { SessionHistory } from './components/SessionHistory';
import { SettingsWebhook } from './components/SettingsWebhook';

export default function App() {
  const [activeTab, setActiveTab] = useState<'live' | 'history' | 'webhooks'>('live');
  const [isStealthOpen, setIsStealthOpen] = useState(false);

  const {
    isConnected,
    isRecording,
    activeSessionId,
    transcriptBuffer,
    ollamaStatus,
    liveSummary,
    startSession,
    endSession,
    checkOllamaHealth,
    queryStealthBar,
  } = useMeetingState();

  // Global hotkey handler (Ctrl+Space / Alt+Space toggle stealth bar)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.altKey) && e.code === 'Space') {
        e.preventDefault();
        setIsStealthOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="min-h-screen bg-background text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Banner: Ollama Health & Privacy Assurance */}
      <OllamaStatusBanner status={ollamaStatus} onRefresh={checkOllamaHealth} />

      {/* Main Desktop Header */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-xl sticky top-0 z-40 px-6 py-3.5 flex items-center justify-between shadow-lg">
        {/* Brand logo & tagline */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-600 p-0.5 shadow-lg shadow-indigo-500/20">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <Shield className="w-5 h-5 text-indigo-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-lg tracking-tight text-white">Adrishyaa-Local</h1>
              <span className="bg-slate-800 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider">
                Stealth Co-Pilot
              </span>
            </div>
            <p className="text-xs text-slate-400">Invisible OS-Level Meeting Assistant & Local MoM Manager</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 bg-slate-900/90 border border-slate-800 p-1 rounded-xl">
          <button
            onClick={() => setActiveTab('live')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              activeTab === 'live'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Radio className={`w-3.5 h-3.5 ${isRecording ? 'text-rose-400 animate-pulse' : ''}`} />
            <span>Live Stream</span>
          </button>

          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              activeTab === 'history'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Sessions & MoMs</span>
          </button>

          <button
            onClick={() => setActiveTab('webhooks')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              activeTab === 'webhooks'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Webhook className="w-3.5 h-3.5" />
            <span>Webhooks</span>
          </button>
        </div>

        {/* Stealth Bar Launcher & Engine Health */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsStealthOpen(true)}
            className="bg-gradient-to-r from-indigo-600/90 to-purple-600/90 hover:from-indigo-500 hover:to-purple-500 text-white border border-indigo-400/30 px-3.5 py-2 rounded-xl text-xs font-medium flex items-center gap-2 transition-all shadow-lg shadow-indigo-500/20"
          >
            <EyeOff className="w-4 h-4 text-indigo-200 animate-pulse" />
            <span>Stealth Prompt Bar</span>
            <kbd className="bg-black/30 border border-white/20 text-[10px] px-1.5 py-0.5 rounded font-mono">
              Ctrl+Space
            </kbd>
          </button>

          <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-400 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl">
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-400' : 'bg-rose-500'}`} />
            <span>{isConnected ? 'Engine Ready' : 'Connecting...'}</span>
          </div>
        </div>
      </header>

      {/* Main View Container */}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {activeTab === 'live' && (
          <LiveTranscriptionView
            isRecording={isRecording}
            activeSessionId={activeSessionId}
            transcripts={transcriptBuffer}
            liveSummary={liveSummary}
            onStartSession={startSession}
            onEndSession={endSession}
          />
        )}

        {activeTab === 'history' && <SessionHistory />}

        {activeTab === 'webhooks' && <SettingsWebhook />}
      </main>

      {/* Stealth Prompt Floating Bar */}
      <StealthPromptBar
        isOpen={isStealthOpen}
        onClose={() => setIsStealthOpen(false)}
        onQuery={queryStealthBar}
      />
    </div>
  );
}
