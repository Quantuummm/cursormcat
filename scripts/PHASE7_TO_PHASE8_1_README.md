# Phase 7 → Phase 8.1 Pipeline

## Overview

This pipeline processes MCAT Kaplan content from **Phase 5** directly into **Phase 7** and **Phase 8.1**, skipping phases 6, 6_1, and 8.

### Pipeline Flow

```
Phase 5 (Figure Catalog) ─────┐
                              │
Phase 4 (Glossary) ───────────┼──→ Phase 7 (Build Primitives) ──→ Phase 8.1 (Compile Modes) ──→ Validation
                              │
Phase 3 (Sections) ───────────┘
```

### What Each Phase Does

- **Phase 3**: Extracted section content with learning objectives, key concepts, and passage text
- **Phase 4**: Glossary terms with definitions
- **Phase 5**: Figure catalog with captions and metadata
- **Phase 7**: Builds deterministic primitives (signal layer) for game mode compilation
- **Phase 8.1**: Compiles engine-ready game modes from primitives and source content

### Skipped Phases

- **Phase 6**: Assessment enrichment (wrong answer explanations)
- **Phase 6.1**: Assessment verification
- **Phase 8**: Guided learning restructure (optional for Phase 8.1)

Phase 8.1 will use Phase 7 primitives and optionally incorporate Phase 8 content if available, but doesn't require it.

## Usage

### Run Full Pipeline (All Subjects)

```powershell
python scripts/run_phase7_to_phase8_1.py
```

This will:
1. Build primitives for all 7 subjects (Phase 7)
2. Compile game modes for all subjects (Phase 8.1)
3. Run validation on compiled modes
4. Show completion summary

### Run Single Subject

```powershell
python scripts/run_phase7_to_phase8_1.py --subject gen_chem
```

### Run in Parallel (5 Workers)

```powershell
python scripts/run_phase7_to_phase8_1.py --parallel
```

Uses ThreadPoolExecutor to process subjects in parallel. Both Phase 7 and 8.1 are **deterministic** and don't require API calls, so parallel execution is safe and fast.

### Run Validation Only

```powershell
python scripts/run_phase7_to_phase8_1.py --validate-only
```

Skips processing and only validates existing Phase 8.1 outputs.

## Parallel Processing with Gemini APIs

Although Phase 7 and 8.1 are deterministic and don't use API calls themselves, if you need to run earlier phases (1-5) that haven't completed yet, you can use the main parallel pipeline:

```powershell
# Run specific waves
python scripts/parallel_pipeline.py --wave 1  # Phases 2, 3, 4, 5
python scripts/parallel_pipeline.py --wave 2  # Phases 6, 6.1, 7 (we skip 6 and 6.1)
```

The parallel pipeline uses **5 Gemini API keys** configured in your `.env`:
- `GEMINI_API_KEY_1` through `GEMINI_API_KEY_5`

Each key handles separate subjects/chapters concurrently, respecting the 200 RPM quota per key.

## Output Directories

```
phases/
├── phase3/output/extracted/{subject}/      # Chapter section JSON files (input)
├── phase4/output/extracted/{subject}/      # Glossary (input)
├── phase5/output/extracted/{subject}/      # Figure catalog (input)
├── phase7/output/primitives/{subject}/     # Primitive JSON files (output)
└── phase8_1/
    ├── output/compiled/{subject}/          # Compiled mode JSON files (output)
    └── validation/                         # Validation scripts
        ├── verify_compiled_modes.py
        └── verification_report_{subject}.txt
```

## Validation

After Phase 8.1 completes, the validation script checks:

- ✅ Mode structure and schema compliance
- ✅ Engine field consistency (rapid_recall, sequence_builder, etc.)
- ✅ Payload integrity (cards, steps, buckets, items)
- ✅ No placeholder text (`[REDACTED]`, `TODO`)
- ✅ Correct answer indices within bounds
- ✅ No duplicate options
- ✅ All required fields present

Validation runs automatically after processing, or manually:

```powershell
# Validate specific subject
python phases/phase8_1/validation/verify_compiled_modes.py --subject gen_chem

# Validate specific section
python phases/phase8_1/validation/verify_compiled_modes.py --section 1.1
```

## Expected Timeline

For all 7 subjects (sequential):
- **Phase 7**: ~5-10 minutes (deterministic, no API)
- **Phase 8.1**: ~10-20 minutes (deterministic, no API)
- **Validation**: ~1-2 minutes

Total: **~20-30 minutes**

With `--parallel` flag: **~5-10 minutes total**

## Subjects Processed

1. biology
2. biochemistry
3. gen_chem
4. org_chem
5. physics
6. psych_soc
7. cars

## Troubleshooting

### "No chapter files (run Phase 3)"

Phase 3 outputs are missing. Run:
```powershell
python scripts/parallel_pipeline.py --wave 1
```

### "Figure catalog not found"

Phase 5 outputs are missing. Ensure Phase 5 completed successfully.

### Validation Errors

Check the validation report in:
```
phases/phase8_1/validation/verification_report_{subject}.txt
```

Common issues:
- **Empty payloads**: Source section had insufficient content
- **Missing correct_index**: Compilation logic issue, check primitives
- **Placeholder text**: Content extraction incomplete

### Re-running After Fixes

The pipeline is **idempotent** — you can re-run safely. It will overwrite previous outputs.

```powershell
# Re-process single subject
python scripts/run_phase7_to_phase8_1.py --subject biology

# Re-run validation
python scripts/run_phase7_to_phase8_1.py --validate-only
```

## Next Steps

After Phase 8.1 completes successfully:

1. **Phase 9**: Build cross-subject bridges
   ```powershell
   python phases/phase9/phase9_enrich_bridges.py
   ```

2. **Phase 10**: Generate TTS audio (optional)
   ```powershell
   python phases/phase10/phase10_generate_tts.py --subject gen_chem
   ```

3. **Phase 11**: Upload to Firestore
   ```powershell
   python phases/phase11/phase11_upload_firestore.py --subject gen_chem
   ```

## Development Notes

- Phase 7 and 8.1 are **deterministic**: Same inputs always produce same outputs
- No randomness or LLM calls, so results are reproducible
- Phase 8.1 dynamically builds primitives if Phase 7 outputs are missing
- Optional dependencies (Phase 8 structured content) gracefully degrade
- Validation is comprehensive — use it to catch issues early
