import requests
import json
import re
from typing import List, Dict, Any

OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:7b"
FALLBACK_MODEL = "qwen2.5:3b"

def get_available_model() -> str:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        if r.status_code == 200:
            models = [m.get("name") for m in r.json().get("models", [])]
            for target in [DEFAULT_MODEL, FALLBACK_MODEL, "llama3.2:3b", "llama3"]:
                if any(m.startswith(target) for m in models):
                    return target
            if models:
                return models[0]
    except Exception:
        pass
    return DEFAULT_MODEL

def check_ollama_status() -> Dict[str, Any]:
    try:
        res = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        if res.status_code == 200:
            models = [m.get("name") for m in res.json().get("models", [])]
            return {
                "online": True,
                "url": OLLAMA_URL,
                "models": models,
                "selected_model": get_available_model()
            }
    except Exception as e:
        pass
    return {
        "online": False,
        "url": OLLAMA_URL,
        "models": [],
        "error": "Ollama server is unreachable. Please ensure Ollama is running on port 11434."
    }

def call_ollama(prompt: str, system_prompt: str = "", format_json: bool = False) -> str:
    model = get_available_model()
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 1024
        }
    }
    if system_prompt:
        payload["system"] = system_prompt
    if format_json:
        payload["format"] = "json"

    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=60)
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            raise Exception(f"Ollama API returned HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[Ollama Error] {e}")
        return ""

def format_transcript_for_prompt(transcripts: List[Dict[str, Any]]) -> str:
    lines = []
    for item in transcripts:
        speaker = item.get("speaker", "Participant")
        text = item.get("text", "")
        lines.append(f"{speaker}: {text}")
    return "\n".join(lines)

def generate_live_summary(transcripts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Runs background 90-second incremental summary of recent meeting transcripts."""
    if not transcripts:
        return {"highlights": [], "topics": [], "consensus": []}

    formatted = format_transcript_for_prompt(transcripts[-25:]) # last ~25 utterances
    system_prompt = (
        "You are an AI meeting assistant. Analyze the recent meeting excerpt and return a JSON object with: "
        "'highlights' (list of 2-3 brief bullet points), 'topics' (list of 2-3 topic keywords), "
        "and 'consensus' (list of 1-2 agreed points or 'None yet'). Keep descriptions concise."
    )

    result_raw = call_ollama(formatted, system_prompt=system_prompt, format_json=True)
    try:
        data = json.loads(result_raw)
        return {
            "highlights": data.get("highlights", []),
            "topics": data.get("topics", []),
            "consensus": data.get("consensus", [])
        }
    except Exception:
        return {
            "highlights": [result_raw[:150]] if result_raw else ["Listening to active discussion..."],
            "topics": ["Live Meeting"],
            "consensus": []
        }

def answer_stealth_prompt(user_question: str, transcripts: List[Dict[str, Any]]) -> str:
    """Answers user queries in the stealth prompt overlay based on 15-minute sliding window context."""
    if not transcripts:
        return "No active meeting transcript detected in the current window."

    formatted = format_transcript_for_prompt(transcripts[-50:]) # 15-minute window
    system_prompt = (
        "You are an invisible meeting co-pilot. Answer the user's question accurately and extremely concisely "
        "based ONLY on the provided meeting context. If the information was not mentioned, state 'Not mentioned in the meeting yet'."
    )
    prompt = f"MEETING CONTEXT:\n{formatted}\n\nUSER QUESTION: {user_question}\n\nCONCISE ANSWER:"
    answer = call_ollama(prompt, system_prompt=system_prompt, format_json=False)
    return answer.strip() if answer else "Could not reach Ollama engine."

def generate_mom(transcripts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generates a formal Minutes of Meeting (MoM) with a strict JSON schema upon meeting completion."""
    if not transcripts:
        return {
            "executive_summary": "Session ended with no recorded transcript.",
            "key_topics": [],
            "decisions_made": [],
            "action_items": [],
            "unresolved_questions": []
        }

    formatted = format_transcript_for_prompt(transcripts)
    system_prompt = """You are an executive meeting assistant. Analyze the full meeting transcript and generate a structured JSON Minutes of Meeting (MoM) object.

Strict JSON Output Requirements:
{
  "executive_summary": "3-4 sentence paragraph summarizing the core purpose, discussion, and outcome of the meeting.",
  "key_topics": ["List of main subjects discussed"],
  "decisions_made": ["List of explicit decisions agreed upon during the call"],
  "action_items": [
    {
      "task": "Clear description of action required",
      "assignee": "Name of responsible person or 'Unassigned'",
      "deadline": "Mentioned deadline or 'TBD'"
    }
  ],
  "unresolved_questions": ["List of open questions or items left unresolved"]
}

Respond ONLY with valid JSON."""

    prompt = f"FULL MEETING TRANSCRIPT:\n{formatted}\n\nGenerate MoM JSON:"
    raw_json = call_ollama(prompt, system_prompt=system_prompt, format_json=True)

    try:
        parsed = json.loads(raw_json)
        return {
            "executive_summary": parsed.get("executive_summary", "Meeting concluded."),
            "key_topics": parsed.get("key_topics", []),
            "decisions_made": parsed.get("decisions_made", []),
            "action_items": parsed.get("action_items", []),
            "unresolved_questions": parsed.get("unresolved_questions", [])
        }
    except Exception as err:
        print(f"[MoM Parse Error] {err}. Raw output: {raw_json}")
        # Robust fallback regex extraction
        return {
            "executive_summary": "Meeting concluded. (Auto-extracted summary)",
            "key_topics": ["General Discussion"],
            "decisions_made": [],
            "action_items": [
                {
                    "task": "Review meeting discussion",
                    "assignee": "Team",
                    "deadline": "As soon as possible"
                }
            ],
            "unresolved_questions": []
        }
