"""
JSON schema validators for pipeline output.
Ensures each extraction/restructuring step produces clean, usable data.
"""


def validate_toc(data: dict) -> list[str]:
    """Validate TOC extraction output. Returns list of issues (empty = valid)."""
    issues = []

    if not data.get("book_title"):
        issues.append("Missing book_title")
    if not data.get("book_subject"):
        issues.append("Missing book_subject")
    if not data.get("chapters") or len(data["chapters"]) == 0:
        issues.append("No chapters found")

    for i, ch in enumerate(data.get("chapters", [])):
        prefix = f"Chapter {ch.get('chapter_number', i)}"
        if not ch.get("chapter_title"):
            issues.append(f"{prefix}: missing chapter_title")
        if not ch.get("sections") or len(ch["sections"]) == 0:
            issues.append(f"{prefix}: no sections found")
        for sec in ch.get("sections", []):
            if not sec.get("section_id"):
                issues.append(f"{prefix}: section missing section_id")
            if not sec.get("section_title"):
                issues.append(f"{prefix}: section missing section_title")

    if not data.get("glossary_pages"):
        issues.append("Missing glossary_pages (may not exist for all books)")

    return issues


def validate_extraction(data: dict) -> list[str]:
    """Validate chapter content extraction output."""
    issues = []

    if not data.get("book"):
        issues.append("Missing book field")
    if not data.get("chapter_number"):
        issues.append("Missing chapter_number")
    if not data.get("sections") or len(data["sections"]) == 0:
        issues.append("No sections extracted")

    for sec in data.get("sections", []):
        sec_id = sec.get("section_id", "?")
        prefix = f"Section {sec_id}"

        if not sec.get("section_title"):
            issues.append(f"{prefix}: missing section_title")
        if not sec.get("learning_objectives"):
            issues.append(f"{prefix}: missing learning_objectives (check if they exist in this section)")
        if not sec.get("content_blocks") or len(sec["content_blocks"]) == 0:
            issues.append(f"{prefix}: no content_blocks extracted")

        # Validate content block formats
        valid_formats = {
            "text", "bullet_list", "numbered_steps", "comparison_table",
            "fill_in_table", "figure_reference", "definition"
        }
        for j, block in enumerate(sec.get("content_blocks", [])):
            if block.get("format") not in valid_formats:
                issues.append(f"{prefix}, block {j}: invalid format '{block.get('format')}'")

    # Validate concept checks have answers
    for q in data.get("concept_checks", []):
        q_num = q.get("question_number", "?")
        if not q.get("correct_letter") and q.get("question_type") == "multiple_choice":
            issues.append(f"Concept check Q{q_num}: missing correct_letter")
        if not q.get("kaplan_explanation"):
            issues.append(f"Concept check Q{q_num}: missing kaplan_explanation")

    return issues


def validate_assessment(data: dict) -> list[str]:
    """Validate chapter assessment extraction."""
    issues = []

    questions = data.get("questions", [])
    if len(questions) == 0:
        issues.append("No assessment questions found")
    elif len(questions) < 10:
        issues.append(f"Only {len(questions)} questions found (expected ~15)")

    for q in questions:
        q_num = q.get("question_number", "?")
        if not q.get("question_text"):
            issues.append(f"Assessment Q{q_num}: missing question_text")
        if not q.get("correct_letter"):
            issues.append(f"Assessment Q{q_num}: missing correct_letter")
        options = q.get("options", [])
        if len(options) < 4:
            issues.append(f"Assessment Q{q_num}: only {len(options)} options (expected 4)")

    return issues


def validate_restructured(data: dict) -> list[str]:
    """Validate restructured guided learning output."""
    issues = []

    if not data.get("concept_id"):
        issues.append("Missing concept_id")
    if not data.get("levels") or len(data["levels"]) == 0:
        issues.append("No levels generated")

    MIN_LEARN_SEGMENTS = 2
    has_mcat_patterns = False

    for level in data.get("levels", []):
        lv = level.get("level", "?")
        prefix = f"Level {lv}"
        level_name = (level.get("level_name") or "").lower()

        if "mcat" in level_name and "pattern" in level_name:
            has_mcat_patterns = True

        if not level.get("learn_segments") or len(level["learn_segments"]) == 0:
            issues.append(f"{prefix}: no learn_segments")
        elif len(level["learn_segments"]) < MIN_LEARN_SEGMENTS:
            issues.append(f"{prefix}: only {len(level['learn_segments'])} learn segment(s), need {MIN_LEARN_SEGMENTS}+")

        # Check learn segments
        for seg in level.get("learn_segments", []):
            if not seg.get("narrator_text"):
                issues.append(f"{prefix}: learn segment missing narrator_text")
            if not seg.get("display_text"):
                issues.append(f"{prefix}: learn segment missing display_text")
            word_count = len(seg.get("narrator_text", "").split())
            if word_count > 80:
                issues.append(f"{prefix}: narrator_text too long ({word_count} words, max ~60)")

        # Check questions
        if not level.get("check_questions") or len(level["check_questions"]) == 0:
            issues.append(f"{prefix}: no check_questions")

        for q in level.get("check_questions", []):
            q_type = q.get("question_type", "")
            if not q.get("question_text"):
                issues.append(f"{prefix}: check question missing question_text")

            # match_up questions have different schema — no correct_index
            if q_type == "match_up":
                if not q.get("options") or not isinstance(q["options"], list):
                    issues.append(f"{prefix}: match_up question missing 'options' array")
                if not q.get("matches") or not isinstance(q["matches"], list):
                    issues.append(f"{prefix}: match_up question missing 'matches' array")
                if q.get("options") and q.get("matches") and len(q["options"]) != len(q["matches"]):
                    issues.append(f"{prefix}: match_up options/matches length mismatch")
                # match_up should NOT have correct_index
                if q.get("correct_index") is not None:
                    issues.append(f"{prefix}: match_up should not have correct_index (use options+matches)")
            else:
                if q.get("correct_index") is None:
                    issues.append(f"{prefix}: check question missing correct_index")

            if not q.get("correct_response"):
                issues.append(f"{prefix}: check question missing correct_response")
            if not q.get("wrong_response"):
                issues.append(f"{prefix}: check question missing wrong_response")

        # Check question type variety
        q_types = [q.get("question_type") for q in level.get("check_questions", [])]
        if len(q_types) >= 3 and len(set(q_types)) == 1:
            issues.append(f"{prefix}: all check questions are same type '{q_types[0]}' — needs variety")

        # Check pro tip (not mandatory but flagged as warning)
        if not level.get("pro_tip") and not level.get("pro_tips"):
            issues.append(f"{prefix}: no pro_tip (recommended for every level)")

    # Check MCAT Patterns capstone
    if data.get("levels") and len(data["levels"]) >= 2 and not has_mcat_patterns:
        issues.append("Missing 'MCAT Patterns' capstone level (should be the final level)")

    # Check bridges
    if not data.get("bridges") or len(data["bridges"]) == 0:
        issues.append("No bridge connections generated")

    return issues


def validate_glossary(data: dict) -> list[str]:
    """Validate glossary extraction."""
    issues = []

    terms = data.get("terms", [])
    if len(terms) == 0:
        issues.append("No glossary terms found")
    elif len(terms) < 20:
        issues.append(f"Only {len(terms)} terms found — seems low for a full glossary")

    for term in terms:
        if not term.get("term"):
            issues.append("Glossary entry missing 'term' field")
        if not term.get("definition"):
            issues.append(f"Glossary term '{term.get('term', '?')}' missing definition")

    return issues


def print_validation(label: str, issues: list[str]):
    """Pretty-print validation results."""
    if not issues:
        print(f"  ✅ {label}: VALID")
    else:
        print(f"  ⚠️  {label}: {len(issues)} issue(s)")
        for issue in issues[:10]:  # Cap at 10 to avoid spam
            print(f"     • {issue}")
        if len(issues) > 10:
            print(f"     ... and {len(issues) - 10} more")
