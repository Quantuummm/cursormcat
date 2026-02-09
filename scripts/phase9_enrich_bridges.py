"""
Phase 9: Enrich bridge connections using Shared Concepts data from all books.
Creates cross-topic connections with explanations and bridge questions.

Requires: Phase 3 complete for ALL books (needs shared_concepts data).

Usage:
    python scripts/phase9_enrich_bridges.py
"""

import sys
import json
from pathlib import Path
from slugify import slugify

sys.path.insert(0, str(Path(__file__).parent))
from config import EXTRACTED_DIR, BRIDGES_DIR, PROMPTS_DIR, BOOKS
from utils.gemini_client import GeminiClient


def collect_shared_concepts():
    """Gather all shared concepts from all extracted books."""
    all_shared = []

    for subject in BOOKS.values():
        subject_dir = EXTRACTED_DIR / subject
        chapter_files = sorted(subject_dir.glob("ch[0-9]*_*.json"))
        chapter_files = [f for f in chapter_files if "_assessment" not in f.name]

        for ch_path in chapter_files:
            ch_data = json.loads(ch_path.read_text(encoding="utf-8"))
            ch_num = ch_data.get("chapter_number")
            ch_title = ch_data.get("chapter_title")

            for sc in ch_data.get("shared_concepts", []):
                all_shared.append({
                    "source_book": subject,
                    "source_chapter": ch_num,
                    "source_chapter_title": ch_title,
                    "target_book": sc.get("external_book", "").lower().replace(" ", "_"),
                    "target_chapter": sc.get("external_chapter"),
                    "target_chapter_title": sc.get("external_chapter_title"),
                    "target_topics": sc.get("topics", []),
                })

    return all_shared


def get_chapter_summary(subject, chapter_num):
    """Load the summary for a given chapter."""
    subject_dir = EXTRACTED_DIR / subject
    chapter_files = sorted(subject_dir.glob(f"ch{chapter_num:02d}_*.json"))
    chapter_files = [f for f in chapter_files if "_assessment" not in f.name]

    if not chapter_files:
        return "Summary not available (chapter not yet extracted)"

    ch_data = json.loads(chapter_files[0].read_text(encoding="utf-8"))
    summary = ch_data.get("summary", {})
    points = []
    for sec in summary.get("by_section", []):
        points.extend(sec.get("summary_points", []))

    return "\n".join(points) if points else "Summary not available"


def run():
    """Generate enriched bridge connections."""
    client = GeminiClient()

    prompt_template = (PROMPTS_DIR / "bridge_enrichment.txt").read_text(encoding="utf-8")

    BRIDGES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"{'='*60}")
    print(f"🌉 Enriching bridge connections")
    print(f"{'='*60}")

    # Collect all shared concepts
    all_shared = collect_shared_concepts()
    print(f"\n  📊 Found {len(all_shared)} shared concept connections across all books")

    if not all_shared:
        print("  ⚠️  No shared concepts found. Ensure Phase 3 has been run for at least one book.")
        return

    # Deduplicate (A→B and B→A should be one bridge)
    seen_pairs = set()
    unique_bridges = []
    for sc in all_shared:
        pair_key = tuple(sorted([
            f"{sc['source_book']}-{sc['source_chapter']}",
            f"{sc['target_book']}-{sc['target_chapter']}"
        ]))
        if pair_key not in seen_pairs:
            seen_pairs.add(pair_key)
            unique_bridges.append(sc)

    print(f"  📊 Unique bridge pairs: {len(unique_bridges)}")

    enriched_bridges = []

    for i, bridge in enumerate(unique_bridges):
        print(f"\n  🌉 [{i+1}/{len(unique_bridges)}] {bridge['source_book']} Ch{bridge['source_chapter']} "
              f"↔ {bridge['target_book']} Ch{bridge['target_chapter']}")

        # Get summaries for both sides
        source_summary = get_chapter_summary(bridge["source_book"], bridge["source_chapter"])
        target_summary = get_chapter_summary(bridge["target_book"], bridge["target_chapter"])

        prompt = prompt_template.format(
            source_book=bridge["source_book"],
            source_chapter=bridge["source_chapter"],
            source_chapter_title=bridge["source_chapter_title"],
            source_section_title=bridge["source_chapter_title"],  # Use chapter title as fallback
            target_book=bridge["target_book"],
            target_chapter=bridge["target_chapter"],
            target_chapter_title=bridge["target_chapter_title"],
            target_topics=", ".join(bridge["target_topics"]),
            source_summary=source_summary[:2000],  # Cap to prevent token overflow
            target_summary=target_summary[:2000],
        )

        try:
            enriched = client.enrich(prompt)
            enriched_bridges.append(enriched)

            conn_type = enriched.get("connection_type", "?")
            print(f"     Connection type: {conn_type}")
            print(f"     Bridge questions: {len(enriched.get('bridge_questions', []))}")

            # Save individual bridge
            bridge_id = enriched.get("bridge_id", f"bridge_{i}")
            bridge_path = BRIDGES_DIR / f"{bridge_id}.json"
            with open(bridge_path, "w", encoding="utf-8") as f:
                json.dump(enriched, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"     ⚠️  Error: {e}")

    # Build complete bridge graph
    nodes = set()
    edges = []
    for eb in enriched_bridges:
        source = eb.get("source", {})
        target = eb.get("target", {})

        source_id = f"{source.get('book', '?')}-ch{source.get('chapter', '?')}"
        target_id = f"{target.get('book', '?')}-ch{target.get('chapter', '?')}"

        nodes.add(source_id)
        nodes.add(target_id)
        edges.append({
            "source": source_id,
            "target": target_id,
            "type": eb.get("connection_type"),
            "bridge_id": eb.get("bridge_id"),
        })

    graph = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "nodes": sorted(list(nodes)),
        "edges": edges,
    }

    graph_path = BRIDGES_DIR / "_bridge_graph.json"
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)

    print(f"\n  📊 Bridge graph: {len(nodes)} nodes, {len(edges)} edges")
    print(f"  💾 Graph saved: {graph_path.name}")
    print(f"\n✅ Phase 9 complete!")


if __name__ == "__main__":
    run()
