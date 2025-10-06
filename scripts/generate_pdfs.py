from pathlib import Path
import fitz

TOPICS = [
    ("dialog1.pdf", "RAG benefits", [
        "A: What are the benefits of RAG?",
        "B: It grounds LLMs with retrieval, improving factuality.",
        "A: How about performance?",
        "B: With FAISS and MiniLM embeddings, it's fast and lightweight.",
    ]),
    ("dialog2.pdf", "Multi-agent routing", [
        "A: How to route queries in a multi-agent setup?",
        "B: Combine rule-based hints with an LLM controller.",
    ]),
    ("dialog3.pdf", "Controller design", [
        "A: What rules should the controller have?",
        "B: PDF summarize -> RAG; recent papers -> ArXiv; latest news -> Web.",
    ]),
    ("dialog4.pdf", "ArXiv scanning strategies", [
        "A: How to find recent papers efficiently?",
        "B: Use the arxiv API with query filters and summarize abstracts.",
    ]),
    ("dialog5.pdf", "Web search vs. curated corpora", [
        "A: When to use web search?",
        "B: For latest developments; curated corpora for depth and reliability.",
    ]),
]

def generate(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, title, lines in TOPICS:
        path = out_dir / filename
        if path.exists():
            continue
        doc = fitz.open()
        page = doc.new_page()
        content = f"NebulaByte Dialog — {title}\n\n" + "\n".join(lines)
        page.insert_text((72, 72), content, fontsize=12)
        doc.save(str(path))
        doc.close()
        print(f"Generated: {path}")

if __name__ == "__main__":
    generate(Path("sample_pdfs"))
