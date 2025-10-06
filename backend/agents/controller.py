import json
import re
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from backend.agents.groq_llm import groq_chat
from backend.agents.web_search import WebSearchAgent
from backend.agents.arxiv_agent import ArXivAgent
from backend.agents.rag_pdf import PDFRAGAgent
from backend.utils.logging import get_logger, Tracer

LOGGER = get_logger()


class ControllerAgent:
    def __init__(self, pdf_agent: PDFRAGAgent, tracer: Tracer):
        self.pdf_agent = pdf_agent
        self.web_agent = WebSearchAgent()
        self.arxiv_agent = ArXivAgent()
        self.tracer = tracer

    def _rule_based(self, query: str) -> List[str]:
        q = query.lower()
        agents: List[str] = []
        if "summarize this" in q:
            # If user previously uploaded PDFs (RAG has data), prefer PDF RAG
            agents.append("PDF RAG")
        if "recent papers" in q or "arxiv" in q or "paper" in q:
            agents.append("ArXiv")
        if "latest news" in q or "recent developments" in q:
            agents.append("Web Search")
        # Deduplicate while preserving order
        dedup = []
        for a in agents:
            if a not in dedup:
                dedup.append(a)
        return dedup

    def _llm_decide(self, query: str) -> Tuple[List[str], str]:
        prompt = (
            "Analyze this query: {query}. Decide agents to call: PDF RAG, Web Search, ArXiv, or combo. "
            "Provide rationale. Output JSON: {'agents': ['list'], 'rationale': 'string'}".format(query=query)
        )
        content = groq_chat([
            {"role": "system", "content": "You are a helpful controller deciding which agents to call."},
            {"role": "user", "content": prompt},
        ], temperature=0.2, max_tokens=200)
        try:
            # Extract JSON substring if necessary
            m = re.search(r"\{.*\}", content, re.DOTALL)
            obj = json.loads(m.group(0) if m else content)
            agents = obj.get("agents", [])
            rationale = obj.get("rationale", "")
            return agents, rationale
        except Exception:
            return [], content

    async def handle_query(self, query: str, client_ip: str = "unknown") -> Tuple[str, List[str], str, str]:
        t0 = time.time()
        rule_agents = self._rule_based(query)
        llm_agents: List[str] = []
        llm_rationale = ""
        if not rule_agents:
            llm_agents, llm_rationale = self._llm_decide(query)

        # Merge decisions, favoring rules for exact matches
        final_agents = rule_agents or llm_agents or ["PDF RAG"]  # default to RAG
        rationale = llm_rationale or ("Rule-based routing: " + ", ".join(final_agents))

        documents: List[Dict] = []
        snippets: List[str] = []

        # Execute agents
        if "PDF RAG" in final_agents:
            results = await self.pdf_agent.retrieve(query)
            for score, doc in results:
                documents.append({"agent": "PDF RAG", "score": score, **doc.metadata})
                snippets.append(doc.text)
        if "Web Search" in final_agents:
            web = await self.web_agent.search(query)
            documents.extend({"agent": "Web Search", **item} for item in web)
            for item in web:
                snippets.append(f"{item.get('title')}: {item.get('snippet')} ({item.get('link')})")
        if "ArXiv" in final_agents:
            ax = await self.arxiv_agent.search_and_summarize(query)
            documents.extend({"agent": "ArXiv", **item} for item in ax)
            for item in ax:
                snippets.append(f"{item.get('title')}: {item.get('llm_summary')}")

        # Synthesize final answer
        synthesis_prompt = (
            "You are a senior AI assistant. Given the user query and the evidence snippets, "
            "write a concise, well-structured answer. Cite sources inline when possible.\n\n"
            f"Query: {query}\n\n"
            f"Evidence snippets (may include RAG passages, web results, arXiv summaries):\n- "
            + "\n- ".join(snippets[:12])
        )
        final_answer = groq_chat([
            {"role": "system", "content": "You answer succinctly and cite sources."},
            {"role": "user", "content": synthesis_prompt},
        ], temperature=0.3, max_tokens=400)

        trace_id = datetime.utcnow().strftime("%Y%m%d%H%M%S") + ":" + str(int(t0 * 1000))
        trace_entry = {
            "id": trace_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "client_ip": client_ip,
            "query": query,
            "decision": {"agents": final_agents, "rationale": rationale},
            "agents_called": final_agents,
            "documents": documents[:20],
            "answer": final_answer,
            "latency_ms": int((time.time() - t0) * 1000),
        }
        self.tracer.add(trace_entry)
        LOGGER.info("controller.trace_saved", id=trace_id, agents=final_agents)
        return final_answer, final_agents, rationale, trace_id
