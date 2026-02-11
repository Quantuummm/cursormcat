# Phase 6.1: Verify Wrong Answers

Core Function: Verify and optionally fix wrong-answer explanations and TTS wrong feedback.
Role in Overall Pipeline: Ensures AI-generated feedback is accurate, non-contradictory, and supportive.
Data Inputs: `phases/phase1/output/extracted/{book}/chNN_assessment.json`

Outputs: `phases/phase6_1/output/verification_assessments/{book}/chNN_wrong_answer_verification.json` (and optional fixes applied to `phases/phase1/output/extracted/{book}/chNN_assessment.json`) 
