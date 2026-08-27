import asyncio
import json
import time
import uuid
import threading
import queue
import numpy as np
import sounddevice as sd
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import requests

from faster_whisper import WhisperModel
import database
import mom_generator
import webhook_dispatcher

# Initialize Database & Mock Webhook Endpoint
database.init_db()
webhook_dispatcher.start_mock_webhook_server(8080)

app = FastAPI(title="Adrishyaa Local STT & AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
active_session_id = None
is_recording = False
transcript_buffer = []  # 15-minute sliding window memory
connected_clients = set()
whisper_model = None
audio_lock = threading.Lock()

# Audio settings
SAMPLE_RATE = 16000
CHUNK_DURATION = 3.0  # seconds per audio slice
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)

def load_whisper():
    global whisper_model
    if whisper_model is None:
        print("[STT Server] Loading Faster-Whisper 'base.en' model...")
        try:
            whisper_model = WhisperModel("base.en", device="cpu", compute_type="int8")
            print("[STT Server] Whisper model loaded successfully.")
        except Exception as e:
            print(f"[STT Server Error] Failed to load whisper model: {e}")
            try:
                whisper_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
                print("[STT Server] Fallback to 'tiny.en' whisper model succeeded.")
            except Exception as e2:
                print(f"[STT Server Fatal] {e2}")
# Audio Loopback & Microphone Stream Ingestion
def audio_capture_worker(loop):
    """Captures real OS microphone and system audio streams and transcribes using Faster-Whisper."""
    global is_recording, active_session_id, transcript_buffer, whisper_model
    
    print("[Audio Capture] Starting real live microphone audio capture stream...")
    audio_queue = queue.Queue()

    def audio_callback(indata, frames, time_info, status):
        if is_recording:
            audio_queue.put(indata.copy().flatten())

    stream = None
    try:
        stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype='float32',
            callback=audio_callback,
            blocksize=4000
        )
        stream.start()
        print("[Audio Capture] Real-time sounddevice InputStream active.")
    except Exception as e:
        print(f"[Audio Capture Error] Could not start sounddevice InputStream: {e}")

    audio_buffer = np.array([], dtype=np.float32)

    while True:
        if not is_recording:
            audio_buffer = np.array([], dtype=np.float32)
            # Drain queue if paused
            while not audio_queue.empty():
                try:
                    audio_queue.get_nowait()
                except Exception:
                    break
            time.sleep(0.3)
            continue

        # Collect audio chunks from queue
        while not audio_queue.empty():
            try:
                chunk = audio_queue.get_nowait()
                audio_buffer = np.append(audio_buffer, chunk)
            except Exception:
                break

        # Process every CHUNK_SIZE (approx 3.0s = 48000 samples)
        if len(audio_buffer) >= CHUNK_SIZE:
            current_chunk = audio_buffer[:CHUNK_SIZE]
            audio_buffer = audio_buffer[CHUNK_SIZE:]

            if not active_session_id:
                continue

            # Calculate Root Mean Square (RMS) energy to detect voice/speech
            rms = np.sqrt(np.mean(current_chunk ** 2))

            if rms > 0.005 and whisper_model is not None:
                try:
                    segments, info = whisper_model.transcribe(
                        current_chunk,
                        beam_size=1,
                        vad_filter=True
                    )
                    text = " ".join([seg.text.strip() for seg in segments if seg.text.strip()]).strip()

                    if text and len(text) > 1:
                        now_ms = int(time.time() * 1000)
                        # Alternate speaker label or tag based on session context if needed
                        speaker = "User"
                        item = {
                            "session_id": active_session_id,
                            "speaker": speaker,
                            "text": text,
                            "timestamp_ms": now_ms,
                            "confidence": 0.95
                        }

                        # Store in SQLite and Memory Buffer
                        database.save_transcript_item(active_session_id, speaker, text, now_ms, 0.95)

                        with audio_lock:
                            transcript_buffer.append(item)
                            if len(transcript_buffer) > 200:
                                transcript_buffer.pop(0)

                        # Broadcast via WebSockets
                        print(f"[Live STT] Real Transcript: {text}")
                        asyncio.run_coroutine_threadsafe(broadcast_event("transcript", item), loop)
                except Exception as stt_err:
                    print(f"[STT Transcription Error] {stt_err}")

        time.sleep(0.1)

async def broadcast_event(event_type: str, data: dict):
    message = json.dumps({"type": event_type, "data": data})
    disconnected = set()
    for client in connected_clients:
        try:
            await client.send_text(message)
        except Exception:
            disconnected.add(client)
    for client in disconnected:
        connected_clients.remove(client)

# WebSockets Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    print(f"[WebSocket] Client connected. Total: {len(connected_clients)}")

    # Send initial state
    ollama_health = mom_generator.check_ollama_status()
    await websocket.send_text(json.dumps({
        "type": "init_state",
        "data": {
            "active_session_id": active_session_id,
            "is_recording": is_recording,
            "ollama_status": ollama_health,
            "transcript_buffer": transcript_buffer[-30:] # last 30 items
        }
    }))

    try:
        while True:
            data_str = await websocket.receive_text()
            try:
                msg = json.loads(data_str)
                msg_type = msg.get("type")
                payload = msg.get("data", {})

                if msg_type == "start_session":
                    await handle_start_session(payload.get("title", "Live Meeting Session"))
                elif msg_type == "end_session":
                    await handle_end_session()
                elif msg_type == "stealth_query":
                    question = payload.get("question", "")
                    answer = mom_generator.answer_stealth_prompt(question, transcript_buffer)
                    await websocket.send_text(json.dumps({
                        "type": "stealth_answer",
                        "data": {"question": question, "answer": answer}
                    }))
                elif msg_type == "check_ollama":
                    health = mom_generator.check_ollama_status()
                    await websocket.send_text(json.dumps({
                        "type": "ollama_status",
                        "data": health
                    }))
            except Exception as e:
                print(f"[WS Error] {e}")
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        print(f"[WebSocket] Client disconnected. Remaining: {len(connected_clients)}")

async def handle_start_session(title: str):
    global active_session_id, is_recording, transcript_buffer
    active_session_id = f"session-{uuid.uuid4().hex[:8]}"
    is_recording = True
    with audio_lock:
        transcript_buffer.clear()
    
    session = database.save_session(active_session_id, title, time.time(), "active")
    print(f"[Session Started] ID: {active_session_id}")
    await broadcast_event("session_started", session)

async def handle_end_session():
    global active_session_id, is_recording
    if not active_session_id:
        return

    sid = active_session_id
    is_recording = False
    ended = database.end_session(sid, time.time())
    
    # Generate MoM
    transcripts = database.get_session_transcripts(sid)
    mom_data = mom_generator.generate_mom(transcripts)
    database.save_mom(sid, mom_data)
    
    # Auto-dispatch webhooks
    webhook_results = webhook_dispatcher.dispatch_session_action_items(
        sid, mom_data.get("action_items", []), mom_data.get("executive_summary", "")
    )

    result = {
        "session": ended,
        "mom": mom_data,
        "webhook_results": webhook_results
    }
    
    active_session_id = None
    print(f"[Session Ended] ID: {sid}")
    await broadcast_event("session_ended", result)

# REST API Endpoints for Frontend Interaction
@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "is_recording": is_recording,
        "active_session_id": active_session_id,
        "ollama": mom_generator.check_ollama_status()
    }

class SessionStartRequest(BaseModel):
    title: str = "Live Meeting Session"

@app.post("/api/sessions/start")
async def api_start_session(req: SessionStartRequest):
    await handle_start_session(req.title)
    return {"status": "started", "session_id": active_session_id}

@app.post("/api/sessions/end")
async def api_end_session():
    sid = active_session_id
    await handle_end_session()
    return {"status": "ended", "session_id": sid}

@app.get("/api/sessions")
def api_list_sessions(query: str = ""):
    if query.strip():
        return database.search_sessions_semantic(query)
    return database.list_all_sessions()

@app.get("/api/sessions/{session_id}")
def api_get_session_detail(session_id: str):
    transcripts = database.get_session_transcripts(session_id)
    mom = database.get_session_mom(session_id)
    return {
        "session_id": session_id,
        "transcripts": transcripts,
        "mom": mom
    }

class StealthQueryRequest(BaseModel):
    question: str

@app.post("/api/stealth/query")
def api_stealth_query(req: StealthQueryRequest):
    answer = mom_generator.answer_stealth_prompt(req.question, transcript_buffer)
    return {"question": req.question, "answer": answer}

@app.get("/api/live-summary")
def api_live_summary():
    summary = mom_generator.generate_live_summary(transcript_buffer)
    return summary

# Webhook Management Endpoints
@app.get("/api/webhooks")
def api_get_webhooks():
    return database.get_webhooks()

class WebhookRequest(BaseModel):
    id: str
    name: str
    url: str
    is_active: bool = True
    headers: dict = {}

@app.post("/api/webhooks")
def api_save_webhook(req: WebhookRequest):
    return database.save_webhook(req.id, req.name, req.url, req.is_active, req.headers)

@app.delete("/api/webhooks/{webhook_id}")
def api_delete_webhook(webhook_id: str):
    database.delete_webhook(webhook_id)
    return {"status": "deleted", "id": webhook_id}

@app.get("/api/webhooks/logs")
def api_get_webhook_logs(webhook_id: str = None):
    return database.get_webhook_logs(webhook_id)

class RetriggerRequest(BaseModel):
    webhook_id: str
    session_id: str

@app.post("/api/webhooks/retrigger")
def api_retrigger_webhook(req: RetriggerRequest):
    return webhook_dispatcher.retrigger_webhook_for_session(req.webhook_id, req.session_id)

@app.on_event("startup")
def startup_event():
    load_whisper()
    loop = asyncio.get_event_loop()
    threading.Thread(target=audio_capture_worker, args=(loop,), daemon=True).start()

if __name__ == "__main__":
    print("==================================================")
    print("  Adrishyaa-Local STT & AI Engine Starting...")
    print("  WebSocket: ws://localhost:8765/ws")
    print("  REST API:  http://localhost:8765/api/health")
    print("==================================================")
    uvicorn.run(app, host="0.0.0.0", port=8765)
