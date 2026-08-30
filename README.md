# 🎙️ Meet AI

### An invisible, offline AI meeting co-pilot.

**Real-time transcription · Local AI · Meeting intelligence · Automated MoM · Webhooks**

> Meet AI is an OS-level AI meeting assistant that listens to your meetings, understands the conversation in real time, generates structured Minutes of Meeting, and turns action items into automated workflows — all while keeping AI processing on your machine.

---

## 🧠 What is Meet AI?

Meet AI is designed to work **alongside your meetings without becoming another participant**.

Instead of joining your Google Meet, Zoom, Teams, or other meeting as a bot, Meet AI works at the **OS level**.

It captures:

* 🎤 Your microphone
* 🔊 System audio from other participants
* 📝 Real-time conversation
* 🧠 Meeting context

and processes them locally using **Faster-Whisper + Ollama**.

### The idea is simple:

```text
              🎙️ MEETING
                  │
          ┌───────┴────────┐
          │                │
      🎤 Microphone    🔊 System Audio
          │                │
          └───────┬────────┘
                  ↓
          ┌───────────────┐
          │   Meet AI     │
          │ Local Engine  │
          └───────┬───────┘
                  ↓
        ┌─────────┼─────────┐
        ↓         ↓         ↓
   Transcribe   Understand  Store
        │         │         │
        └─────────┼─────────┘
                  ↓
             📝 MoM
                  ↓
          ⚡ Action Items
                  ↓
            🔗 Webhooks
```

---

# ✨ Features

## 🔒 100% Local AI Processing

Meet AI is built around a **privacy-first architecture**.

Audio transcription, LLM inference, SQLite storage, and vector-based retrieval run locally on the host machine.

### Local stack

| Purpose           | Technology         |
| ----------------- | ------------------ |
| Speech-to-Text    | Faster-Whisper     |
| Local LLM         | Ollama             |
| LLM Model         | Qwen 2.5           |
| Database          | SQLite             |
| Retrieval         | Vector RAG         |
| Desktop Framework | Tauri              |
| Audio Capture     | Rust + CPAL        |
| Frontend          | React + TypeScript |

> **Your meeting data stays on your machine by default.**

---

# 🎧 OS-Level Dual Audio Capture

Meet AI doesn't need to join your meeting.

It captures two separate audio sources:

```text
🎤 Microphone
      │
      ├──────────────┐
      │              │
      ↓              ↓
   Your Voice    🔊 System Audio
                     │
                     ↓
              Other Participants
```

This allows Meet AI to understand **both sides of the conversation** without requiring:

* ❌ Meeting bots
* ❌ Browser extensions
* ❌ Virtual audio cables

The audio capture layer is implemented using **Rust + CPAL through Tauri**.

---

# 🥷 Stealth Overlay

Need to ask the AI something without leaving your meeting?

Meet AI provides a translucent floating prompt bar that can be toggled using a global keyboard shortcut.

### Default shortcuts

```text
Ctrl + Space
      or
Alt + Space
```

The overlay can query the **recent meeting context** while keeping your meeting window in focus.

```text
┌───────────────────────────────────────┐
│                                       │
│          Your Meeting                 │
│                                       │
│                                       │
│      ┌─────────────────────────┐      │
│      │ Ask Meet AI...           │      │
│      └─────────────────────────┘      │
│                                       │
└───────────────────────────────────────┘
```

---

# ⚡ Real-Time Transcription

Meet AI streams meeting audio through a local **Faster-Whisper WebSocket server**.

The result is a continuously updated transcript while the meeting is happening.

```text
🎙️ Live Transcript

──────────────────────────────────────

10:32:14
"We need to finish the API integration
before Friday."

10:32:27
"I'll handle the backend changes."

10:32:41
"Perfect. I'll take care of testing."

──────────────────────────────────────
```

---

# 🧠 Incremental Meeting Intelligence

Meet AI doesn't wait until the meeting ends to understand what's happening.

A background process generates **incremental summaries every 90 seconds**, tracking:

* Key highlights
* Mentioned topics
* Emerging consensus
* Important conversation context

This gives you a continuously evolving understanding of the meeting.

```text
Meeting starts
      ↓
90 sec → Summary
      ↓
90 sec → Updated summary
      ↓
90 sec → Updated summary
      ↓
      ...
      ↓
Meeting ends
      ↓
Final MoM
```

---

# 📝 Structured Minutes of Meeting

Once the meeting concludes, Meet AI generates a structured **Minutes of Meeting**.

The generated structure includes:

```text
📋 Executive Summary

📌 Key Topics

✅ Decisions Made

🎯 Action Items

❓ Unresolved Questions
```

Example:

```json
{
  "executive_summary": "...",

  "key_topics": [
    "Backend migration",
    "Deployment planning"
  ],

  "decisions_made": [
    "Deployment will happen on Friday"
  ],

  "action_items": [
    {
      "task": "Create deployment ticket",
      "owner": "Developer"
    }
  ],

  "unresolved_questions": [
    "Who will handle production monitoring?"
  ]
}
```

The structured output makes the meeting information easy to store, search, and automate.

---

# 🗂️ Meeting Session Archive

Every meeting becomes a searchable session.

Meet AI stores meeting information locally using **SQLite** and makes it available through vector-based retrieval.

Instead of manually going through old transcripts, you can search your meeting history using semantic context.

```text
Past Meetings
      │
      ├── Meeting 01
      ├── Meeting 02
      ├── Meeting 03
      └── Meeting 04
             │
             ↓
          Vector RAG
             │
             ↓
       Relevant Context
```

This turns your previous meetings into a **local knowledge base**.

---

# 🔗 Automated Webhook Dispatcher

The meeting doesn't have to end with a PDF or a block of notes.

Meet AI can automatically dispatch extracted action items through HTTP webhooks.

### Supported workflows

```text
Meet AI
   │
   ↓
Action Items
   │
   ├──→ Notion
   ├──→ Trello
   ├──→ Zapier
   ├──→ n8n
   └──→ Custom REST API
```

For development and testing, the project also includes a mock webhook receiver:

```text
http://localhost:8080/webhook
```

---

# 🏗️ Architecture

Meet AI is built as a multi-layer desktop application.

```text
                    ┌─────────────────────┐
                    │   React + TypeScript│
                    │       Frontend      │
                    └──────────┬──────────┘
                               │
                              Tauri
                               │
                    ┌──────────▼──────────┐
                    │     Rust Layer      │
                    │                     │
                    │  • Audio Capture    │
                    │  • Global Hotkeys   │
                    │  • App State        │
                    └──────────┬──────────┘
                               │
                          WebSocket
                               │
                    ┌──────────▼──────────┐
                    │   Python AI Engine  │
                    │                     │
                    │ • Faster-Whisper    │
                    │ • Ollama             │
                    │ • RAG                │
                    │ • SQLite             │
                    │ • Webhooks           │
                    └─────────────────────┘
```

### Data flow

```text
Audio
  ↓
Rust / CPAL
  ↓
WebSocket
  ↓
Faster-Whisper
  ↓
Live Transcript
  ↓
Local AI / Ollama
  ↓
Summary + Meeting Intelligence
  ↓
SQLite + Vector Storage
  ↓
Structured MoM
  ↓
Webhook Dispatcher
```

---

# 📂 Project Structure

```text
meet-ai/
│
├── src/
│   ├── components/
│   │   ├── StealthPromptBar.tsx
│   │   ├── LiveTranscriptionView.tsx
│   │   ├── SessionHistory.tsx
│   │   └── SettingsWebhook.tsx
│   │
│   ├── hooks/
│   └── App.tsx
│
├── src-tauri/
│   ├── src/
│   │   ├── audio/
│   │   │   └── CPAL audio loopback
│   │   ├── hotkey/
│   │   │   └── Global hotkey handling
│   │   ├── state.rs
│   │   └── main.rs
│   │
│   ├── Cargo.toml
│   └── tauri.conf.json
│
├── python-engine/
│   ├── stt_server.py
│   ├── mom_generator.py
│   ├── webhook_dispatcher.py
│   ├── database.py
│   └── requirements.txt
│
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── README.md
```

---

# 🛠️ Tech Stack

### Frontend

* ⚛️ React
* 📘 TypeScript
* ⚡ Vite
* 🎨 Tailwind CSS

### Desktop

* 🦀 Rust
* 🖥️ Tauri
* 🎧 CPAL

### AI

* 🗣️ Faster-Whisper
* 🧠 Ollama
* 🤖 Qwen 2.5

### Data

* 🗄️ SQLite
* 🔎 Vector RAG

### Communication

* 🔌 WebSockets
* 🌐 HTTP Webhooks

---

# 🚀 Running Meet AI

## 1. Start Ollama

Make sure Ollama is installed and running with one of the supported models.

### Recommended

```bash
ollama run qwen2.5:7b
```

### Lower-resource alternatives

```bash
ollama run qwen2.5:3b
```

or

```bash
ollama run llama3.2:3b
```

---

## 2. Start the Python AI Engine

```bash
python python-engine/stt_server.py
```

This starts the local transcription engine.

---

## 3. Start the Desktop Interface

```bash
npm install
npm run dev
```

The development interface runs on:

```text
http://localhost:1420
```

---

# 🔐 Privacy

Meet AI is designed around one principle:

> **Your meetings should remain your data.**

The core AI pipeline is local:

```text
🎤 Audio
   ↓
🖥️ Local Processing
   ↓
🗣️ Local Transcription
   ↓
🧠 Local LLM
   ↓
🗄️ Local Storage
   ↓
🔎 Local Retrieval
```

No external AI API is required for the core meeting workflow.

External services are only used when you explicitly configure webhook integrations.

---

# 🎯 Why Meet AI?

Traditional meeting assistants often require a bot to join the call.

Meet AI takes another approach:

| Traditional Meeting Bot    | Meet AI                         |
| -------------------------- | ------------------------------- |
| 🤖 Joins your meeting      | 🥷 Works at OS level            |
| ☁️ Often cloud-dependent   | 🖥️ Local AI processing         |
| 🎙️ Captures meeting audio | 🎤 Captures system + microphone |
| 📝 Generates notes         | 🧠 Generates structured MoM     |
| 📄 Notes after meeting     | ⚡ Incremental intelligence      |
| 🔗 External integrations   | 🔗 Webhook automation           |

---

# 🧩 Engineering Highlights

Meet AI combines several different areas of software engineering into one application:

### 🦀 Systems Programming

Rust handles OS-level functionality such as audio capture and global hotkeys.

### ⚛️ Modern Frontend

React + TypeScript provides the desktop interface and real-time meeting experience.

### 🐍 AI Engineering

Python handles transcription, local model interaction, session processing, and webhook dispatching.

### 🧠 Local LLMs

Ollama enables LLM inference without requiring a cloud AI provider.

### 🔎 Retrieval-Augmented Generation

Meeting sessions are stored and retrieved using vector-based search.

### 🔗 Automation

Structured action items can be pushed into external workflows through HTTP webhooks.

---

# 🚧 Current Status

Meet AI is currently an **active development project**.

The current implementation focuses on:

* ✅ Local transcription
* ✅ OS-level audio capture
* ✅ Stealth prompt interface
* ✅ Incremental summaries
* ✅ Structured MoM generation
* ✅ Session archive
* ✅ Vector retrieval
* ✅ Webhook automation
* ✅ Local LLM inference

---

# 🗺️ What's Next?

The project can evolve toward:

```text
Current
  │
  ├── Live Transcription
  ├── Local AI
  ├── MoM
  ├── RAG
  └── Automation
          │
          ▼
Future
  │
  ├── Speaker Diarization
  ├── Meeting Analytics
  ├── Better Search
  ├── Calendar Integration
  ├── More Integrations
  └── Advanced Meeting Intelligence
```

---

# 💭 The Idea Behind Meet AI

Meetings contain valuable information.

But once the meeting ends, that information is often scattered across:

* Memory
* Chat messages
* Notes
* Documents
* Task managers

Meet AI tries to close that gap.

```text
             CONVERSATION
                   ↓
              TRANSCRIPTION
                   ↓
             UNDERSTANDING
                   ↓
                MEMORY
                   ↓
                ACTION
```

### **Listen. Understand. Remember. Automate.**

---

# ⭐ If you find this project interesting

Check out the repository and feel free to experiment, suggest improvements, or contribute.

**Built with React, TypeScript, Rust, Python and local AI.**

---

<div align="center">

### 🎙️ Meet AI

**An invisible AI co-pilot for your meetings.**

🔒 Local · 🧠 Intelligent · ⚡ Automated

</div>
