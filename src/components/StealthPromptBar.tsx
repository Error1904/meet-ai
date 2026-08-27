import React, { useState, useEffect, useRef } from 'react';
import { EyeOff, Send, Sparkles, X, CornerDownLeft, Command, ShieldCheck } from 'lucide-react';

interface StealthPromptProps {
  isOpen: boolean;
  onClose: () => void;
  onQuery: (question: string) => Promise<string>;
}

export const StealthPromptBar: React.FC<StealthPromptProps> = ({ isOpen, onClose, onQuery }) => {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery('');
      setAnswer(null);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.strip() || isLoading) return;

    setIsLoading(true);
    setAnswer(null);
    const res = await onQuery(query);
    setAnswer(res);
    setIsLoading(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 px-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-2xl glass-stealth rounded-2xl p-4 shadow-2xl transition-all">
        {/* Top bar header */}
        <div className="flex items-center justify-between text-xs text-slate-400 mb-3 px-1 border-b border-slate-700/50 pb-2">
          <div className="flex items-center gap-2">
            <EyeOff className="w-4 h-4 text-indigo-400 animate-pulse" />
            <span className="font-semibold text-indigo-300">STEALTH OVERLAY CO-PILOT</span>
            <span className="bg-indigo-950 text-indigo-300 border border-indigo-500/30 px-1.5 py-0.5 rounded text-[10px] uppercase font-mono">
              15-Min Context Window
            </span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 text-[11px] text-slate-400">
              <Command className="w-3 h-3" />
              <span>Press <kbd className="bg-slate-800 border border-slate-700 px-1.5 py-0.5 rounded text-slate-200">Esc</kbd> to hide</span>
            </div>
            <button onClick={onClose} className="hover:text-white transition-colors p-0.5">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="relative flex items-center">
          <Sparkles className="w-5 h-5 text-indigo-400 absolute left-3.5" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask anything about the active meeting... (e.g. 'What is the Q3 deadline?')"
            className="w-full bg-slate-900/90 text-white placeholder-slate-500 rounded-xl pl-11 pr-24 py-3 text-sm border border-indigo-500/30 focus:outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20 transition-all shadow-inner"
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="absolute right-2 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white px-3.5 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 shadow-md disabled:opacity-40 transition-all"
          >
            {isLoading ? (
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-white animate-ping" />
                Thinking...
              </span>
            ) : (
              <>
                <span>Ask AI</span>
                <CornerDownLeft className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </form>

        {/* Suggested Quick Prompts */}
        {!answer && !isLoading && (
          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            <span className="text-slate-400 text-[11px] self-center mr-1">Quick Prompts:</span>
            {[
              "Summarize the last 3 minutes",
              "What did Sarah say about deadlines?",
              "What are the current open action items?"
            ].map((p) => (
              <button
                key={p}
                onClick={() => setQuery(p)}
                className="bg-slate-800/80 hover:bg-indigo-950/80 hover:border-indigo-500/40 text-slate-300 hover:text-indigo-200 border border-slate-700/60 px-2.5 py-1 rounded-lg transition-colors text-[11px]"
              >
                {p}
              </button>
            ))}
          </div>
        )}

        {/* Real-time Stealth Answer Display */}
        {answer && (
          <div className="mt-4 bg-slate-950/90 border border-indigo-500/30 rounded-xl p-4 animate-in slide-in-from-top-2 duration-200">
            <div className="flex items-center justify-between text-xs text-indigo-300 font-semibold mb-2">
              <span className="flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                Real-Time Contextual Response:
              </span>
              <span className="text-[10px] text-emerald-400 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" /> Zero Cloud Transmission
              </span>
            </div>
            <p className="text-slate-200 text-sm leading-relaxed whitespace-pre-wrap">{answer}</p>
          </div>
        )}
      </div>
    </div>
  );
};
