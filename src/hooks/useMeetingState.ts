import { useState, useEffect, useRef, useCallback } from 'react';

export interface TranscriptItem {
  session_id: string;
  speaker: 'User' | 'Participant' | string;
  text: string;
  timestamp_ms: number;
  confidence?: number;
}

export interface OllamaStatus {
  online: boolean;
  url: string;
  models: string[];
  selected_model?: string;
  error?: string;
}

export interface LiveSummary {
  highlights: string[];
  topics: string[];
  consensus: string[];
}

const API_BASE = 'http://localhost:8765/api';
const WS_URL = 'ws://localhost:8765/ws';

export function useMeetingState() {
  const [isConnected, setIsConnected] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [transcriptBuffer, setTranscriptBuffer] = useState<TranscriptItem[]>([]);
  const [ollamaStatus, setOllamaStatus] = useState<OllamaStatus>({
    online: false,
    url: 'http://localhost:11434',
    models: []
  });
  const [liveSummary, setLiveSummary] = useState<LiveSummary>({
    highlights: ['Listening for active meeting conversation...'],
    topics: ['Initialization'],
    consensus: []
  });

  const wsRef = useRef<WebSocket | null>(null);

  // Connect WebSocket
  const connectWebSocket = useCallback(() => {
    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        // Check Ollama status
        ws.send(JSON.stringify({ type: 'check_ollama' }));
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'init_state') {
            setIsRecording(msg.data.is_recording);
            setActiveSessionId(msg.data.active_session_id);
            if (msg.data.ollama_status) setOllamaStatus(msg.data.ollama_status);
            if (msg.data.transcript_buffer) setTranscriptBuffer(msg.data.transcript_buffer);
          } else if (msg.type === 'transcript') {
            setTranscriptBuffer((prev) => [...prev.slice(-150), msg.data]);
          } else if (msg.type === 'session_started') {
            setIsRecording(true);
            setActiveSessionId(msg.data.id);
            setTranscriptBuffer([]);
          } else if (msg.type === 'session_ended') {
            setIsRecording(false);
            setActiveSessionId(null);
          } else if (msg.type === 'ollama_status') {
            setOllamaStatus(msg.data);
          }
        } catch (e) {
          console.error('[WS Msg Error]', e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Retry connection after 3s
        setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = () => {
        setIsConnected(false);
      };
    } catch (err) {
      console.error('[WS Connect Error]', err);
      setTimeout(connectWebSocket, 3000);
    }
  }, []);

  useEffect(() => {
    connectWebSocket();
    return () => {
      wsRef.current?.close();
    };
  }, [connectWebSocket]);

  // Periodic 90-second incremental live summary
  useEffect(() => {
    if (!isRecording) return;

    const fetchSummary = async () => {
      try {
        const res = await fetch(`${API_BASE}/live-summary`);
        if (res.ok) {
          const data = await res.json();
          setLiveSummary(data);
        }
      } catch (err) {
        console.error('[Live Summary Error]', err);
      }
    };

    fetchSummary();
    const interval = setInterval(fetchSummary, 90000); // 90 seconds
    return () => clearInterval(interval);
  }, [isRecording]);

  const checkOllamaHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        const data = await res.json();
        setOllamaStatus(data.ollama);
        return data.ollama;
      }
    } catch (err) {
      setOllamaStatus((prev) => ({ ...prev, online: false }));
    }
    return { online: false, url: 'http://localhost:11434', models: [] };
  };

  const startSession = async (title: string = 'Live Meeting Session') => {
    try {
      const res = await fetch(`${API_BASE}/sessions/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      });
      if (res.ok) {
        const data = await res.json();
        setIsRecording(true);
        setActiveSessionId(data.session_id);
        setTranscriptBuffer([]);
      }
    } catch (err) {
      console.error('[Start Session Error]', err);
    }
  };

  const endSession = async () => {
    try {
      const res = await fetch(`${API_BASE}/sessions/end`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setIsRecording(false);
        setActiveSessionId(null);
        return data;
      }
    } catch (err) {
      console.error('[End Session Error]', err);
    }
    return null;
  };

  const queryStealthBar = async (question: string): Promise<string> => {
    try {
      const res = await fetch(`${API_BASE}/stealth/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });
      if (res.ok) {
        const data = await res.json();
        return data.answer || 'No response generated.';
      }
    } catch (err) {
      console.error('[Stealth Query Error]', err);
    }
    return 'Could not connect to AI engine.';
  };

  return {
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
  };
}
