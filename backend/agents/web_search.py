import json
import os
from typing import List, Dict, Any
from urllib.parse import urlencode
from urllib.request import urlopen, Request

from backend.utils.logging import get_logger

LOGGER = get_logger()


class WebSearchAgent:
    def __init__(self):
        self.serpapi_key = os.environ.get("SERPAPI_API_KEY")

    def _serpapi_search(self, query: str) -> List[Dict[str, Any]]:
        if not self.serpapi_key:
            raise RuntimeError("SERPAPI key missing")
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.serpapi_key,
            "num": 5,
        }
        url = f"https://serpapi.com/search.json?{urlencode(params)}"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        results = []
        for item in data.get("organic_results", [])[:5]:
            results.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet") or "",
            })
        return results

    def _duckduckgo_fallback(self, query: str) -> List[Dict[str, Any]]:
        params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
        url = f"https://api.duckduckgo.com/?{urlencode(params)}"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        results = []
        # Use RelatedTopics as quick hits
        for item in data.get("RelatedTopics", [])[:5]:
            if isinstance(item, dict) and item.get("Text"):
                results.append({"title": item.get("Text"), "link": item.get("FirstURL"), "snippet": item.get("Text")})
        # Also consider Abstract
        abstract = data.get("AbstractText")
        if abstract:
            results.insert(0, {"title": "DuckDuckGo Abstract", "link": data.get("AbstractURL"), "snippet": abstract})
        return results[:5]

    async def search(self, query: str) -> List[Dict[str, Any]]:
        try:
            results = self._serpapi_search(query)
            LOGGER.info("web.serpapi_ok", count=len(results))
            return results
        except Exception as e:
            LOGGER.warn("web.serpapi_failed", error=str(e))
            try:
                results = self._duckduckgo_fallback(query)
                LOGGER.info("web.duck_ok", count=len(results))
                return results
            except Exception as e2:
                LOGGER.error("web.duck_failed", error=str(e2))
                return []
