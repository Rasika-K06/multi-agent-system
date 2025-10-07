from pathlib import Path
import fitz

TOPICS = [
    # AI Topics (3 dialogs)
    ("dialog1.pdf", "RAG benefits", [
        "A: What are the benefits of RAG?",
        "B: It grounds LLMs with retrieval, improving factuality.",
        "A: How about performance?",
        "B: With FAISS and MiniLM embeddings, it's fast and lightweight.",
    ]),
    ("dialog2.pdf", "Multi-agent routing", [
        "A: How to route queries in a multi-agent setup?",
        "B: Combine rule-based hints with an LLM controller.",
        "A: Why use multiple agents?",
        "B: Specialization enables better accuracy per domain: PDFs, research papers, real-time news.",
    ]),
    ("dialog3.pdf", "Controller design", [
        "A: What rules should the controller have?",
        "B: PDF summarize -> RAG; recent papers -> ArXiv; latest news -> Web.",
        "A: How does the LLM help?",
        "B: It handles ambiguous queries and can call multiple agents in parallel.",
    ]),
    
    # Solar Industries Context (2 documents)
    ("solar_overview.pdf", "Solar Industries Overview", [
        "Company: Solar Industries India Limited",
        "Founded: 1995 | HQ: Nagpur, Maharashtra",
        "Business: India's largest private sector manufacturer of industrial explosives and propellants.",
        "",
        "Product Lines:",
        "- Bulk explosives (ANFO, emulsions, SME)",
        "- Packaged explosives (cartridges, detonators, boosters)",
        "- Initiating systems (electronic, non-electric detonators)",
        "- Defense products (propellants, warheads, ammunition)",
        "",
        "Technology Focus:",
        "- Advanced blasting solutions for mining, infrastructure, defense",
        "- R&D in energetic materials, precision munitions",
        "- Automation in manufacturing for safety and efficiency",
        "",
        "Industry: Explosives manufacturing requires extreme safety, regulatory compliance,",
        "and continuous innovation in chemistry and materials science.",
    ]),
    ("solar_ai_applications.pdf", "AI/ML at Solar Industries", [
        "AI/ML Applications in Explosives & Defense Manufacturing:",
        "",
        "1. Predictive Maintenance:",
        "   - ML models monitor equipment health (mixers, conveyor systems)",
        "   - Reduces downtime, prevents hazardous failures",
        "",
        "2. Quality Control:",
        "   - Computer vision inspects detonator assembly, cartridge consistency",
        "   - Anomaly detection in chemical composition via spectroscopy data",
        "",
        "3. Supply Chain Optimization:",
        "   - Demand forecasting for explosives (mining seasonality, infrastructure projects)",
        "   - Route optimization for safe transport of hazardous materials",
        "",
        "4. R&D Acceleration:",
        "   - NLP for patent/research paper analysis (energetic materials, propellants)",
        "   - Molecular simulation for new explosive formulations",
        "",
        "5. Safety & Compliance:",
        "   - Document management systems for regulatory filings",
        "   - Real-time monitoring of safety protocols via IoT + AI",
        "",
        "Potential: Multi-agent systems could unify technical docs, track industry research,",
        "and provide instant answers to engineers across manufacturing sites.",
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
