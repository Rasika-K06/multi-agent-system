import arxiv
from typing import List, Dict, Any

from backend.agents.groq_llm import groq_chat
from backend.utils.logging import get_logger

LOGGER = get_logger()


class ArXivAgent:
    async def search_and_summarize(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        results = []
        try:
            search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.SubmittedDate)
            for res in search.results():
                entry = {
                    "title": res.title,
                    "authors": [a.name for a in res.authors],
                    "summary": res.summary,
                    "published": res.published.isoformat() if res.published else None,
                    "url": res.entry_id,
                }
                # Summarize abstract via LLM
                prompt = f"Summarize the following paper abstract in 3-4 bullet points:\n\nTitle: {res.title}\n\nAbstract: {res.summary}"
                summary = groq_chat([
                    {"role": "system", "content": "You are a concise scientific assistant."},
                    {"role": "user", "content": prompt},
                ], temperature=0.2, max_tokens=200)
                entry["llm_summary"] = summary
                results.append(entry)
        except Exception as e:
            LOGGER.error("arxiv.error", error=str(e))
        return results
