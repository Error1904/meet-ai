import sqlite3
import json
import os
import time
import math
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "adrishyaa.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        start_time REAL NOT NULL,
        end_time REAL,
        duration_seconds INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transcripts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        speaker TEXT NOT NULL,
        text TEXT NOT NULL,
        timestamp_ms INTEGER NOT NULL,
        confidence REAL DEFAULT 1.0,
        FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS moms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE NOT NULL,
        executive_summary TEXT NOT NULL,
        key_topics TEXT NOT NULL,
        decisions_made TEXT NOT NULL,
        action_items TEXT NOT NULL,
        unresolved_questions TEXT NOT NULL,
        created_at REAL NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS webhooks (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        headers TEXT DEFAULT '{}',
        created_at REAL NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS webhook_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        webhook_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        status_code INTEGER,
        request_payload TEXT,
        response_body TEXT,
        timestamp REAL NOT NULL
    )
    """)

    # Default Mock Webhook if empty
    cursor.execute("SELECT COUNT(*) as count FROM webhooks")
    if cursor.fetchone()["count"] == 0:
        cursor.execute(
            "INSERT INTO webhooks (id, name, url, is_active, headers, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("mock-webhook-1", "Local Test Endpoint", "http://localhost:8080/webhook", 1, "{}", time.time())
        )

    conn.commit()
    conn.close()

def save_session(session_id: str, title: str, start_time: float, status: str = "active") -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO sessions (id, title, start_time, status) VALUES (?, ?, ?, ?)",
        (session_id, title, start_time, status)
    )
    conn.commit()
    conn.close()
    return {"id": session_id, "title": title, "start_time": start_time, "status": status}

def end_session(session_id: str, end_time: float) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT start_time FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    start_time = row["start_time"]
    duration = int(end_time - start_time)
    cursor.execute(
        "UPDATE sessions SET end_time = ?, duration_seconds = ?, status = 'completed' WHERE id = ?",
        (end_time, duration, session_id)
    )
    conn.commit()
    conn.close()
    return {"id": session_id, "end_time": end_time, "duration_seconds": duration, "status": "completed"}

def save_transcript_item(session_id: str, speaker: str, text: str, timestamp_ms: int, confidence: float = 1.0):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transcripts (session_id, speaker, text, timestamp_ms, confidence) VALUES (?, ?, ?, ?, ?)",
        (session_id, speaker, text, timestamp_ms, confidence)
    )
    conn.commit()
    conn.close()

def get_session_transcripts(session_id: str) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT speaker, text, timestamp_ms, confidence FROM transcripts WHERE session_id = ? ORDER BY timestamp_ms ASC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_mom(session_id: str, mom_data: Dict[str, Any]):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT OR REPLACE INTO moms 
           (session_id, executive_summary, key_topics, decisions_made, action_items, unresolved_questions, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            session_id,
            mom_data.get("executive_summary", ""),
            json.dumps(mom_data.get("key_topics", [])),
            json.dumps(mom_data.get("decisions_made", [])),
            json.dumps(mom_data.get("action_items", [])),
            json.dumps(mom_data.get("unresolved_questions", [])),
            time.time()
        )
    )
    conn.commit()
    conn.close()

def get_session_mom(session_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM moms WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "session_id": row["session_id"],
        "executive_summary": row["executive_summary"],
        "key_topics": json.loads(row["key_topics"]),
        "decisions_made": json.loads(row["decisions_made"]),
        "action_items": json.loads(row["action_items"]),
        "unresolved_questions": json.loads(row["unresolved_questions"]),
        "created_at": row["created_at"]
    }

def list_all_sessions() -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions ORDER BY start_time DESC")
    sessions = [dict(r) for r in cursor.fetchall()]
    
    # Attach MoM status if available
    for s in sessions:
        mom = get_session_mom(s["id"])
        s["has_mom"] = mom is not None
        s["mom"] = mom
    conn.close()
    return sessions

def search_sessions_semantic(query: str) -> List[Dict[str, Any]]:
    """Local semantic/text search across stored meeting transcripts and MoMs."""
    if not query.strip():
        return list_all_sessions()
        
    query_terms = [q.lower() for q in query.strip().split()]
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sessions ORDER BY start_time DESC")
    sessions = [dict(r) for r in cursor.fetchall()]
    
    results = []
    for s in sessions:
        transcripts = get_session_transcripts(s["id"])
        mom = get_session_mom(s["id"])
        s["has_mom"] = mom is not None
        s["mom"] = mom
        
        full_text = " ".join([t["text"] for t in transcripts])
        if mom:
            full_text += " " + mom["executive_summary"] + " " + " ".join(mom["key_topics"]) + " " + " ".join(mom["decisions_made"])
        
        full_text_lower = full_text.lower()
        score = sum(full_text_lower.count(term) for term in query_terms)
        
        if score > 0 or query.lower() in s["title"].lower():
            s["relevance_score"] = score + (5 if query.lower() in s["title"].lower() else 0)
            results.append(s)
            
    results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    conn.close()
    return results

def get_webhooks() -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM webhooks ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["headers"] = json.loads(d["headers"])
        result.append(d)
    return result

def save_webhook(id_str: str, name: str, url: str, is_active: bool = True, headers: dict = None) -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO webhooks (id, name, url, is_active, headers, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (id_str, name, url, 1 if is_active else 0, json.dumps(headers or {}), time.time())
    )
    conn.commit()
    conn.close()
    return {"id": id_str, "name": name, "url": url, "is_active": is_active, "headers": headers or {}}

def delete_webhook(id_str: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM webhooks WHERE id = ?", (id_str,))
    conn.commit()
    conn.close()

def log_webhook_execution(webhook_id: str, session_id: str, status_code: int, payload: dict, response_body: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO webhook_logs (webhook_id, session_id, status_code, request_payload, response_body, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (webhook_id, session_id, status_code, json.dumps(payload), response_body, time.time())
    )
    conn.commit()
    conn.close()

def get_webhook_logs(webhook_id: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    if webhook_id:
        cursor.execute("SELECT * FROM webhook_logs WHERE webhook_id = ? ORDER BY timestamp DESC LIMIT 50", (webhook_id,))
    else:
        cursor.execute("SELECT * FROM webhook_logs ORDER BY timestamp DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        d["request_payload"] = json.loads(d["request_payload"])
        res.append(d)
    return res

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
