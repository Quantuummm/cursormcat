"""\
Primitives Builder
------------------
Transforms Phase 3/4/5 extraction outputs into "game primitives".

Why primitives?
- Phase 3 is rich but not directly game-ready.
- Games need stable, typed payload pieces (terms, processes, tables, diagram labels, graph specs, equations).
- Primitives are deterministic and reusable: guided learning, drills, bosses, analytics.

This module is intentionally conservative ("best-effort"):
- It never invents missing labels/axes.
- If structure isn't present, it records a raw description so you can improve prompts later.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _lower(s: str) -> str:
    return _norm(s).lower()


def _dedup_keep_order(items: List[Any]) -> List[Any]:
    seen = set()
    out = []
    for it in items:
        key = json.dumps(it, sort_keys=True, ensure_ascii=False) if isinstance(it, (dict, list)) else str(it)
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def _extract_text_blobs_from_section(section: Dict[str, Any]) -> str:
    """Cheap full-text representation used for glossary filtering."""
    try:
        return json.dumps(section, ensure_ascii=False)
    except Exception:
        return str(section)


def _glossary_map(glossary_terms: List[Dict[str, Any]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for t in glossary_terms or []:
        term = _norm(t.get("term") or "")
        definition = _norm(t.get("definition") or "")
        if term and definition and term.lower() not in out:
            out[term.lower()] = definition
    return out


def _best_effort_parse_labels(figure: Dict[str, Any]) -> List[Dict[str, str]]:
    """Try to recover label list from multiple possible figure catalog schemas."""
    # Preferred: figure["labels"] = [{"label":"...", "points_to":"..."}]
    labels = figure.get("labels")
    if isinstance(labels, list) and labels and isinstance(labels[0], dict):
        out = []
        for l in labels:
            label = _norm(l.get("label") or l.get("text") or "")
            points_to = _norm(l.get("points_to") or l.get("meaning") or l.get("description") or "")
            if label:
                out.append({"label": label, "points_to": points_to})
        return out

    # Fallback: try to parse from description lines like "X (blue) ..." or "labeled 'X'"
    desc = _norm(figure.get("description") or "")
    if not desc:
        return []

    # labeled 'X'
    labeled = re.findall(r"labeled\s+[\"']([^\"']+)[\"']", desc, flags=re.IGNORECASE)
    # TitleCase tokens before parentheses
    paren = re.findall(r"\b([A-Z][A-Za-z0-9\-]{2,40})\s*\(", desc)
    candidates = []
    for c in labeled + paren:
        c = _norm(c)
        if 3 <= len(c) <= 50:
            candidates.append(c)
    candidates = list(dict.fromkeys(candidates))
    return [{"label": c, "points_to": ""} for c in candidates[:20]]


def _best_effort_parse_graph(figure: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return a minimal graph spec if available."""
    if (figure.get("figure_type") or "").lower() != "graph":
        return None

    # Preferred schema: figure["graph"] = {x_axis, y_axis, series:[...]}
    g = figure.get("graph")
    if isinstance(g, dict) and (g.get("x_axis") or g.get("y_axis") or g.get("trend_summary")):
        return {
            "x_axis": _norm(g.get("x_axis") or ""),
            "y_axis": _norm(g.get("y_axis") or ""),
            "trend_summary": _norm(g.get("trend_summary") or g.get("trend") or ""),
            "series": g.get("series") or [],
            "key_points": g.get("key_points") or [],
        }

    # Fallback: attempt to infer axes from description text (conservative)
    desc = _norm(figure.get("description") or "")
    if not desc:
        return {"x_axis": "", "y_axis": "", "trend_summary": "", "series": [], "key_points": []}
    # Simple patterns
    x = ""
    y = ""
    m = re.search(r"x-?axis\s*(?:represents|is|shows)\s*([^.;]+)", desc, flags=re.IGNORECASE)
    if m:
        x = _norm(m.group(1))
    m = re.search(r"y-?axis\s*(?:represents|is|shows)\s*([^.;]+)", desc, flags=re.IGNORECASE)
    if m:
        y = _norm(m.group(1))
    return {"x_axis": x, "y_axis": y, "trend_summary": "", "series": [], "key_points": []}


def build_primitives_for_section(
    *,
    subject: str,
    chapter_number: int,
    chapter_title: str,
    section: Dict[str, Any],
    figure_catalog: List[Dict[str, Any]],
    glossary_terms: List[Dict[str, Any]],
    equations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build a deterministic primitives package for a single section."""

    sec_id = section.get("section_id") or "?"
    sec_title = section.get("section_title") or "?"

    blocks = section.get("content_blocks", []) or []
    fulltext = _extract_text_blobs_from_section(section)
    glossary = _glossary_map(glossary_terms)

    # -----------------------------
    # TERMS (vocab)
    # -----------------------------
    terms: List[Dict[str, Any]] = []
    for b in blocks:
        if b.get("format") == "definition":
            term = _norm(b.get("term") or "")
            definition = _norm(b.get("definition") or b.get("content") or "")
            if term and definition:
                terms.append({
                    "term": term,
                    "definition": definition,
                    "source": "definition_block",
                })

    # Glossary terms that appear in this section
    for term_lc, definition in glossary.items():
        if term_lc and term_lc in fulltext.lower():
            # preserve original capitalization if we can find it in glossary_terms
            original_term = None
            for gt in glossary_terms:
                if _lower(gt.get("term") or "") == term_lc:
                    original_term = _norm(gt.get("term") or "")
                    break
            terms.append({
                "term": original_term or term_lc,
                "definition": definition,
                "source": "glossary",
            })

    terms = _dedup_keep_order(terms)

    # -----------------------------
    # PROCESSES / SEQUENCES
    # -----------------------------
    processes: List[Dict[str, Any]] = []
    for b in blocks:
        if b.get("format") == "numbered_steps":
            steps = b.get("content") or []
            norm_steps = []
            for s in steps:
                if not isinstance(s, dict):
                    continue
                step_n = s.get("step")
                text = _norm(s.get("text") or "")
                if isinstance(step_n, int) and text:
                    norm_steps.append({"step": step_n, "text": text})
            if len(norm_steps) >= 2:
                processes.append({
                    "title": _norm(b.get("title") or ""),
                    "steps": norm_steps,
                    "source": "numbered_steps",
                })

    # -----------------------------
    # TABLES
    # -----------------------------
    tables: List[Dict[str, Any]] = []
    for b in blocks:
        if b.get("format") in {"comparison_table", "fill_in_table"}:
            tables.append({
                "table_type": b.get("format"),
                "title": _norm(b.get("title") or ""),
                "headers": b.get("headers") or [],
                "rows": b.get("rows") or b.get("content") or [],
                "given_column": b.get("given_column"),
                "blank_column": b.get("blank_column"),
                "source": b.get("format"),
            })

    # -----------------------------
    # EQUATIONS
    # -----------------------------
    # For now we include all chapter equations; later you can filter by mentions.
    eq_out = []
    for e in equations or []:
        eq_out.append({
            "equation_id": e.get("equation_id"),
            "title": _norm(e.get("title") or ""),
            "equation": e.get("equation_plain") or e.get("equation") or "",
            "variables": e.get("variables") or [],
        })

    # -----------------------------
    # FIGURES / DIAGRAMS / GRAPHS
    # -----------------------------
    figures = [f for f in (figure_catalog or []) if (f.get("section_id") == sec_id)]
    fig_out = []
    graph_specs = []

    for f in figures:
        labels = _best_effort_parse_labels(f)
        graph = _best_effort_parse_graph(f)
        fig_out.append({
            "figure_id": f.get("figure_id"),
            "title": _norm(f.get("title") or ""),
            "page": f.get("page"),
            "figure_type": f.get("figure_type"),
            "content_tags": f.get("content_tags") or [],
            "description": _norm(f.get("description") or ""),
            "labels": labels,
            "graph": graph,
            "table": f.get("table"),
            "flow": f.get("flow"),
        })
        if graph is not None:
            graph_specs.append({
                "figure_id": f.get("figure_id"),
                "title": _norm(f.get("title") or ""),
                "graph": graph,
            })

    # -----------------------------
    # SIGNALS + ARCHETYPES
    # -----------------------------
    signals = {
        "term_count": len(terms),
        "process_count": len(processes),
        "table_count": len(tables),
        "equation_count": len(eq_out),
        "figure_count": len(fig_out),
        "graph_count": len(graph_specs),
    }

    archetypes = []
    if signals["process_count"] > 0:
        archetypes.append("process")
    if signals["graph_count"] > 0:
        archetypes.append("graph")
    if signals["table_count"] > 0:
        archetypes.append("table")
    if signals["equation_count"] > 0:
        archetypes.append("equation")
    if signals["figure_count"] > 0:
        archetypes.append("diagram")
    if signals["term_count"] > 0:
        archetypes.append("vocab")
    if not archetypes:
        archetypes = ["concept"]

    return {
        "book": subject,
        "chapter_number": chapter_number,
        "chapter_title": chapter_title,
        "section_id": sec_id,
        "section_title": sec_title,
        "archetypes": archetypes,
        "signals": signals,
        "terms": terms,
        "processes": processes,
        "tables": tables,
        "equations": eq_out,
        "figures": fig_out,
        "graph_specs": graph_specs,
    }
