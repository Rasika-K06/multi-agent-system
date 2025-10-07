import os
from typing import Any, Dict, List, Optional

try:
    import google.generativeai as genai  # type: ignore
except Exception:
    genai = None  # type: ignore

_LAST_ERROR: Optional[Dict[str, Any]] = None

# model name aliases for convenience
_MODEL_ALIASES = {
    # Convenience aliases for latest stable models (prefer Gemini 2.x when available)
    "gemini-flash": "gemini-2.5-flash",
    "gemini-flash-latest": "gemini-flash-latest",
    "gemini-pro": "gemini-2.5-pro",
    "gemini-pro-latest": "gemini-pro-latest",
    "gemini-flash-lite": "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest": "gemini-flash-lite-latest",
    # Explicit version aliases
    "gemini-1.5-flash": "gemini-flash-latest",
    "gemini-1.5-pro": "gemini-pro-latest",
}


def gemini_last_error() -> Optional[Dict[str, Any]]:
    return _LAST_ERROR


def gemini_chat(messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 512) -> str:
    # wrapper for gemini API - returns mock on error so app doesn't crash
    global _LAST_ERROR
    _LAST_ERROR = None

    raw_key = os.environ.get("GOOGLE_API_KEY") or ""
    api_key = raw_key.strip().strip('"').strip("'")
    raw_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    model_name = _MODEL_ALIASES.get(raw_model, raw_model).strip()

    user_content = next((m.get("content", "") for m in messages if m.get("role") == "user"), "")

    if not api_key or genai is None:
        tag = "NO_API_KEY" if not api_key else "LIB_IMPORT_ERROR"
        return f"[MOCK LLM RESPONSE - {tag}] {user_content[:200]}..."

    try:
        genai.configure(api_key=api_key)
        system_prompts = [m.get("content", "") for m in messages if m.get("role") == "system"]
        user_parts = [m.get("content", "") for m in messages if m.get("role") != "system"]
        system_instruction = "\n".join(p for p in system_prompts if p) or None
        generation_config = {"temperature": float(temperature), "max_output_tokens": int(max_tokens)}
        model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
        prompt_text = "\n\n".join(p for p in user_parts if p)
        resp = model.generate_content(prompt_text, generation_config=generation_config, safety_settings=None)
        text = getattr(resp, "text", None)
        if not text:
            try:
                candidates = getattr(resp, "candidates", None)
                if candidates:
                    parts = getattr(candidates[0].content, "parts", [])
                    text = "".join(getattr(p, "text", "") for p in parts)
            except Exception:
                pass
        if text:
            return text.strip()
        _LAST_ERROR = {"source": "gemini", "type": "BadResponse", "message": "No text in response"}
        return "[LLM ERROR] Unexpected Gemini response"
    except Exception as e:
        _LAST_ERROR = {"source": "gemini", "type": e.__class__.__name__, "message": str(e)}
        return f"[MOCK LLM RESPONSE - {e.__class__.__name__}] {user_content[:200]}..."
