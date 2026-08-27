import requests
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import List, Dict, Any
import database

class MockWebhookHandler(BaseHTTPRequestHandler):
    received_requests = []

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        try:
            payload = json.loads(post_data)
        except Exception:
            payload = post_data

        entry = {
            "timestamp": time.time(),
            "headers": dict(self.headers),
            "payload": payload
        }
        MockWebhookHandler.received_requests.append(entry)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = json.dumps({"status": "success", "message": "Webhook payload received successfully by mock endpoint", "received_at": time.time()})
        self.wfile.write(response.encode('utf-8'))

    def log_message(self, format, *args):
        pass # Suppress default stdout logging

def start_mock_webhook_server(port: int = 8080):
    """Starts a background HTTP mock webhook receiver on http://localhost:8080/webhook."""
    def run():
        try:
            server = HTTPServer(('localhost', port), MockWebhookHandler)
            print(f"[Mock Webhook Server] Running on http://localhost:{port}/webhook")
            server.serve_forever()
        except Exception as e:
            print(f"[Mock Webhook Server] Could not start on port {port}: {e}")

    t = threading.Thread(target=run, daemon=True)
    t.start()

def send_webhook_payload(webhook: Dict[str, Any], session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = webhook["url"]
    headers = webhook.get("headers", {})
    headers.setdefault("Content-Type", "application/json")
    headers.setdefault("User-Agent", "Adrishyaa-Local-WebhookDispatcher/1.0")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        status_code = response.status_code
        response_text = response.text
    except Exception as e:
        status_code = 500
        response_text = str(e)

    # Log to SQLite
    database.log_webhook_execution(
        webhook_id=webhook["id"],
        session_id=session_id,
        status_code=status_code,
        payload=payload,
        response_body=response_text
    )

    return {
        "webhook_id": webhook["id"],
        "webhook_name": webhook["name"],
        "url": url,
        "status_code": status_code,
        "response": response_text
    }

def dispatch_session_action_items(session_id: str, action_items: List[Dict[str, Any]], executive_summary: str = "") -> List[Dict[str, Any]]:
    """Automatically posts action items to all active configured webhooks."""
    webhooks = database.get_webhooks()
    active_webhooks = [w for w in webhooks if w.get("is_active")]

    payload = {
        "event": "meeting_ended",
        "session_id": session_id,
        "timestamp": time.time(),
        "executive_summary": executive_summary,
        "action_items_count": len(action_items),
        "action_items": action_items,
        "source": "Adrishyaa-Local"
    }

    results = []
    for wh in active_webhooks:
        res = send_webhook_payload(wh, session_id, payload)
        results.append(res)
    return results

def retrigger_webhook_for_session(webhook_id: str, session_id: str) -> Dict[str, Any]:
    """Manually re-triggers a specific webhook for a past session."""
    webhooks = database.get_webhooks()
    target = next((w for w in webhooks if w["id"] == webhook_id), None)
    if not target:
        return {"error": f"Webhook with ID '{webhook_id}' not found."}

    mom = database.get_session_mom(session_id)
    action_items = mom.get("action_items", []) if mom else []
    exec_summary = mom.get("executive_summary", "") if mom else ""

    payload = {
        "event": "manual_retrigger",
        "session_id": session_id,
        "timestamp": time.time(),
        "executive_summary": exec_summary,
        "action_items_count": len(action_items),
        "action_items": action_items,
        "source": "Adrishyaa-Local"
    }

    return send_webhook_payload(target, session_id, payload)

if __name__ == "__main__":
    database.init_db()
    start_mock_webhook_server(8080)
    print("Testing Webhook Dispatcher...")
    res = dispatch_session_action_items(
        "test-session-1",
        [{"task": "Prepare Q3 Deck", "assignee": "Alex", "deadline": "Friday"}],
        "Test Executive Summary"
    )
    print("Dispatch Results:", res)
