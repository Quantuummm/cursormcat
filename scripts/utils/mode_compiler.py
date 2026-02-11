"""
Mode Compiler
-------------
Turns extracted + structured Kaplan content into deterministic, engine-ready "mode instances"
(games) with stable payload schemas.

DEBUGGING & FIXING:
If the generated JSONs fail validation (see `phases/phase8_1/validation/`):
- If EVERY file has the same schema error: The bug is likely here in these payload builders.
- If only ONE file has a logic error (e.g., wrong answer): The bug is in the source JSON data
  (Phase 8 structured or Phase 3 extracted). Fix the source data and re-run compilation.

Design goals:
- No custom art required: payloads are schematic and themeable.
- Deterministic first: avoid relying on an LLM for routine payload generation.
- Robust to partial data: if labels/axes/etc. aren't available yet, the compiler skips that mode.
- Every section gets at least 2 game modes (concept_clash + rapid_recall as minimum fallbacks).
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─── Minimum games per section (bulletproofing) ─────────────
MIN_MODES_PER_SECTION = 2

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _stable_id(*parts: str) -> str:
    """Create a stable-ish id from parts (used for mode ids)."""
    base = "|".join(p.strip() for p in parts if p is not None)
    base = re.sub(r"\s+", " ", base)
    return re.sub(r"[^a-zA-Z0-9:_\-|]+", "", base)[:120]

def _slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"[^a-z0-9\-]+", "", s)
    return s[:60] or "x"

def _sample_unique(items: List[Any], k: int, rng: random.Random) -> List[Any]:
    if k <= 0:
        return []
    if len(items) <= k:
        return list(items)
    return rng.sample(items, k)

def _extract_terms_from_text(text: str) -> List[str]:
    """Cheap term extraction: pulls bold-like terms, TitleCase phrases, and acronym tokens."""
    if not text:
        return []
    acr = re.findall(r"\b[A-Z]{2,6}\b", text)
    tc = re.findall(r"\b(?:[A-Z][a-z]+)(?:\s+[A-Z][a-z]+){0,2}\b", text)
    out = list(dict.fromkeys([t.strip() for t in acr + tc if len(t.strip()) >= 3]))
    return out[:50]

def _best_effort_labels_from_description(desc: str) -> List[str]:
    if not desc:
        return []
    labels = re.findall(r"labeled\s+[\"']([^\"']+)[\"']", desc, flags=re.IGNORECASE)
    paren = re.findall(r"\b([A-Z][a-zA-Z0-9\-]{2,30})\s*\(", desc)
    candidates = labels + paren
    stop = {"Figure", "Chapter", "Level", "DNA", "RNA"}
    cleaned = []
    for c in candidates:
        c = c.strip()
        if len(c) < 3 or len(c) > 40:
            continue
        if c in stop:
            continue
        cleaned.append(c)
    cleaned = list(dict.fromkeys(cleaned))
    return cleaned[:20]

def _extract_section_content_text(section: Dict[str, Any]) -> str:
    """Extract actual content text from section for term filtering.
    Uses content block text only — NOT the full JSON serialization."""
    parts = []
    parts.append((section.get("section_title") or "").strip())
    for b in section.get("content_blocks", []) or []:
        content = b.get("content", "")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.append((item.get("text") or "").strip())
        for h in b.get("headers", []) or []:
            parts.append(str(h))
        for row in b.get("rows", []) or []:
            if isinstance(row, list):
                parts.extend(str(cell) for cell in row)
        if b.get("term"):
            parts.append(str(b["term"]))
        if b.get("definition"):
            parts.append(str(b["definition"]))
    return " ".join(p for p in parts if p)

# ---------------------------------------------------------------------
# World config
# ---------------------------------------------------------------------

def load_world_config(project_root: Path) -> Dict[str, Any]:
    path = project_root / "lore" / "world.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def load_specialists(project_root: Path) -> Dict[str, Any]:
    path = project_root / "lore" / "characters" / "specialists.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def subject_specialist_id(world: Dict[str, Any], subject: str) -> str:
    """Get the specialist_id for a subject from world.json."""
    return (
        world.get("subjects", {})
             .get(subject, {})
             .get("specialist_id", "lyra")
    )


def specialist_display_name(specialists: Dict[str, Any], specialist_id: str) -> str:
    """Get the display name for a specialist from specialists.json."""
    spec = specialists.get("specialists", {}).get(specialist_id, {})
    return spec.get("display_name", specialist_id)


# Legacy alias for backward compatibility
def subject_companion_id(world: Dict[str, Any], subject: str) -> str:
    return subject_specialist_id(world, subject)

# ---------------------------------------------------------------------
# Core compilation
# ---------------------------------------------------------------------

@dataclass
class CompilationContext:
    subject: str
    chapter_number: int
    section_id: str
    rng_seed: int
    world: Dict[str, Any]
    project_root: Path

    @property
    def rng(self) -> random.Random:
        return random.Random(self.rng_seed)

def infer_archetypes(section: Dict[str, Any], figures: List[Dict[str, Any]], equations: List[Dict[str, Any]]) -> List[str]:
    """Deterministic archetype inference from already-extracted structure."""
    archetypes = set()
    blocks = section.get("content_blocks", []) or []

    if any(b.get("format") == "numbered_steps" and len(b.get("content", [])) >= 3 for b in blocks):
        archetypes.add("process")
    if any(b.get("format") in {"comparison_table", "fill_in_table"} for b in blocks):
        archetypes.add("table")
    if any(b.get("format") == "definition" for b in blocks):
        archetypes.add("vocab")
    if equations:
        archetypes.add("equation")

    for f in figures or []:
        ft = (f.get("figure_type") or "").lower()
        if ft in {"diagram", "structure", "illustration", "flowchart", "chart"}:
            archetypes.add("diagram")
        if ft in {"graph"}:
            archetypes.add("graph")
        if ft in {"table_figure"}:
            archetypes.add("table")

    if not archetypes:
        archetypes.add("concept")

    order = ["process", "network", "diagram", "graph", "table", "equation", "vocab", "concept"]
    return [a for a in order if a in archetypes] + sorted([a for a in archetypes if a not in order])

# ---------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------

def build_sequence_payload(ctx: CompilationContext, steps_block: Dict[str, Any], difficulty: str) -> Dict[str, Any]:
    rng = ctx.rng
    steps = steps_block.get("content", []) or []
    items = [{"order": s.get("step"), "text": s.get("text", "").strip()} for s in steps if s.get("text")]
    items = [it for it in items if isinstance(it["order"], int)]
    items.sort(key=lambda x: x["order"])
    if difficulty == "easy":
        items = items[: min(5, len(items))]
    elif difficulty == "medium":
        items = items[: min(7, len(items))]
    shuffled = items[:]
    rng.shuffle(shuffled)
    return {
        "engine": "sequence_builder",
        "title": steps_block.get("title") or "Build the sequence",
        "instructions": "Drag the steps into the correct order.",
        "steps": shuffled,
        "correct_order": [it["order"] for it in items],
        "hint_policy": {
            "show_first_step": difficulty in {"easy", "medium"},
            "show_last_step": difficulty == "easy",
        },
    }

def build_sort_payload(ctx: CompilationContext, table_block: Dict[str, Any], difficulty: str) -> Optional[Dict[str, Any]]:
    rng = ctx.rng
    headers = table_block.get("headers") or []
    rows = table_block.get("rows") or []
    if len(headers) < 3 or len(rows) < 2:
        return None
    feature_header = headers[0]
    buckets = headers[1:]
    items = []
    for r in rows:
        if not r or len(r) < 3:
            continue
        feature = str(r[0]).strip()
        if not feature:
            continue
        cells = [str(c).strip() for c in r[1:]]
        items.append({"feature": feature, "cells": dict(zip(buckets, cells))})
    if not items:
        return None
    n = {"easy": 6, "medium": 10, "hard": 14, "expert": 18}.get(difficulty, 10)
    items = _sample_unique(items, min(n, len(items)), rng)
    return {
        "engine": "sort_buckets",
        "title": table_block.get("title") or "Sort the features",
        "instructions": f"Drag each {feature_header.lower()} into the correct category.",
        "buckets": buckets,
        "items": items,
        "scoring": {"per_item": 10, "streak_bonus": 5},
        "hint_policy": {"show_one_correct": difficulty == "easy"},
    }

def build_equation_payload(ctx: CompilationContext, equations: List[Dict[str, Any]], difficulty: str,
                            scope: str = "section") -> Optional[Dict[str, Any]]:
    """Build equation forge payload. scope can be 'section', 'chapter', 'book', or 'multibook'."""
    rng = ctx.rng
    if not equations:
        return None
    k = {"easy": 2, "medium": 3, "hard": 4, "expert": 5}.get(difficulty, 3)
    # For larger scopes, include more equations
    if scope in ("chapter", "book", "multibook"):
        k = {"easy": 3, "medium": 5, "hard": 7, "expert": 10}.get(difficulty, 5)
    eqs = _sample_unique(equations, min(k, len(equations)), rng)
    cards = []
    for e in eqs:
        title = e.get("title") or e.get("equation_id") or "Equation"
        formula = e.get("equation") or ""
        vars_ = e.get("variables") or []
        cards.append({
            "equation_id": e.get("equation_id"),
            "title": title,
            "formula": formula,
            "variables": vars_,
            "question_types": (
                ["name_to_formula"] if difficulty == "easy" else
                ["name_to_formula", "variable_meaning", "units"] if difficulty in {"medium", "hard"} else
                ["name_to_formula", "variable_meaning", "units", "rearrange"]
            ),
        })
    scope_label = {"section": "", "chapter": " (Chapter)", "book": " (Book)", "multibook": " (Multi-Book)"}
    return {
        "engine": "equation_forge",
        "title": f"Equation Forge{scope_label.get(scope, '')}",
        "scope": scope,
        "instructions": "Pick the right equation, then identify variables and units.",
        "cards": cards,
        "total_available": len(equations),
        "hint_policy": {"show_variable_hints": difficulty in {"easy", "medium"}},
    }

def build_rapid_recall_payload(ctx: CompilationContext, term_defs: List[Tuple[str, str]], difficulty: str) -> Optional[Dict[str, Any]]:
    rng = ctx.rng
    if len(term_defs) < 4:
        return None
    n = {"easy": 8, "medium": 12, "hard": 16, "expert": 20}.get(difficulty, 12)
    chosen = _sample_unique(term_defs, min(n, len(term_defs)), rng)
    all_defs = [d for _, d in term_defs]
    cards = []
    for term, correct_def in chosen:
        distractors = _sample_unique([d for d in all_defs if d != correct_def], 3, rng)
        options = distractors + [correct_def]
        rng.shuffle(options)
        correct_index = options.index(correct_def)
        cards.append({"term": term, "options": options, "correct_index": correct_index})
    return {
        "engine": "rapid_recall",
        "title": "Rapid Recall",
        "instructions": "Pick the correct definition. Keep your streak alive.",
        "timer_seconds": 6 if difficulty in {"hard", "expert"} else None,
        "cards": cards,
        "hint_policy": {"eliminate_one": difficulty == "easy"},
    }

def build_label_payload(ctx: CompilationContext, figures: List[Dict[str, Any]], difficulty: str) -> Optional[Dict[str, Any]]:
    rng = ctx.rng
    candidates = []
    for f in figures or []:
        labels = f.get("labels") or f.get("parts")
        if not labels:
            labels = _best_effort_labels_from_description(f.get("description", ""))
        labels = [
            l if isinstance(l, str) else (l.get("label") or l.get("text"))
            for l in labels if l
        ]
        labels = [l.strip() for l in labels if isinstance(l, str) and len(l.strip()) >= 2]
        labels = list(dict.fromkeys(labels))
        if len(labels) >= 4:
            candidates.append((f, labels))
    if not candidates:
        return None
    fig, labels = rng.choice(candidates)
    n = {"easy": 4, "medium": 6, "hard": 8, "expert": 10}.get(difficulty, 6)
    labels = labels[: min(n, len(labels))]

    structured = fig.get("labels_structured") or []
    meaning_map = {}
    if isinstance(fig.get("labels"), list) and fig["labels"] and isinstance(fig["labels"][0], dict):
        for it in fig["labels"]:
            if not isinstance(it, dict):
                continue
            text = it.get("label") or it.get("text")
            meaning = it.get("points_to") or it.get("meaning")
            if text and meaning:
                meaning_map[str(text).strip()] = str(meaning).strip()
    for it in structured:
        if isinstance(it, dict) and it.get("text") and it.get("meaning"):
            meaning_map[str(it["text"]).strip()] = str(it["meaning"]).strip()

    items = []
    if meaning_map:
        meanings = list(meaning_map.values())
        for lab in labels:
            m = meaning_map.get(lab)
            if not m:
                continue
            distractors = _sample_unique([x for x in meanings if x != m], 3, rng)
            options = distractors + [m]
            rng.shuffle(options)
            items.append({"label": lab, "options": options, "correct_index": options.index(m)})
        if len(items) < 3:
            items = [{"label": lab} for lab in labels]
    else:
        items = [{"label": lab} for lab in labels]

    return {
        "engine": "label_text",
        "title": f"Label: {fig.get('title') or fig.get('figure_id') or 'Figure'}",
        "figure_ref": {
            "figure_id": fig.get("figure_id"),
            "title": fig.get("title"),
            "image_file": fig.get("image_file"),
            "page": fig.get("page"),
        },
        "instructions": "Match labels as fast as you can.",
        "labels": items,
        "hint_policy": {"show_image": True},
    }


def build_concept_clash_payload(ctx: CompilationContext, term_defs: List[Tuple[str, str]],
                                 section_title: str, difficulty: str) -> Optional[Dict[str, Any]]:
    """Concept Clash: A fallback game for pure-concept sections that lack tables/equations/processes.
    Presents true/false statements derived from term definitions.
    Always available as long as there are at least 2 terms."""
    rng = ctx.rng
    if len(term_defs) < 2:
        return None

    n = {"easy": 6, "medium": 10, "hard": 14, "expert": 18}.get(difficulty, 10)
    chosen = _sample_unique(term_defs, min(n, len(term_defs)), rng)
    all_terms = [t for t, _ in term_defs]
    all_defs = [d for _, d in term_defs]

    cards = []
    for term, correct_def in chosen:
        # 50% true statement, 50% false (swap definition)
        is_true = rng.random() > 0.5
        if is_true:
            statement = f"{term}: {correct_def}"
            cards.append({"statement": statement, "is_true": True, "term": term,
                          "explanation": f"Correct! {term} is indeed defined as: {correct_def}"})
        else:
            wrong_def = rng.choice([d for d in all_defs if d != correct_def]) if len(all_defs) > 1 else correct_def
            statement = f"{term}: {wrong_def}"
            cards.append({"statement": statement, "is_true": False, "term": term,
                          "explanation": f"That's the definition of something else. {term} is actually: {correct_def}"})

    return {
        "engine": "concept_clash",
        "title": f"Concept Clash: {section_title}",
        "instructions": "True or false? Swipe right for true, left for false. Speed matters!",
        "timer_seconds": 8 if difficulty in {"hard", "expert"} else None,
        "cards": cards,
        "scoring": {"per_correct": 10, "streak_bonus": 5, "speed_bonus": True},
        "hint_policy": {"show_term_highlight": difficulty == "easy"},
    }


def build_table_challenge_payload(ctx: CompilationContext, table_block: Dict[str, Any],
                                   difficulty: str) -> Optional[Dict[str, Any]]:
    """Table Challenge: a fill-in-the-blank game from comparison/fill-in tables.
    Covers one cell at a time and asks the student to pick the right value."""
    rng = ctx.rng
    headers = table_block.get("headers") or []
    rows = table_block.get("rows") or []
    if len(headers) < 2 or len(rows) < 2:
        return None

    # Build question cards: hide one cell, ask student to identify it
    cards = []
    for r in rows:
        if not isinstance(r, list) or len(r) < 2:
            continue
        row_label = str(r[0]).strip()
        for col_idx in range(1, min(len(r), len(headers))):
            answer = str(r[col_idx]).strip()
            if not answer or answer.lower() in ("", "null", "none", "n/a"):
                continue
            # Gather distractors from other rows in the same column
            other_values = [str(other_row[col_idx]).strip() for other_row in rows
                           if isinstance(other_row, list) and len(other_row) > col_idx
                           and str(other_row[col_idx]).strip() != answer
                           and str(other_row[col_idx]).strip()]
            if not other_values:
                continue
            distractors = _sample_unique(other_values, 3, rng)
            options = distractors + [answer]
            rng.shuffle(options)
            cards.append({
                "row_label": row_label,
                "column": headers[col_idx],
                "options": options,
                "correct_index": options.index(answer),
            })

    if len(cards) < 3:
        return None

    n = {"easy": 5, "medium": 8, "hard": 12, "expert": 16}.get(difficulty, 8)
    cards = _sample_unique(cards, min(n, len(cards)), rng)

    return {
        "engine": "table_challenge",
        "title": f"Table Challenge: {table_block.get('title') or 'Fill the Table'}",
        "instructions": "Fill in the missing cell. What goes here?",
        "headers": headers,
        "cards": cards,
        "scoring": {"per_correct": 10, "streak_bonus": 5},
        "hint_policy": {"show_row_context": difficulty in {"easy", "medium"}},
    }


# ---------------------------------------------------------------------
# Mode selection and compile
# ---------------------------------------------------------------------

def compile_modes_for_section(
    ctx: CompilationContext,
    section: Dict[str, Any],
    figures: List[Dict[str, Any]],
    equations: List[Dict[str, Any]],
    glossary_terms: List[Dict[str, Any]],
    primitives: Optional[Dict[str, Any]] = None,
    structured_section: Optional[Dict[str, Any]] = None,
    game_classification: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Returns a compiled package with archetypes, mode_instances, and speaker defaults."""
    world = ctx.world
    specialist_id = subject_specialist_id(world, ctx.subject)

    # Prefer primitives for downstream payload builders when present.
    # Use section-scoped equations from primitives (not chapter-wide)
    if primitives and isinstance(primitives.get("equations"), list) and primitives["equations"]:
        equations = primitives["equations"]
    if primitives and isinstance(primitives.get("figures"), list) and primitives["figures"]:
        figures = primitives["figures"]

    # Chapter-wide equations for broader game modes
    all_chapter_equations = (primitives or {}).get("all_chapter_equations") or []

    archetypes = (primitives or {}).get("archetypes") or infer_archetypes(section, figures, equations)

    # ─── Build term→definition list with proper section-level scoping ───
    term_defs: List[Tuple[str, str]] = []
    section_text = _extract_section_content_text(section)
    section_text_lower = section_text.lower()

    if primitives and isinstance(primitives.get("terms"), list) and primitives["terms"]:
        for t in primitives["terms"]:
            if not isinstance(t, dict):
                continue
            term = (t.get("term") or "").strip()
            definition = (t.get("definition") or "").strip()
            if term and definition:
                term_defs.append((term, definition))
    else:
        # From definition blocks in section
        for b in section.get("content_blocks", []) or []:
            if b.get("format") == "definition":
                term = (b.get("term") or "").strip()
                definition = (b.get("definition") or b.get("content") or "").strip()
                if term and definition:
                    term_defs.append((term, definition))

        # From glossary — SECTION-SCOPED: check actual content text, not JSON serialization
        for t in glossary_terms or []:
            term = (t.get("term") or "").strip()
            definition = (t.get("definition") or "").strip()
            if term and definition and term.lower() in section_text_lower:
                term_defs.append((term, definition))

    # From structured key_terms (guided learning output)
    if structured_section:
        key_terms = []
        for lvl in structured_section.get("levels", []) or []:
            for seg in lvl.get("learn_segments", []) or []:
                kt = seg.get("key_term")
                if kt:
                    key_terms.append(str(kt).strip())
        key_terms = list(dict.fromkeys([k for k in key_terms if k]))
        glossary_map = {str(t.get("term")).strip(): str(t.get("definition")).strip()
                        for t in glossary_terms or [] if t.get("term") and t.get("definition")}
        for kt in key_terms:
            if kt in glossary_map:
                term_defs.append((kt, glossary_map[kt]))

    # Deduplicate
    seen = set()
    dedup = []
    for term, definition in term_defs:
        key = (term.lower(), definition[:80].lower())
        if key not in seen:
            seen.add(key)
            dedup.append((term, definition))
    term_defs = dedup

    section_title = section.get("section_title") or ctx.section_id

    # ─── Gather source blocks ───
    if primitives and isinstance(primitives.get("processes"), list) and primitives["processes"]:
        steps_blocks = [{
            "format": "numbered_steps", "title": p.get("title"),
            "content": p.get("steps") or [],
        } for p in primitives["processes"] if isinstance(p, dict) and len(p.get("steps") or []) >= 3]
    else:
        steps_blocks = [b for b in section.get("content_blocks", []) or []
                       if b.get("format") == "numbered_steps" and len(b.get("content", []) or []) >= 3]

    if primitives and isinstance(primitives.get("tables"), list) and primitives["tables"]:
        table_blocks = [{
            "format": t.get("table_type"), "title": t.get("title"),
            "headers": t.get("headers") or [], "rows": t.get("rows") or [],
        } for t in primitives["tables"] if isinstance(t, dict) and t.get("table_type") in {"comparison_table", "fill_in_table"}]
    else:
        table_blocks = [b for b in section.get("content_blocks", []) or []
                       if b.get("format") in {"comparison_table", "fill_in_table"}]

    comparison_tables = [tb for tb in table_blocks if tb.get("format") == "comparison_table"]
    all_tables = table_blocks  # includes fill_in_table too

    difficulties = ["easy", "medium", "hard", "expert"]
    mode_instances = []

    def _add_mode(mode_type: str, payload_builder, difficulty: str, source_obj=None, **kwargs):
        payload = None
        if payload_builder == build_sequence_payload:
            if not source_obj: return
            payload = payload_builder(ctx, source_obj, difficulty)
        elif payload_builder == build_sort_payload:
            if not source_obj: return
            payload = payload_builder(ctx, source_obj, difficulty)
        elif payload_builder == build_equation_payload:
            scope = kwargs.get("scope", "section")
            eq_source = kwargs.get("equations", equations)
            payload = payload_builder(ctx, eq_source, difficulty, scope=scope)
        elif payload_builder == build_rapid_recall_payload:
            payload = payload_builder(ctx, term_defs, difficulty)
        elif payload_builder == build_label_payload:
            payload = payload_builder(ctx, figures, difficulty)
        elif payload_builder == build_concept_clash_payload:
            payload = payload_builder(ctx, term_defs, section_title, difficulty)
        elif payload_builder == build_table_challenge_payload:
            if not source_obj: return
            payload = payload_builder(ctx, source_obj, difficulty)
        if not payload:
            return

        mode_id = _stable_id(ctx.subject, f"ch{ctx.chapter_number}", ctx.section_id, mode_type,
                             kwargs.get("scope", ""), difficulty)
        mode_instances.append({
            "mode_id": mode_id,
            "mode_type": mode_type,
            "difficulty": difficulty,
            "unlock_after": "guided_learning",
            "payload": payload,
            "rewards": {
                "xp": {"easy": 40, "medium": 60, "hard": 85, "expert": 110}[difficulty],
                "shards": {"easy": 1, "medium": 1, "hard": 2, "expert": 3}[difficulty],
            },
            "tts": {
                "speaker_defaults": {
                    "narrator": "narrator", "companion": companion_id, "antagonist": "the_fog",
                },
                "events": {
                    "on_enter": {"speaker": "narrator", "text": f"Mode unlocked. {payload.get('title','')}." },
                    "on_correct": {"speaker": "companion", "text": "Nice. Keep the streak."},
                    "on_wrong": {"speaker": "companion", "text": "All good. Try again—focus on the key clue."},
                    "on_complete": {"speaker": "narrator", "text": "Locked in. Mode complete."},
                }
            }
        })

    # ─── Build universal modes (always attempted) ───
    for difficulty in difficulties[:2]:
        _add_mode("rapid_recall", build_rapid_recall_payload, difficulty)
        if comparison_tables:
            _add_mode("sort_buckets", build_sort_payload, difficulty, source_obj=comparison_tables[0])

    # ─── Archetype-driven modes ───
    for difficulty in difficulties:
        if "process" in archetypes and steps_blocks:
            _add_mode("sequence_builder", build_sequence_payload, difficulty, source_obj=steps_blocks[0])
        if "equation" in archetypes:
            _add_mode("equation_forge", build_equation_payload, difficulty, scope="section")
        if "diagram" in archetypes:
            _add_mode("label_text", build_label_payload, difficulty)

    # ─── Chapter-wide equation forge (uses ALL chapter equations) ───
    if all_chapter_equations and len(all_chapter_equations) >= 2:
        for difficulty in difficulties:
            _add_mode("equation_forge", build_equation_payload, difficulty,
                     scope="chapter", equations=all_chapter_equations)

    # ─── Table challenge from any table (comparison or fill-in) ───
    for tb in all_tables[:2]:
        for difficulty in difficulties[:2]:
            _add_mode("table_challenge", build_table_challenge_payload, difficulty, source_obj=tb)

    # ─── Fallback: concept_clash for minimum game coverage ───
    if len(mode_instances) < MIN_MODES_PER_SECTION:
        for difficulty in difficulties[:2]:
            _add_mode("concept_clash", build_concept_clash_payload, difficulty)

    # Optionally incorporate Phase 7 hints
    repetition_priority = None
    if game_classification and isinstance(game_classification, dict):
        games = game_classification.get("games") or []
        priorities = [g.get("repetition_priority") for g in games if isinstance(g, dict)]
        if "critical" in priorities:
            repetition_priority = "critical"
        elif "important" in priorities:
            repetition_priority = "important"
        elif priorities:
            repetition_priority = "supplementary"

    return {
        "subject": ctx.subject,
        "chapter_number": ctx.chapter_number,
        "section_id": ctx.section_id,
        "archetypes": archetypes,
        "repetition_priority": repetition_priority,
        "planet": world.get("subjects", {}).get(ctx.subject, {}),
        "specialist_id": specialist_id,
        "mode_instances": mode_instances,
        "equation_forge_scopes": {
            "section_equations": len(equations),
            "chapter_equations": len(all_chapter_equations),
            "book_wide_available": True,
            "multibook_available": True,
        },
        "notes": {
            "label_mode_requires_structured_labels_for_best_results": True,
            "graph_modes_not_implemented_yet": True,
            "concept_clash_is_universal_fallback": True,
        }
    }


# ---------------------------------------------------------------------
# Book-wide and Multi-book equation forge compilation
# ---------------------------------------------------------------------

def compile_equation_forge_book_wide(
    project_root: Path,
    subject: str,
    world: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Compile a book-wide equation forge that draws from ALL chapters in one subject.
    Called separately from section compilation (e.g., by Phase 8.1 at the end)."""
    from config import PRIMITIVES_DIR

    prims_dir = PRIMITIVES_DIR / subject
    if not prims_dir.exists():
        return None

    all_equations = []
    seen_ids = set()
    for prim_file in sorted(prims_dir.glob("*.json")):
        prim = json.loads(prim_file.read_text(encoding="utf-8"))
        for eq in prim.get("all_chapter_equations", []) or prim.get("equations", []):
            eq_id = eq.get("equation_id") or eq.get("title")
            if eq_id and eq_id not in seen_ids:
                seen_ids.add(eq_id)
                all_equations.append(eq)

    if len(all_equations) < 3:
        return None

    specialist_id = subject_specialist_id(world, subject)
    rng = random.Random(hash(f"book_eq_{subject}") % (2**31))

    modes = []
    for difficulty in ["easy", "medium", "hard", "expert"]:
        payload = build_equation_payload(
            CompilationContext(subject=subject, chapter_number=0, section_id="book_wide",
                             rng_seed=rng.randint(0, 2**31), world=world, project_root=project_root),
            all_equations, difficulty, scope="book"
        )
        if payload:
            modes.append({
                "mode_id": _stable_id(subject, "book_wide", "equation_forge", difficulty),
                "mode_type": "equation_forge",
                "difficulty": difficulty,
                "unlock_after": "any_chapter_complete",
                "scope": "book",
                "payload": payload,
                "rewards": {
                    "xp": {"easy": 60, "medium": 90, "hard": 120, "expert": 160}[difficulty],
                    "crystals": {"easy": 10, "medium": 15, "hard": 25, "expert": 40}[difficulty],
                },
                "tts": {
                    "speaker_defaults": {"lyra": "lyra", "specialist": specialist_id, "grimble": "grimble"},
                    "events": {
                        "on_enter": {"speaker": "lyra", "text": f"Book-wide Equation Forge. All {subject.replace('_', ' ')} equations."},
                        "on_correct": {"speaker": "specialist", "text": "Solid. That equation is locked in."},
                        "on_wrong": {"speaker": "specialist", "text": "Check the variables. You've got this."},
                        "on_complete": {"speaker": "lyra", "text": "All equations mastered for this book."},
                    }
                }
            })

    return {
        "subject": subject,
        "scope": "book",
        "total_equations": len(all_equations),
        "mode_instances": modes,
    }


def compile_equation_forge_multibook(
    project_root: Path,
    selected_subjects: List[str],
    world: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Compile a multi-book equation forge. Students select which books (1-6) to pull equations from.
    Excludes CARS (no equations)."""
    from config import PRIMITIVES_DIR

    all_equations = []
    by_subject = {}
    for subject in selected_subjects:
        if subject == "cars":
            continue  # CARS has no equations
        prims_dir = PRIMITIVES_DIR / subject
        if not prims_dir.exists():
            continue
        subj_eqs = []
        seen_ids = set()
        for prim_file in sorted(prims_dir.glob("*.json")):
            prim = json.loads(prim_file.read_text(encoding="utf-8"))
            for eq in prim.get("all_chapter_equations", []) or prim.get("equations", []):
                eq_id = eq.get("equation_id") or eq.get("title")
                if eq_id and eq_id not in seen_ids:
                    seen_ids.add(eq_id)
                    eq_with_source = {**eq, "source_subject": subject}
                    subj_eqs.append(eq_with_source)
                    all_equations.append(eq_with_source)
        by_subject[subject] = subj_eqs

    if len(all_equations) < 5:
        return None

    rng = random.Random(hash(f"multibook_eq_{'_'.join(sorted(selected_subjects))}") % (2**31))

    modes = []
    for difficulty in ["easy", "medium", "hard", "expert"]:
        ctx = CompilationContext(
            subject="multibook", chapter_number=0, section_id="multibook",
            rng_seed=rng.randint(0, 2**31), world=world, project_root=project_root
        )
        payload = build_equation_payload(ctx, all_equations, difficulty, scope="multibook")
        if payload:
            # Add source_subject to each card so frontend can show which book it came from
            for card in payload.get("cards", []):
                for eq in all_equations:
                    if eq.get("equation_id") == card.get("equation_id"):
                        card["source_subject"] = eq.get("source_subject")
                        break
            modes.append({
                "mode_id": _stable_id("multibook", "equation_forge", difficulty),
                "mode_type": "equation_forge",
                "difficulty": difficulty,
                "unlock_after": "any_chapter_complete",
                "scope": "multibook",
                "selected_subjects": selected_subjects,
                "payload": payload,
                "rewards": {
                    "xp": {"easy": 80, "medium": 120, "hard": 160, "expert": 200}[difficulty],
                    "crystals": {"easy": 15, "medium": 25, "hard": 35, "expert": 50}[difficulty],
                },
            })

    return {
        "scope": "multibook",
        "selected_subjects": selected_subjects,
        "total_equations": len(all_equations),
        "equations_by_subject": {s: len(eqs) for s, eqs in by_subject.items()},
        "mode_instances": modes,
    }
