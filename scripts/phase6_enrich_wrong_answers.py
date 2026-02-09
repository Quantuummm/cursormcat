"""
Phase 6: Enrich chapter assessment questions with wrong-answer explanations.
Kaplan only provides explanations for the CORRECT answer. This phase uses AI
to generate specific explanations for why each WRONG option is wrong.

Requires: Phase 2 complete (needs ch*_assessment.json files).

Usage:
    python scripts/phase6_enrich_wrong_answers.py                    # All books
    python scripts/phase6_enrich_wrong_answers.py biology.pdf        # One book
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import EXTRACTED_DIR, PROMPTS_DIR, BOOKS
from utils.gemini_client import GeminiClient


def run(pdf_filename: str = None):
    """Add wrong-answer explanations to chapter assessments."""
    client = GeminiClient()

    prompt_template = (PROMPTS_DIR / "wrong_answer_enrichment.txt").read_text(encoding="utf-8")

    subjects = [BOOKS[pdf_filename]] if pdf_filename and pdf_filename in BOOKS else BOOKS.values()

    for subject in subjects:
        subject_dir = EXTRACTED_DIR / subject

        # Find all assessment files
        assessment_files = sorted(subject_dir.glob("ch*_assessment.json"))
        if not assessment_files:
            print(f"⏭️  Skipping {subject}: No assessment files found (run Phase 2)")
            continue

        print(f"\n{'='*60}")
        print(f"🔧 Enriching wrong-answer explanations: {subject}")
        print(f"{'='*60}")

        for assess_path in assessment_files:
            assessment = json.loads(assess_path.read_text(encoding="utf-8"))
            questions = assessment.get("questions", [])
            ch_num = assessment.get("chapter_number", "?")

            if not questions:
                continue

            print(f"\n  📝 Chapter {ch_num}: {len(questions)} questions")

            # Prepare questions for the prompt (only those without wrong_explanations)
            questions_needing_enrichment = [
                q for q in questions if not q.get("wrong_explanations")
            ]

            if not questions_needing_enrichment:
                print(f"     ✅ Already enriched, skipping")
                continue

            # Format questions for prompt
            questions_for_prompt = []
            for q in questions_needing_enrichment:
                questions_for_prompt.append({
                    "question_number": q["question_number"],
                    "question_text": q["question_text"],
                    "options": q["options"],
                    "correct_letter": q["correct_letter"],
                    "kaplan_explanation": q.get("kaplan_explanation", ""),
                })

            prompt = prompt_template.format(
                questions_json=json.dumps(questions_for_prompt, indent=2)
            )

            print(f"     🔍 Generating explanations...")
            enrichments = client.enrich(prompt, phase=f"P6_wrong_answers_ch{ch_num}")

            # Merge enrichments back into assessment
            enrichment_map = {}
            if isinstance(enrichments, list):
                for e in enrichments:
                    enrichment_map[e["question_number"]] = e.get("wrong_explanations", {})
            elif isinstance(enrichments, dict) and "questions" in enrichments:
                # Sometimes Gemini wraps in an object
                for e in enrichments["questions"]:
                    enrichment_map[e["question_number"]] = e.get("wrong_explanations", {})

            enriched_count = 0
            for q in assessment["questions"]:
                if q["question_number"] in enrichment_map:
                    q["wrong_explanations"] = enrichment_map[q["question_number"]]
                    enriched_count += 1

            print(f"     ✅ Enriched {enriched_count}/{len(questions_needing_enrichment)} questions")

            # Save updated assessment (overwrite)
            with open(assess_path, "w", encoding="utf-8") as f:
                json.dump(assessment, f, indent=2, ensure_ascii=False)
            print(f"     💾 Updated: {assess_path.name}")

    print(f"\n✅ Phase 6 complete!")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    run(target)
