"""
Mode Compiler
-------------
Turns extracted + structured Kaplan content into deterministic, engine-ready "mode instances"
(games) with stable payload schemas.

Design goals:
- No custom art required: payloads are schematic and themeable.
- Deterministic first: avoid relying on an LLM for routine payload generation.
- Robust to partial data: if labels/axes/etc. aren't available yet, the compiler skips that mode.
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _stable_id(*parts: str) -> str:
    """Create a stable-ish id from parts (used for mode ids)."""
    base = "|".join(p.strip() for p in parts if p is not None)
    base = re.sub(r"\s+", " ", base)
    # Keep it readable; caller can add uniqueness if needed.
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
    # Acronyms
    acr = re.findall(r"\b[A-Z]{2,6}\b", text)
    # TitleCase phrases (very approximate)
    tc = re.findall(r"\b(?:[A-Z][a-z]+)(?:\s+[A-Z][a-z]+){0,2}\b", text)
    out = list(dict.fromkeys([t.strip() for t in acr + tc if len(t.strip()) >= 3]))
    return out[:50]

def _best_effort_labels_from_description(desc: str) -> List[str]:
    """
    If Phase 5 didn't output structured labels yet, try to recover some from the description.
    This is intentionally conservative; it is better to skip label modes than hallucinate.
    """
    if not desc:
        return []
    # Look for patterns like: labeled 'X' or labeled "X"
    labels = re.findall(r"labeled\s+[\"']([^\"']+)[\"']", desc, flags=re.IGNORECASE)
    # Also patterns like: X lobe (blue) ... or X (something)
    paren = re.findall(r"\b([A-Z][a-zA-Z0-9\-]{2,30})\s*\(", desc)
    candidates = labels + paren
    # Filter common stop words
    stop = {"Figure", "Chapter", "Level", "DNA", "RNA"}  # keep short list; don't overfilter
    cleaned = []
    for c in candidates:
        c = c.strip()
        if len(c) < 3 or len(c) > 40:
            continue
        if c in stop:
            continue
        cleaned.append(c)
    # Deduplicate while preserving order
    cleaned = list(dict.fromkeys(cleaned))
    return cleaned[:20]

# ---------------------------------------------------------------------
# World config
# ---------------------------------------------------------------------

def load_world_config(project_root: Path) -> Dict[str, Any]:
    path = project_root / "lore" / "world.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}

def subject_companion_id(world: Dict[str, Any], subject: str) -> str:
    return (
        world.get("regions", {})
             .get(subject, {})
             .get("companion_id", "narrator")
    )

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

    # Figures drive diagram/graph archetypes if present
    for f in figures or []:
        ft = (f.get("figure_type") or "").lower()
        if ft in {"diagram", "structure", "illustration", "flowchart", "chart"}:
            archetypes.add("diagram")
        if ft in {"graph"}:
            archetypes.add("graph")
        if ft in {"table_figure"}:
            archetypes.add("table")

    # If nothing detected, it's conceptual
    if not archetypes:
        archetypes.add("concept")

    # Stable order
    order = ["process", "network", "diagram", "graph", "table", "equation", "vocab", "concept"]
    return [a for a in order if a in archetypes] + sorted([a for a in archetypes if a not in order])

# ---------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------

def build_sequence_payload(ctx: CompilationContext, steps_block: Dict[str, Any], difficulty: str) -> Dict[str, Any]:
    rng = ctx.rng
    steps = steps_block.get("content", []) or []
    items = [{"order": s.get("step"), "text": s.get("text", "").strip()} for s in steps if s.get("text")]
    # Normalize order
    items = [it for it in items if isinstance(it["order"], int)]
    items.sort(key=lambda x: x["order"])
    # Difficulty controls number of steps included
    if difficulty == "easy":
        items = items[: min(5, len(items))]
    elif difficulty == "medium":
        items = items[: min(7, len(items))]
    # Hard/expert can use all
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
    # Each row: [feature, bucket1, bucket2, ...]
    # We'll turn into prompts where learner assigns the feature to the correct bucket based on which column contains a distinguishing value.
    items = []
    for r in rows:
        if not r or len(r) < 3:
            continue
        feature = str(r[0]).strip()
        if not feature:
            continue
        # Determine "best" bucket by looking for the most unique / non-empty cell.
        cells = [str(c).strip() for c in r[1:]]
        # If multiple columns have content, use a randomized question card
        items.append({
            "feature": feature,
            "cells": dict(zip(buckets, cells)),
        })

    if not items:
        return None

    # Difficulty controls number of features per run
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

def build_equation_payload(ctx: CompilationContext, equations: List[Dict[str, Any]], difficulty: str) -> Optional[Dict[str, Any]]:
    rng = ctx.rng
    if not equations:
        return None

    # Pick up to K equations for the run
    k = {"easy": 2, "medium": 3, "hard": 4, "expert": 5}.get(difficulty, 3)
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

    return {
        "engine": "equation_forge",
        "title": "Equation Forge",
        "instructions": "Pick the right equation, then identify variables and units.",
        "cards": cards,
        "hint_policy": {"show_variable_hints": difficulty in {"easy", "medium"}},
    }

def build_rapid_recall_payload(ctx: CompilationContext, term_defs: List[Tuple[str, str]], difficulty: str) -> Optional[Dict[str, Any]]:
    rng = ctx.rng
    if len(term_defs) < 4:
        return None

    # Select terms for this run
    n = {"easy": 8, "medium": 12, "hard": 16, "expert": 20}.get(difficulty, 12)
    chosen = _sample_unique(term_defs, min(n, len(term_defs)), rng)

    # Build MC cards with distractor definitions from other terms
    all_defs = [d for _, d in term_defs]
    cards = []
    for term, correct_def in chosen:
        distractors = _sample_unique([d for d in all_defs if d != correct_def], 3, rng)
        options = distractors + [correct_def]
        rng.shuffle(options)
        correct_index = options.index(correct_def)
        cards.append({
            "term": term,
            "options": options,
            "correct_index": correct_index,
        })

    return {
        "engine": "rapid_recall",
        "title": "Rapid Recall",
        "instructions": "Pick the correct definition. Keep your streak alive.",
        "timer_seconds": 6 if difficulty in {"hard", "expert"} else None,
        "cards": cards,
        "hint_policy": {"eliminate_one": difficulty == "easy"},
    }

def build_label_payload(ctx: CompilationContext, figures: List[Dict[str, Any]], difficulty: str) -> Optional[Dict[str, Any]]:
    """
    Label mode without coordinates (text-first).
    Later you can upgrade to hotspot coordinates and use the same payload 'labels' array.
    """
    rng = ctx.rng
    # Pick a figure with labels
    candidates = []
    for f in figures or []:
        labels = f.get("labels") or f.get("parts")  # future-proof
        if not labels:
            labels = _best_effort_labels_from_description(f.get("description", ""))
        # Allow multiple label schemas:
        # - ["Frontal lobe", "Parietal lobe", ...]
        # - [{"label":"Frontal lobe","points_to":"..."}, ...]  (figure_catalog v2)
        # - [{"text":"Frontal lobe","meaning":"..."}, ...]     (legacy)
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

    # Difficulty controls label count + distractors
    n = {"easy": 4, "medium": 6, "hard": 8, "expert": 10}.get(difficulty, 6)
    labels = labels[: min(n, len(labels))]

    # We'll create a "match labels to descriptions" game if we have structured label meanings; otherwise just name recognition.
    # Build structured meaning map if present.
    # Supports:
    # - fig["labels"] = [{"label":"Frontal lobe","points_to":"executive function"}, ...]
    # - fig["labels_structured"] = [{"text":"Frontal lobe","meaning":"executive function"}, ...]
    structured = fig.get("labels_structured") or []
    meaning_map = {}
    # Prefer new schema from fig["labels"]
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
        # Match label -> meaning with distractor meanings
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
            # fallback to name-only
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
    """
    Returns a compiled package with:
    - archetypes
    - mode_instances (unlocked after guided learning)
    - speaker defaults (from lore/world.json)
    """
    world = ctx.world
    companion_id = subject_companion_id(world, ctx.subject)

    # Prefer primitives for downstream payload builders when present.
    if primitives and isinstance(primitives.get("equations"), list) and primitives["equations"]:
        equations = primitives["equations"]
    if primitives and isinstance(primitives.get("figures"), list) and primitives["figures"]:
        figures = primitives["figures"]

    # If primitives exist, prefer their archetypes/signals; otherwise infer from raw extraction.
    archetypes = (primitives or {}).get("archetypes") or infer_archetypes(section, figures, equations)

    # Build a term->definition list (prefer primitives if present)
    term_defs: List[Tuple[str, str]] = []
    if primitives and isinstance(primitives.get("terms"), list) and primitives["terms"]:
        for t in primitives["terms"]:
            if not isinstance(t, dict):
                continue
            term = (t.get("term") or "").strip()
            definition = (t.get("definition") or "").strip()
            if term and definition:
                term_defs.append((term, definition))
    else:
        # 1) From explicit definition blocks in section
        for b in section.get("content_blocks", []) or []:
            if b.get("format") == "definition":
                term = (b.get("term") or "").strip()
                definition = (b.get("definition") or b.get("content") or "").strip()
                if term and definition:
                    term_defs.append((term, definition))

        # 2) From glossary (filter by terms that appear in section text)
        section_text = json.dumps(section, ensure_ascii=False)
        for t in glossary_terms or []:
            term = (t.get("term") or "").strip()
            definition = (t.get("definition") or "").strip()
            if term and definition and term.lower() in section_text.lower():
                term_defs.append((term, definition))

    # 3) From structured key_terms (optional)
    if structured_section:
        key_terms = []
        for lvl in structured_section.get("levels", []) or []:
            for seg in lvl.get("learn_segments", []) or []:
                kt = seg.get("key_term")
                if kt:
                    key_terms.append(str(kt).strip())
        key_terms = list(dict.fromkeys([k for k in key_terms if k]))
        # attach glossary definitions if present
        glossary_map = {str(t.get("term")).strip(): str(t.get("definition")).strip()
                        for t in glossary_terms or [] if t.get("term") and t.get("definition")}
        for kt in key_terms:
            if kt in glossary_map:
                term_defs.append((kt, glossary_map[kt]))

    # Deduplicate term_defs
    seen = set()
    dedup = []
    for term, definition in term_defs:
        key = (term.lower(), definition[:80].lower())
        if key in seen:
            continue
        seen.add(key)
        dedup.append((term, definition))
    term_defs = dedup

    # Choose "universal" modes
    universal_modes = []
    # Always try Rapid Recall; if not enough data, it just won't be included.
    universal_modes.append(("rapid_recall", build_rapid_recall_payload))
    # If tables exist, sort is broadly useful
    universal_modes.append(("sort_buckets", build_sort_payload))

    # Archetype-driven modes
    archetype_modes = []
    if "process" in archetypes:
        archetype_modes.append(("sequence_builder", build_sequence_payload))
    if "equation" in archetypes:
        archetype_modes.append(("equation_forge", build_equation_payload))
    if "diagram" in archetypes:
        archetype_modes.append(("label_text", build_label_payload))
    if "graph" in archetypes:
        # Placeholder: later you can add graph engines (curve shift, graph detective)
        pass

    # Gather candidate source blocks for certain engines
    if primitives and isinstance(primitives.get("processes"), list) and primitives["processes"]:
        # Convert primitive processes back to the expected builder shape
        steps_blocks = [{
            "format": "numbered_steps",
            "title": p.get("title"),
            "content": p.get("steps") or [],
        } for p in primitives.get("processes") or [] if isinstance(p, dict) and len(p.get("steps") or []) >= 3]
    else:
        steps_blocks = [b for b in section.get("content_blocks", []) or [] if b.get("format") == "numbered_steps" and len(b.get("content", []) or []) >= 3]

    if primitives and isinstance(primitives.get("tables"), list) and primitives["tables"]:
        table_blocks = [{
            "format": "comparison_table" if (t.get("table_type") == "comparison_table") else t.get("table_type"),
            "title": t.get("title"),
            "headers": t.get("headers") or [],
            "rows": t.get("rows") or [],
        } for t in primitives.get("tables") or [] if isinstance(t, dict) and (t.get("table_type") in {"comparison_table", "fill_in_table"})]
        # sort mode currently expects comparison_table; keep only those
        table_blocks = [tb for tb in table_blocks if tb.get("format") == "comparison_table"]
    else:
        table_blocks = [b for b in section.get("content_blocks", []) or [] if b.get("format") == "comparison_table"]

    # Difficulty ladder
    difficulties = ["easy", "medium", "hard", "expert"]
    mode_instances = []

    def _add_mode(mode_type: str, payload_builder, difficulty: str, source_obj=None):
        payload = None
        if payload_builder == build_sequence_payload:
            if not source_obj:
                return
            payload = payload_builder(ctx, source_obj, difficulty)
        elif payload_builder == build_sort_payload:
            if not source_obj:
                return
            payload = payload_builder(ctx, source_obj, difficulty)
        elif payload_builder == build_equation_payload:
            payload = payload_builder(ctx, equations, difficulty)
        elif payload_builder == build_rapid_recall_payload:
            payload = payload_builder(ctx, term_defs, difficulty)
        elif payload_builder == build_label_payload:
            payload = payload_builder(ctx, figures, difficulty)

        if not payload:
            return

        mode_id = _stable_id(ctx.subject, f"ch{ctx.chapter_number}", ctx.section_id, mode_type, difficulty)
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
                    "narrator": "narrator",
                    "companion": companion_id,
                    "antagonist": "the_fog",
                },
                "events": {
                    "on_enter": {
                        "speaker": "narrator",
                        "text": f"Mode unlocked. {payload.get('title','')}."
                    },
                    "on_correct": {"speaker": "companion", "text": "Nice. Keep the streak."},
                    "on_wrong": {"speaker": "companion", "text": "All good. Try again—focus on the key clue."},
                    "on_complete": {"speaker": "narrator", "text": "Locked in. Mode complete."},
                }
            }
        })

    # Build universal modes from best sources
    for difficulty in difficulties[:2]:  # universal: easy/medium first
        _add_mode("rapid_recall", build_rapid_recall_payload, difficulty)

        if table_blocks:
            _add_mode("sort_buckets", build_sort_payload, difficulty, source_obj=table_blocks[0])

    # Archetype modes across all difficulties (if available)
    for difficulty in difficulties:
        for mode_type, builder in archetype_modes:
            if builder == build_sequence_payload:
                if steps_blocks:
                    _add_mode(mode_type, builder, difficulty, source_obj=steps_blocks[0])
            elif builder == build_sort_payload:
                if table_blocks:
                    _add_mode(mode_type, builder, difficulty, source_obj=table_blocks[0])
            else:
                _add_mode(mode_type, builder, difficulty)

    # Optionally incorporate Phase 7 hints (priority flags) into ordering/metadata
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
        "region": world.get("regions", {}).get(ctx.subject, {}),
        "mode_instances": mode_instances,
        "notes": {
            "label_mode_requires_structured_labels_for_best_results": True,
            "graph_modes_not_implemented_yet": True,
        }
    }
