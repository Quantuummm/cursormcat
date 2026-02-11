# Phase 8: Restructure Guided Learning

Core Function: Transform extracted content into ADHD-friendly guided learning with levels, segments, and questions.
Role in Overall Pipeline: Produces the core lesson JSON consumed by the frontend and validation.
Data Inputs: `phases/phase1/output/extracted/{book}/chNN_*.json`, `phases/phase1/output/extracted/{book}/_figure_catalog.json`, `phases/phase7_legacy/output/classified/{book}/*_games.json` (legacy), `lore/world.json`

Outputs: `phases/phase8/output/structured/{book}/{concept_id}.json`
