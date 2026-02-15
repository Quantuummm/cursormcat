# Phase 10: Generate TTS Audio

Core Function: Generate MP3 audio from narrator_text using Google Cloud TTS.
Role in Overall Pipeline: Produces audio assets for spoken lessons.
Data Inputs: `phases/phase8/output/structured/{book}/*.json`

Outputs: `phases/phase10/output/audio/{book}/{concept_id}/*.mp3`

## MCP Connections
- **Google Cloud MCP**: Handles Text-to-Speech API interactions and storage autonomously.
- **Google Search MCP**: Allows enrichment of narrator scripts with real-time research.
- **Firestore MCP**: Manages authentication and configuration state.

Using MCP servers allows the AI agent to possess much better control over the TTS generation and verification process compared to standard API keys.
