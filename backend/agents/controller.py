import json
import re
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from backend.agents.gemini_llm import gemini_chat, gemini_last_error
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

    def _rule_based(self, query: str) -> Tuple[List[str], str]:
        # quick keyword-based routing for common patterns
        q = query.lower()
        agents: List[str] = []
        reasons: List[str] = []
        
        # PDF stuff
        if any(phrase in q for phrase in ["summarize", "summary", "uploaded", "document", "pdf"]):
            agents.append("PDF RAG")
            reasons.append("The query contains keywords related to document summarization (e.g., 'summarize', 'uploaded', 'pdf'). The PDF RAG agent is specifically designed to process and extract information from uploaded documents.")
        
        # academic papers
        if any(phrase in q for phrase in ["recent papers", "arxiv", "paper", "research", "study", "publication"]):
            agents.append("ArXiv")
            reasons.append("The query contains terms indicating interest in academic research (e.g., 'papers', 'arxiv', 'research'). The ArXiv agent retrieves and summarizes recent scholarly publications.")
        
        # news/web search
        if any(phrase in q for phrase in ["latest news", "recent developments", "news", "current", "today", "happening"]):
            agents.append("Web Search")
            reasons.append("The query contains phrases requesting real-time or current information (e.g., 'latest news', 'recent developments'). The Web Search agent retrieves the most up-to-date data from the web.")
        
        # remove dupes but keep order
        dedup = []
        dedup_reasons = []
        for i, a in enumerate(agents):
            if a not in dedup:
                dedup.append(a)
                dedup_reasons.append(reasons[i])
        
        # combine all the reasons
        if dedup_reasons:
            rationale = " ".join(dedup_reasons)
        else:
            rationale = ""
        
        return dedup, rationale

    def _llm_decide(self, query: str) -> Tuple[List[str], str]:
        # use gemini to figure out which agents to call
        prompt = (
            f"Analyze this query: {query}. Decide agents to call: PDF RAG, Web Search, ArXiv, or combo. "
            "Provide rationale. Output JSON: {\"agents\": [\"PDF RAG\"], \"rationale\": \"string\"}"
        )
        content = gemini_chat([
            {"role": "system", "content": "You are a helpful controller deciding which agents to call."},
            {"role": "user", "content": prompt},
        ], temperature=0.2, max_tokens=200)
        try:
            # sometimes the LLM wraps JSON in extra text, so extract it
            m = re.search(r"\{.*\}", content, re.DOTALL)
            obj = json.loads(m.group(0) if m else content)
            # filter to only our real agents
            allowed = {"PDF RAG", "Web Search", "ArXiv"}
            agents = [a for a in obj.get("agents", []) if a in allowed]
            rationale = obj.get("rationale", "")
            return agents, rationale
        except Exception:
            # parsing failed, just return the raw text
            return [], content

    async def handle_query(self, query: str, client_ip: str = "unknown") -> Tuple[str, List[str], str, str]:
        t0 = time.time()
        rule_agents, rule_rationale = self._rule_based(query)
        llm_agents: List[str] = []
        llm_rationale = ""
        errors: List[Dict] = []
        called_llm_decide = False
        if not rule_agents:
            llm_agents, llm_rationale = self._llm_decide(query)
            called_llm_decide = True
            err = gemini_last_error()
            if err:
                errors.append({"stage": "decision", **err})

        # prefer rule-based when we have a match (faster)
        final_agents = rule_agents or llm_agents or ["PDF RAG"]
        rationale = rule_rationale or llm_rationale or f"Default routing to {', '.join(final_agents)} as no specific patterns were detected."

        documents: List[Dict] = []
        snippets: List[str] = []

        # call the agents and collect results
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

        # now ask gemini to synthesize everything into one answer
        synthesis_prompt = (
            "You are a senior AI assistant. Given the user query and the evidence snippets, "
            "write a concise, well-structured answer. Cite sources inline when possible.\n\n"
            f"Query: {query}\n\n"
            f"Evidence snippets (may include RAG passages, web results, arXiv summaries):\n- "
            + "\n- ".join(snippets[:12])
        )
        final_answer = gemini_chat([
            {"role": "system", "content": "You answer succinctly and cite sources."},
            {"role": "user", "content": synthesis_prompt},
        ], temperature=0.3, max_tokens=400)
        err2 = gemini_last_error()
        if err2:
            errors.append({"stage": "synthesis", **err2})

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
            "errors": errors or None,
        }
        self.tracer.add(trace_entry)
        LOGGER.info("controller.trace_saved", id=trace_id, agents=final_agents)
        return final_answer, final_agents, rationale, trace_id
