# Phase 8.1 Validation

This directory contains tools and reports for validating the engine-ready mode instances generated in Phase 8.1.

## Validation & Fix Loop

The system uses a **Verify -> Fix -> Re-compile** cycle:

1. **Verify**: Use `verify_compiled_modes.py` to detect issues in the final JSONs.
2. **Fix**: 
   - If the error is **Content/Logic**: Fix the upstream source data (usually in Phase 8 `structured/` or Phase 3 `extracted/`) or use `scripts/fix_and_verify.py`.
   - If the error is **Structural/Systemic**: Update the compiler logic in `scripts/utils/mode_compiler.py`.
3. **Re-compile**: Run `phase8_1_compile_modes.py` to regenerate the JSONs.
4. **Re-verify**: Run `verify_compiled_modes.py` to ensure the fix is successful.

The script `auto_fix_and_recompile.py` can be used to automate this cycle for a specific subject.

## Tools

- `verify_compiled_modes.py`: A deterministic validator that checks JSON integrity, schema compliance, and engine-specific logic (e.g., ensuring Rapid Recall cards have 4 options and a valid correct index).

## Usage

To verify all compiled modes for a specific subject (e.g., General Chemistry):
```bash
python phases/phase8_1/validation/verify_compiled_modes.py --subject gen_chem
```

To verify a specific section:
```bash
python phases/phase8_1/validation/verify_compiled_modes.py --subject gen_chem --section 1.1
```

## Validation Logic
The script checks for:
- **Structural Integrity**: All required top-level fields (subject, chapter, section, mode_instances).
- **Engine Schemas**: Correct payload structures for `rapid_recall`, `sequence_builder`, `sort_buckets`, and `equation_forge`.
- **Formatting**: Detects unclosed LaTeX (`$`) and common placeholder artifacts (`[REDACTED]`, `TODO`).
- **Consistency**: Ensures the internal data matches the file system structure.
