import React, { useState, useRef, useEffect } from 'react';
import { Play, Square, Mic, Volume2, User, Users, Sparkles, Clock, Layers, FileCheck } from 'lucide-react';
import { TranscriptItem, LiveSummary } from '../hooks/useMeetingState';

interface LiveViewProps {
  isRecording: boolean;
  activeSessionId: string | null;
  transcripts: TranscriptItem[];
  liveSummary: LiveSummary;
  onStartSession: (title: string) => void;
  onEndSession: () => Promise<any>;
}

export const LiveTranscriptionView: React.FC<LiveViewProps> = ({
  isRecording,
  activeSessionId,
  transcripts,
  liveSummary,
  onStartSession,
  onEndSession,
}) => {
  const [sessionTitle, setSessionTitle] = useState('Q3 Product & Architecture Sync');
  const [isGeneratingMoM, setIsGeneratingMoM] = useState(false);
  const [lastGeneratedMoM, setLastGeneratedMoM] = useState<any>(null);
  const transcriptEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcripts]);

  const handleEndSessionClick = async () => {
    setIsGeneratingMoM(true);
    const result = await onEndSession();
    setLastGeneratedMoM(result?.mom);
    setIsGeneratingMoM(false);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-140px)]">
      {/* Main Subtitle Feed (2 Cols) */}
      <div className="lg:col-span-2 flex flex-col glass-card rounded-2xl p-5 border border-slate-800 shadow-xl overflow-hidden">
        {/* Header & Controls */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isRecording ? 'bg-rose-500 animate-ping' : 'bg-slate-600'}`} />
              <h2 className="font-semibold text-lg text-white">
                {isRecording ? 'Live Meeting In Progress' : 'Meeting Transcription Feed'}
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-2">
              <span>Dual WASAPI OS Capture (System Output + Microphone)</span>
              <span className="text-slate-600">•</span>
              <span className="text-indigo-400">15-Min Sliding Buffer Active</span>
            </p>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            {!isRecording ? (
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <input
                  type="text"
                  value={sessionTitle}
                  onChange={(e) => setSessionTitle(e.target.value)}
                  placeholder="Session Title..."
                  className="bg-slate-900 border border-slate-700 text-white text-xs px-3 py-2 rounded-lg focus:outline-none focus:border-indigo-500 w-full sm:w-48"
                />
                <button
                  onClick={() => onStartSession(sessionTitle)}
                  className="shrink-0 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs px-4 py-2 rounded-lg flex items-center gap-2 transition-all shadow-lg shadow-indigo-600/30"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Start Session</span>
                </button>
              </div>
            ) : (
              <button
                onClick={handleEndSessionClick}
                disabled={isGeneratingMoM}
                className="bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs px-4 py-2 rounded-lg flex items-center gap-2 transition-all shadow-lg shadow-rose-600/30 disabled:opacity-50"
              >
                {isGeneratingMoM ? (
                  <>
                    <span className="w-3 h-3 rounded-full border-2 border-white border-t-transparent animate-spin" />
                    <span>Generating Structured MoM...</span>
                  </>
                ) : (
                  <>
                    <Square className="w-3.5 h-3.5 fill-current" />
                    <span>End Meeting & Generate MoM</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Live Subtitle Transcript Stream */}
        <div className="flex-1 overflow-y-auto py-4 space-y-3.5 pr-2">
          {transcripts.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-500 text-center py-12">
              <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mb-3 text-indigo-400">
                <Mic className="w-6 h-6 animate-pulse" />
              </div>
              <p className="text-sm font-medium text-slate-300">
                {isRecording ? 'Listening for speech...' : 'No active recording session'}
              </p>
              <p className="text-xs text-slate-500 max-w-xs mt-1">
                {isRecording
                  ? 'System audio loopback and user mic audio are continuously processed offline via Faster-Whisper.'
                  : 'Click "Start Session" to begin capturing live dual-channel meeting audio.'}
              </p>
            </div>
          ) : (
            transcripts.map((item, idx) => {
              const isUser = item.speaker === 'User';
              return (
                <div
                  key={idx}
                  className={`flex items-start gap-3 p-3 rounded-xl border transition-all ${
                    isUser
                      ? 'bg-indigo-950/20 border-indigo-500/20 ml-4'
                      : 'bg-slate-900/60 border-slate-800 mr-4'
                  }`}
                >
                  <div
                    className={`w-7 h-7 rounded-lg shrink-0 flex items-center justify-center text-xs font-semibold ${
                      isUser
                        ? 'bg-indigo-600/30 text-indigo-300 border border-indigo-500/40'
                        : 'bg-emerald-600/30 text-emerald-300 border border-emerald-500/40'
                    }`}
                  >
                    {isUser ? <User className="w-4 h-4" /> : <Users className="w-4 h-4" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span
                        className={`text-xs font-semibold ${
                          isUser ? 'text-indigo-300' : 'text-emerald-300'
                        }`}
                      >
                        {isUser ? 'User (Mic Input)' : 'Participant (System Audio)'}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {new Date(item.timestamp_ms).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-slate-200 text-sm leading-relaxed">{item.text}</p>
                  </div>
                </div>
              );
            })
          )}
          <div ref={transcriptEndRef} />
        </div>
      </div>

      {/* 90-Second Incremental Live Summary Drawer (1 Col) */}
      <div className="flex flex-col glass-card rounded-2xl p-5 border border-slate-800 shadow-xl overflow-hidden">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <h3 className="font-semibold text-sm text-white">90-Sec Live Highlights</h3>
          </div>
          <span className="text-[10px] text-indigo-400 bg-indigo-950 border border-indigo-500/30 px-2 py-0.5 rounded-full flex items-center gap-1 font-mono">
            <Clock className="w-3 h-3" /> Auto 90s
          </span>
        </div>

        <div className="flex-1 overflow-y-auto space-y-4 text-xs pr-1">
          {/* Key Highlights */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <p className="font-semibold text-slate-300 mb-2 flex items-center gap-1.5 text-xs">
              <Layers className="w-3.5 h-3.5 text-indigo-400" /> Key Live Highlights:
            </p>
            <ul className="space-y-1.5 text-slate-300">
              {liveSummary.highlights.map((h, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-indigo-400 shrink-0">•</span>
                  <span>{h}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Active Topics */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <p className="font-semibold text-slate-300 mb-2 text-xs">Mentioned Topics:</p>
            <div className="flex flex-wrap gap-1.5">
              {liveSummary.topics.map((t, i) => (
                <span
                  key={i}
                  className="bg-indigo-950/80 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded-md text-[11px]"
                >
                  #{t}
                </span>
              ))}
            </div>
          </div>

          {/* Emerging Consensus */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5">
            <p className="font-semibold text-slate-300 mb-2 text-xs">Emerging Consensus:</p>
            {liveSummary.consensus.length > 0 ? (
              <ul className="space-y-1 text-slate-300">
                {liveSummary.consensus.map((c, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-emerald-400">✓</span>
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-slate-500 italic text-[11px]">Discussion in progress...</p>
            )}
          </div>

          {/* Generated MoM preview card if session just ended */}
          {lastGeneratedMoM && (
            <div className="bg-emerald-950/40 border border-emerald-500/30 rounded-xl p-3.5 text-emerald-200">
              <div className="flex items-center gap-1.5 text-xs font-semibold mb-1 text-emerald-300">
                <FileCheck className="w-4 h-4" /> MoM Generated & Archived!
              </div>
              <p className="text-[11px] text-emerald-300/80">
                Action Items auto-posted to webhooks. View full MoM in Session History dashboard.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
