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
import pyaudiowpatch as pyaudio

# Audio Loopback & Microphone Stream Ingestion
def audio_capture_worker(loop):
    """Captures dual OS audio channels (Microphone + WASAPI System Audio Loopback) and transcribes using Faster-Whisper."""
    global is_recording, active_session_id, transcript_buffer, whisper_model
    
    print("[Audio Capture] Starting OS dual audio capture stream (Mic + WASAPI Loopback)...")
    mic_queue = queue.Queue()
    loopback_queue = queue.Queue()

    p = pyaudio.PyAudio()

    # Discover WASAPI loopback device (for other meeting participants' voice output)
    loopback_dev = None
    try:
        wasapi = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_out = p.get_device_info_by_index(wasapi['defaultOutputDevice'])
        for d in p.get_device_info_generator():
            if d.get('isLoopbackDevice') and default_out['name'] in d['name']:
                loopback_dev = d
                break
        if not loopback_dev:
            loopback_dev = next((d for d in p.get_device_info_generator() if d.get('isLoopbackDevice')), None)
    except Exception as e:
        print(f"[Audio Capture Warning] WASAPI discovery failed: {e}")

    # Discover microphone input device (for user's voice input)
    mic_dev = None
    try:
        mic_dev = p.get_default_input_device_info()
    except Exception as e:
        print(f"[Audio Capture Warning] Default mic discovery failed: {e}")

    # Callbacks
    def mic_callback(in_data, frame_count, time_info, status):
        if is_recording:
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            mic_queue.put(audio_data)
        return (None, pyaudio.paContinue)

    def loopback_callback(in_data, frame_count, time_info, status):
        if is_recording:
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            if loopback_dev and loopback_dev['maxInputChannels'] > 1:
                audio_data = audio_data.reshape(-1, loopback_dev['maxInputChannels']).mean(axis=1)
            loopback_queue.put((audio_data, int(loopback_dev['defaultSampleRate']) if loopback_dev else 48000))
        return (None, pyaudio.paContinue)

    # Start audio streams
    stream_mic = None
    if mic_dev:
        try:
            stream_mic = p.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=mic_dev['index'],
                stream_callback=mic_callback
            )
            stream_mic.start_stream()
            print(f"[Audio Capture] Microphone stream started: {mic_dev['name']}")
        except Exception as e:
            print(f"[Audio Capture Error] Failed to start mic stream: {e}")

    stream_loop = None
    if loopback_dev:
        try:
            stream_loop = p.open(
                format=pyaudio.paFloat32,
                channels=loopback_dev['maxInputChannels'],
                rate=int(loopback_dev['defaultSampleRate']),
                input=True,
                input_device_index=loopback_dev['index'],
                stream_callback=loopback_callback
            )
            stream_loop.start_stream()
            print(f"[Audio Capture] WASAPI System Audio Loopback stream started: {loopback_dev['name']}")
        except Exception as e:
            print(f"[Audio Capture Error] Failed to start loopback stream: {e}")

    mic_buffer = np.array([], dtype=np.float32)
    loopback_buffer = np.array([], dtype=np.float32)

    def resample_to_16k(audio, orig_sr):
        if orig_sr == 16000:
            return audio
        num_output_samples = int(len(audio) * 16000 / orig_sr)
        if num_output_samples <= 0:
            return np.array([], dtype=np.float32)
        x_old = np.linspace(0, 1, len(audio))
        x_new = np.linspace(0, 1, num_output_samples)
        return np.interp(x_new, x_old, audio).astype(np.float32)

    def process_speech_chunk(chunk, speaker_name):
        if len(chunk) < CHUNK_SIZE or not active_session_id or whisper_model is None:
            return
        rms = np.sqrt(np.mean(chunk ** 2))
        if rms > 0.005:  # Voice activity detected above background noise
            try:
                segments, info = whisper_model.transcribe(
                    chunk,
                    beam_size=1,
                    vad_filter=True
                )
                text = " ".join([seg.text.strip() for seg in segments if seg.text.strip()]).strip()
                if text and len(text) > 1:
                    now_ms = int(time.time() * 1000)
                    item = {
                        "session_id": active_session_id,
                        "speaker": speaker_name,
                        "text": text,
                        "timestamp_ms": now_ms,
                        "confidence": 0.95
                    }
                    database.save_transcript_item(active_session_id, speaker_name, text, now_ms, 0.95)
                    with audio_lock:
                        transcript_buffer.append(item)
                        if len(transcript_buffer) > 200:
                            transcript_buffer.pop(0)
                    print(f"[Live STT] [{speaker_name}] {text}")
                    asyncio.run_coroutine_threadsafe(broadcast_event("transcript", item), loop)
            except Exception as stt_err:
                print(f"[STT Error - {speaker_name}] {stt_err}")

    while True:
        if not is_recording:
            mic_buffer = np.array([], dtype=np.float32)
            loopback_buffer = np.array([], dtype=np.float32)
            while not mic_queue.empty():
                try: mic_queue.get_nowait()
                except Exception: break
            while not loopback_queue.empty():
                try: loopback_queue.get_nowait()
                except Exception: break
            time.sleep(0.3)
            continue

        # Drain Mic Queue
        while not mic_queue.empty():
            try:
                data = mic_queue.get_nowait()
                mic_buffer = np.append(mic_buffer, data)
            except Exception:
                break

        # Drain Loopback Queue
        while not loopback_queue.empty():
            try:
                data, orig_sr = loopback_queue.get_nowait()
                data_16k = resample_to_16k(data, orig_sr)
                loopback_buffer = np.append(loopback_buffer, data_16k)
            except Exception:
                break

        # Process Mic Buffer (User)
        if len(mic_buffer) >= CHUNK_SIZE:
            chunk = mic_buffer[:CHUNK_SIZE]
            mic_buffer = mic_buffer[CHUNK_SIZE:]
            process_speech_chunk(chunk, "User")

        # Process Loopback Buffer (Participant)
        if len(loopback_buffer) >= CHUNK_SIZE:
            chunk = loopback_buffer[:CHUNK_SIZE]
            loopback_buffer = loopback_buffer[CHUNK_SIZE:]
            process_speech_chunk(chunk, "Participant")

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
