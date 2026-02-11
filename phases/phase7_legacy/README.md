# Phase 7 Legacy: LLM Game Classification

Core Function: Use Gemini to classify possible game types per section.
Role in Overall Pipeline: Legacy fallback for game hints (superseded by primitives + compiler).
Data Inputs: `phases/phase1/output/extracted/{book}/chNN_*.json`, `phases/phase1/output/extracted/{book}/_figure_catalog.json`
Outputs: `phases/phase7_legacy/output/classified/{book}/{section_id}-*_games.json`
