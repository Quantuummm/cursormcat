# MCAT Content Hub — Project Summary

## What We're Building

A **Duolingo-style gamified MCAT study platform** designed specifically for ADHD learners. It takes Kaplan MCAT textbooks and transforms them into bite-sized, progressive guided learning with TTS narration, interactive memorization games, and a visual "bridge" system connecting topics the way the MCAT tests them.

**This is NOT another Anki or Khan Academy.** The difference:
- Short, punchy lessons (not lectures)
- Questions interleaved every 2-3 minutes (not saved for the end)
- Multiple sensory inputs simultaneously (TTS audio + animated captions + visuals)
- Scales from "what is this?" to "I can answer MCAT questions about it"
- Memorization games for pathways, structures, and processes (drag-and-drop, label, build, regulate)
- Cross-topic "MCAT Bridges" that unlock when you finish related concepts

---

## Key Choices We Made

| Decision | What We Chose | Why |
|----------|---------------|-----|
| **Content source** | Kaplan books (not AI-generated) | MCAT accuracy is non-negotiable. AI restructures, it doesn't create medical facts. |
| **AI role** | Extraction + restructuring pipeline | AI is the assembly line, not the knowledge base. |
| **Extraction model** | Gemini 2.5 Flash | Reads copyrighted PDFs without blocking. 65K output for full chapters. |
| **Generation model** | Gemini 3 Flash Preview → 2.5 fallback | Best question quality. Auto-falls back if Gemini 3 refuses. |
| **Content format** | Single JSON per concept section | Everything the frontend needs in one file — lessons, questions, answers, TTS text, game data. |
| **Answers in same file?** | Yes | Instant feedback (0ms) is the #1 ADHD engagement factor. No separate API call. |
| **Question style** | 7 types, ADHD-optimized wording | Variety prevents zoning out. Action verbs, stakes, no "which of the following." |
| **Cloud platform** | Google Cloud ($300 credits) | Firebase hosting, Firestore DB, Cloud TTS, Cloud Storage — all one ecosystem. |
| **Verification** | 3-layer system (logic + cross-ref + AI) | Catches hallucinations before they reach learners. |

---

## Conversation Evolution (Brief)

1. **Vision & Architecture** — Defined the gamified hub concept, Duolingo inspiration, ADHD design principles, and debated AI-generated content vs Kaplan books. Chose Kaplan as source of truth with AI as the pipeline.

2. **Pipeline Design** — Designed a 12-phase extraction-to-deployment pipeline. Created the extraction prompts (TOC, sections, assessments, glossary), the restructuring prompt (ADHD-optimized guided learning), and the game classification system. Decided on single-file JSON per concept.

3. **Content Requirements Expansion** — Added 10 new data types: learning objectives, fill-in tables, figure/diagram extraction (PyMuPDF + Gemini matching), MCAT Expertise callouts, equations, shared concepts for bridges, chapter assessments with AI-enriched wrong-answer explanations, glossary for definition games, chapter profiles with AAMC categories and HY markers. Redesigned prompts to capture all of these with typed content blocks.

4. **Implementation** — Built the entire pipeline: 12 Python scripts, 8 prompt templates, utility modules (Gemini client with rate limiting + cost tracking, image matcher, validators), config system. Installed Python 3.12, Node.js, all dependencies. Set up GitHub repo.

5. **Proof of Concept (Biology Ch1)** — Ran all phases on Chapter 1. Extracted 92 content blocks, 18 concept checks, 16 callouts, 485 glossary terms, 195 images, 20 cataloged figures. Restructured 5 sections into 23 levels with 53 ADHD-optimized questions. Classified 22 memorization games.

6. **Model Strategy** — Discovered Gemini 3 Flash blocks copyrighted extraction (finish_reason: 4) but excels at generation. Built dual-model approach: 2.5 Flash for extraction, 3 Flash for generation with automatic fallback.

7. **Verification System** — Built 3-layer verification (logic checks, cross-reference, AI comparison). Found real issues: hallucinated facts, wrong answer keys, terminology drift. Built fix-and-verify loop. Sections 1.1 and 1.2 passed after fixes.

8. **Handoff** — Wrote comprehensive INSTRUCTIONS.md for any AI agent to continue the project.

---

## Core Principles & Rationale

### 1. Kaplan is Truth, AI is Labor
Medical content accuracy is life-or-death for MCAT scores. Every fact in the game traces back to a Kaplan source. AI's job is to reformat, restructure, and make it engaging — never to invent biology.

### 2. ADHD-First Design
Every design decision runs through the filter: "Would someone with ADHD stay engaged?" This means:
- **Micro-lessons** (25-50 words per TTS segment, ~15 seconds each)
- **Immediate feedback** (correct/wrong response in the same JSON, no network round-trip)
- **Question variety** (7 types, never the same type 3x in a row)
- **Stakes in every question** ("What breaks if X fails?" not "Define X")
- **No shame on wrong answers** ("Almost! Here's the key..." never "Incorrect")
- **Variable rewards** (different celebration messages, not "Correct!" every time)
- **Autonomy** (never force review, offer "dig deeper" as optional)

### 3. Progressive Scaffolding (Zero to Hero)
Each concept scales through levels:
- Level 1: "The Big Picture" — What is this? Why care?
- Level 2: "The Rules" — What principles govern it?
- Level 3: "The Players" — What molecules/enzymes are involved?
- Level 4: "The Process" — How does it work step by step?
- Level 5: "The Variations" — How does it differ across contexts?
- Level 6: "When Things Go Wrong" — Diseases, mutations, inhibitors
- Level 7: "MCAT Patterns" — How the test asks about this

Not every concept needs all 7 levels. Simple concepts get 3, complex ones get 7.

### 4. Format Tags Drive Everything
During extraction, every content block gets a `format` tag (text, bullet_list, numbered_steps, comparison_table, fill_in_table, figure_reference, definition). These tags automatically determine:
- What type of memorization game can be generated
- How the frontend renders it
- What question types are appropriate

### 5. Verify Before You Ship
AI-generated questions can have wrong answers. The 3-layer verification system catches this:
- **Layer 1 (Code):** Is `correct_index` in bounds? Do all wrong options have explanations?
- **Layer 2 (Cross-ref):** Do key terms from the restructured output exist in the original?
- **Layer 3 (AI):** Does Gemini 3 find any hallucinations, wrong answers, or inaccuracies when comparing structured output to the Kaplan source?

### 6. One JSON = One Complete Lesson
Each section produces a single JSON file containing everything the frontend needs: mission briefing, all levels with learn segments + questions + answers + explanations + TTS text + figure references + game data + bridge connections. No assembly required at runtime.

---

## How the Pipeline Works (Phase by Phase)

### Input: Drop a Kaplan PDF into `pdfs/`

---

### Phase 0 — Extract Images `(PyMuPDF, no API needed)`
**What:** Pulls every image from the PDF as PNG files.
**Why:** Figures and diagrams need to be served alongside lessons.
**Output:** `assets/{book}/figures/` → hundreds of PNG files + `_image_manifest.json`
**Model:** None (pure Python, PyMuPDF library)

---

### Phase 1 — Extract Table of Contents `(Gemini 2.5 Flash)`
**What:** Maps the entire book structure — chapters, sections, page ranges, HY markers, AAMC content categories, chapter profiles, locations of assessments/summaries/glossary.
**Why:** This is the roadmap for all subsequent phases. Every other phase references the TOC.
**Output:** `extracted/{book}/_toc.json`
**Key data:** Chapter numbers, section IDs (1.1, 1.2...), is_high_yield flags, mcat_relevance_percent, aamc_content_categories

---

### Phase 2 — Extract Chapter Assessments `(Gemini 2.5 Flash, per chapter)`
**What:** Pulls the 15-question diagnostic MCQ test at the start of each chapter, plus the answer key and detailed explanations from the end of the chapter.
**Why:** These become the "level assessment" before guided learning — showing how much time to spend.
**Output:** `extracted/{book}/ch{N}_assessment.json`
**Key data:** Question text, 4 options, correct letter, Kaplan's explanation

---

### Phase 3 — Extract Section Content `(Gemini 2.5 Flash, per chapter)`
**What:** The BIG extraction. For every section in the chapter, pulls: learning objectives, typed content blocks (text, bullets, numbered steps, tables, fill-in tables, definitions, figure references), concept check questions with answers, callouts (mnemonics, MCAT expertise, bridge notes), equations to remember, shared concepts.
**Why:** This is the raw material that Phase 8 restructures into guided learning.
**Output:** `extracted/{book}/ch{N}_{title}.json`
**Key data:** Everything. Content blocks with `format` tags, concept checks with answers, callouts by type.

---

### Phase 4 — Extract Glossary `(Gemini 2.5 Flash, once per book)`
**What:** Pulls the complete A-Z glossary from the end of the book.
**Why:** Feeds "Definition Sprint" and "Term Match" mini-games. Also surfaces relevant definitions during guided learning.
**Output:** `extracted/{book}/_glossary.json`
**Key data:** Term, definition, first letter (for alphabetical grouping)

---

### Phase 5 — Catalog Figures `(Gemini 2.5 Flash, per chapter)`
**What:** Gemini identifies every figure in the chapter (figure ID, title, page, description, content tags, type). Then a matching script connects Gemini's catalog to the PNG images extracted in Phase 0 using page numbers.
**Why:** Figures appear in guided learning when the lesson references them. The detailed description doubles as alt text and can feed TTS.
**Output:** `extracted/{book}/_figure_catalog.json` + renamed images in `assets/{book}/figures/`
**Key data:** figure_id, title, section_id, detailed description, image filename, matched boolean

---

### Phase 6 — Enrich Wrong-Answer Explanations `(Gemini 3 Flash, per chapter)`
**What:** Chapter assessments only have Kaplan explanations for the CORRECT answer. This phase generates 1-sentence explanations for WHY each WRONG option is wrong.
**Why:** When a learner picks the wrong answer, they need to understand the specific misconception — not just see "Incorrect."
**Output:** Updates `ch{N}_assessment.json` in place (adds `wrong_explanations` to each question)
**Model:** Gemini 3 (generation, no PDF attached)

---

### Phase 7 — Classify Games `(Gemini 3 Flash, per section)`
**What:** Analyzes content blocks, figures, and equations to determine what memorization games can be built. Assigns game types (build, label, enzyme, regulate, match, equation, rapid_recall, diagram_label) and repetition priority (critical/important/supplementary).
**Why:** Not every section gets games — only content with structured/ordered/labeled data. This phase automatically detects which sections need which game types.
**Output:** `classified/{book}/{section_id}-{title}_games.json`
**Key data:** game_type, game_title, difficulty, repetition_priority, items array, regulators, distractors

---

### Phase 8 — Restructure Guided Learning `(Gemini 3 Flash, per section)`
**What:** THE critical transformation. Takes flat Kaplan content and produces progressive ADHD-friendly guided learning with 3-7 levels, each containing learn segments (narrator_text + display_text), check questions (7 types), apply questions, pro tips, mnemonics, figure references, and bridge connections.
**Why:** This is the game content. Everything the frontend renders comes from this output.
**Output:** `structured/{book}/{concept_id}.json`
**Model:** Gemini 3 Flash (best reasoning for question quality). Falls back to 2.5 if needed.
**Key data:** Full structured lesson — mission briefing, levels, questions with all feedback, bridges, game elements

---

### Phase 9 — Enrich Bridges `(Gemini 3 Flash, batch after all books)`
**What:** Takes "Shared Concepts" from every book and generates enriched cross-topic connections with explanations, narrator text, and bridge questions that require knowledge of BOTH topics.
**Why:** MCAT tests cross-topic application. "MCAT Bridges" unlock after finishing related concepts, showing how physics connects to biochemistry, etc.
**Output:** `bridges/{bridge_id}.json` + `bridges/_bridge_graph.json` (node + edge list for visualization)

---

### Phase 10 — Generate TTS Audio `(Google Cloud TTS, requires $300 credits)`
**What:** Converts every `narrator_text` field into MP3 audio using Google Cloud Text-to-Speech. Converts `[PAUSE]` markers to SSML `<break>` tags.
**Why:** Multi-sensory input for ADHD — audio narration plays while text animates on screen.
**Output:** `audio/{book}/{concept_id}/*.mp3`

---

### Phase 11 — Upload to Firestore `(Firebase, requires project setup)`
**What:** Pushes all structured content, glossaries, assessments, figure catalogs, equations, and bridge graphs to Firebase Firestore collections.
**Why:** The web app queries Firestore in real-time. Levels are stored as subcollections for efficient loading.
**Output:** Firestore collections: concepts, glossaries, assessments, figures, equations, shared_concepts, bridge_graph

---

### Post-Pipeline: Verification Loop
**What:** 3-layer verification checks the Phase 8 output against original Kaplan content. If issues are found, `quick_fix.py` regenerates flagged content and re-verifies. Max 3 iterations per section.
**Why:** AI can hallucinate facts or mark wrong answers as correct. This catches it before content goes live.
**Commands:** `python scripts/quick_fix.py {subject} {section_id} verify|fix|status`
