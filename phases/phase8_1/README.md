# Phase 8.1: Compile Modes

Core Function: Compile engine-ready mode instances from primitives (and optional structured content).
Role in Overall Pipeline: Generates deterministic game payloads unlocked after guided learning.
Data Inputs:
- `phases/phase7/output/primitives/{book}/{section_id}.json`
- `phases/phase4/output/extracted/{book}/_glossary.json`
- `phases/phase5/output/extracted/{book}/_figure_catalog.json`
- `phases/phase8/output/structured/{book}/*.json` (optional)

Outputs:
- `phases/phase8_1/output/compiled/{book}/{section_id}_modes.json`
