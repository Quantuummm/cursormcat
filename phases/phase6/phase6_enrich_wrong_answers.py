"""
Phase 6: Enrich chapter assessment questions with wrong-answer explanations.
Kaplan only provides explanations for the CORRECT answer. This phase uses AI
to generate specific explanations for why each WRONG option is wrong.

Requires: Phase 2 complete (needs ch*_assessment.json files).

Usage:
    python phases/phase6/phase6_enrich_wrong_answers.py                    # All books
    python phases/phase6/phase6_enrich_wrong_answers.py biology.pdf        # One book
"""

import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from config import ASSESSMENTS_DIR, ENRICHED_ASSESSMENTS_DIR, BOOKS
from utils.gemini_client import GeminiClient


def run(pdf_filename: str = None, chapter_num: int = None):
    """Add wrong-answer explanations to chapter assessments."""
    client = GeminiClient()

    prompt_template = (Path(__file__).parent / "wrong_answer_enrichment.txt").read_text(encoding="utf-8")

    subjects = [BOOKS[pdf_filename]] if pdf_filename and pdf_filename in BOOKS else BOOKS.values()

    for subject in subjects:
        source_dir = ASSESSMENTS_DIR / subject
        output_dir = ENRICHED_ASSESSMENTS_DIR / subject
        output_dir.mkdir(parents=True, exist_ok=True)

        # Find all assessment files
        assessment_files = sorted(source_dir.glob("ch*_assessment.json"))
        if not assessment_files:
            print(f"⏭️  Skipping {subject}: No assessment files found in Phase 2")
            continue

        print(f"\n{'='*60}")
        print(f"🔧 Phase 6: Enriching wrong-answer explanations: {subject}")
        print(f"{'='*60}")

        for assess_path in assessment_files:
            assessment = json.loads(assess_path.read_text(encoding="utf-8"))
            ch_num = assessment.get("chapter_number")
            
            if chapter_num is not None and ch_num != chapter_num:
                continue

            questions = assessment.get("questions", [])
            print(f"\n  📝 Chapter {ch_num}: {len(questions)} questions")

            output_path = output_dir / assess_path.name
            
            # If output already exists and is complete, skip generating unless we want to force
            if output_path.exists():
                existing = json.loads(output_path.read_text(encoding="utf-8"))
                if all(q.get("wrong_explanations") and q.get("tts_wrong_feedback") for q in existing.get("questions", [])):
                    print(f"     ✅ Already enriched in {output_path.name}, skipping")
                    continue
                # If it exists but is partial, use it as baseline
                assessment = existing

            # Prepare questions for the prompt (only those without complete enrichment)
            questions_needing_enrichment = [
                q for q in assessment.get("questions", []) 
                if not q.get("wrong_explanations") or not q.get("tts_wrong_feedback")
            ]

            if not questions_needing_enrichment:
                print(f"     ✅ No questions need enrichment")
                # Still save to output_dir even if we just copied it
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(assessment, f, indent=2, ensure_ascii=False)
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
                    enrichment_map[e["question_number"]] = {
                        "wrong_explanations": e.get("wrong_explanations", {}),
                        "tts_wrong_feedback": e.get("tts_wrong_feedback", {})
                    }
            elif isinstance(enrichments, dict) and "questions" in enrichments:
                # Sometimes Gemini wraps in an object
                for e in enrichments["questions"]:
                    enrichment_map[e["question_number"]] = {
                        "wrong_explanations": e.get("wrong_explanations", {}),
                        "tts_wrong_feedback": e.get("tts_wrong_feedback", {})
                    }

            enriched_count = 0
            for q in assessment["questions"]:
                if q["question_number"] in enrichment_map:
                    q["wrong_explanations"] = enrichment_map[q["question_number"]]["wrong_explanations"]
                    q["tts_wrong_feedback"] = enrichment_map[q["question_number"]]["tts_wrong_feedback"]
                    enriched_count += 1

            print(f"     ✅ Enriched {enriched_count}/{len(questions_needing_enrichment)} questions")

            # Save to Phase 6 output folder
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(assessment, f, indent=2, ensure_ascii=False)
            print(f"     💾 Saved to Phase 6: {output_path.name}")

    print(f"\n✅ Phase 6 complete!")


if __name__ == "__main__":
    pdf = sys.argv[1] if len(sys.argv) > 1 else None
    chapter = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run(pdf, chapter)
