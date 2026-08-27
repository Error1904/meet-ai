# Adrishyaa-Local

An invisible OS-level AI meeting co-pilot, real-time transcript streaming engine, and automated Minutes of Meeting (MoM) session manager.

---

## Key Features

1. **100% Offline & Zero Cloud Transmission**:
   - Audio transcription, local LLM inferencing (`qwen2.5:7b` via Ollama), SQLite storage, and vector RAG search run entirely on the host machine.
2. **Invisible OS-Level Dual Audio Loopback**:
   - Captures system audio output (other participants) + microphone input (user) on separate channels without meeting bot extensions or virtual audio cables.
3. **Stealth Overlay Prompt Bar**:
   - Translucent floating prompt bar toggled via global desktop hotkey (`Ctrl + Space` / `Alt + Space`).
   - Query the 15-minute sliding window context during active calls without losing focus on meeting windows.
4. **Real-Time Live Summary & Incremental Notes**:
   - Background 90-second incremental summarization tracking key highlights, mentioned topics, and emerging consensus.
5. **Structured MoM Generator & Session Archive**:
   - Formal JSON Minutes of Meeting generation (Executive Summary, Key Topics, Decisions Made, Action Items, Unresolved Questions).
6. **Automated Webhook Dispatcher**:
   - Automatic HTTP POST dispatching of action items upon meeting conclusion to Notion, Trello, Zapier, n8n, or custom REST endpoints.
   - Built-in Mock Webhook receiver on `http://localhost:8080/webhook`.

---

## Directory Structure

```text
adrishyaa-local/
├── src-tauri/
│   ├── src/
│   │   ├── audio/ (cpal audio loopback capture engine)
│   │   ├── hotkey/ (global hotkey listener for stealth bar)
│   │   ├── state.rs (app state management)
│   │   └── main.rs
│   ├── Cargo.toml
│   └── tauri.conf.json
├── python-engine/ (Sidecar for local Whisper & Webhook dispatching)
│   ├── stt_server.py (Faster-Whisper WebSocket server)
│   ├── mom_generator.py (Ollama structured schema caller)
│   ├── webhook_dispatcher.py (Async HTTP webhook delivery)
│   ├── database.py (SQLite vector storage & session archive)
│   └── requirements.txt
├── src/ (React + TypeScript Frontend)
│   ├── components/
│   │   ├── StealthPromptBar.tsx (Floating transparent overlay bar)
│   │   ├── LiveTranscriptionView.tsx (Real-time subtitle feed & 90s summary)
│   │   ├── SessionHistory.tsx (Dashboard & RAG search)
│   │   └── SettingsWebhook.tsx (Webhook configuration UI)
│   ├── hooks/
│   └── App.tsx
└── README.md
```

---

## Running the Application

### 1. Start Ollama Local LLM
Ensure Ollama is running on your machine with `qwen2.5:7b` (or `qwen2.5:3b` / `llama3.2:3b`):
```bash
ollama run qwen2.5:7b
```

### 2. Launch Python AI Engine
```bash
python python-engine/stt_server.py
```

### 3. Launch React Desktop Interface
```bash
npm run dev
```

Open `http://localhost:1420` in your browser or desktop container.
