# Phase 2: Extract Chapter Assessments

Core Function: Extract chapter diagnostic MCQs, answers, and explanations.
Role in Overall Pipeline: Creates assessment content used for pre-checks and wrong-answer enrichment.
Data Inputs: `pdfs/{book}.pdf`, `phases/phase1/output/extracted/{book}/_toc.json`

Outputs: `phases/phase2/output/extracted/{book}/chNN_assessment.json`
