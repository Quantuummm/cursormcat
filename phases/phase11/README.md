# Phase 11: Upload to Firestore

Core Function: Upload structured content, glossaries, assessments, and bridges to Firestore.
Role in Overall Pipeline: Publishes content for frontend consumption.
Data Inputs: `phases/phase8/output/structured/{book}/*.json`, `phases/phase1/output/extracted/{book}/*.json`, `phases/phase9/output/bridges/*.json`
Outputs: Firestore collections (no local files)
