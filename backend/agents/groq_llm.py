import json
import os
from typing import List, Dict, Optional
from urllib.request import Request, urlopen

GROQ_API = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-70b-8192"


def groq_chat(messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 512) -> str:
    """Call Groq Chat Completions API (OpenAI-compatible). Returns assistant content or a mock fallback."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        # Fallback mock for offline/testing
        user_content = next((m["content"] for m in messages if m.get("role") == "user"), "")
        return f"[MOCK LLM RESPONSE] {user_content[:200]}..."
    body = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = json.dumps(body).encode("utf-8")
    req = Request(
        GROQ_API,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
    try:
        return payload["choices"][0]["message"]["content"].strip()
    except Exception:
        return "[LLM ERROR] Unexpected response structure"
