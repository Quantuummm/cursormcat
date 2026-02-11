"""
Auto-Fix & Recompile Orchestrator
--------------------------------
1. Runs Phase 8.1 validation.
2. If failures are found, alerts the user (or agent) to fix Phase 8 source.
3. Automatically triggers re-compilation of just the failed sections.
4. Final verification check.
"""

import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "phases" / "phase8_1" / "validation" / "verify_compiled_modes.py"
COMPILER = REPO_ROOT / "phases" / "phase8_1" / "phase8_1_compile_modes.py"

def run_command(cmd_parts):
    print(f"🚀 Running: {' '.join(cmd_parts)}")
    result = subprocess.run([sys.executable] + cmd_parts, capture_output=True, text=True)
    return result

def main(subject):
    print(f"🛠️  Orchestrating fix loop for {subject}...")
    
    # Step 1: Verify current state
    v_res = run_command([str(VALIDATOR), "--subject", subject])
    
    if v_res.returncode == 0:
        print("✅ Everything looks perfect! No fixes needed.")
        return

    print("⚠️  Validation found issues. Identifying sections...")
    # Extract section IDs from output (simple approach)
    import re
    failed_sections = list(set(re.findall(r"(\d+\.\d+)_modes\.json", v_res.stdout + v_res.stderr)))
    
    if not failed_sections:
        # Check if maybe it was a subject-level error
        print(v_res.stdout)
        return

    print(f"📍 Found {len(failed_sections)} sections with issues: {', '.join(failed_sections)}")
    
    # Step 2: In a real automated loop, we would trigger scripts/fix_and_verify.py here.
    # For now, we assume the user/agent has fixed the source or we are testing re-compilation.
    
    for sec in failed_sections:
        print(f"\n🔄 Re-compiling section {sec}...")
        c_res = run_command([str(COMPILER), "--section", sec])
        if c_res.returncode != 0:
            print(f"❌ Re-compilation failed for {sec}")
            continue
            
        print(f"🧪 Re-verifying {sec}...")
        v_res_new = run_command([str(VALIDATOR), "--subject", subject, "--section", sec])
        if v_res_new.returncode == 0:
            print(f"✨ Section {sec} is now FIXED and VALID!")
        else:
            print(f"❌ Section {sec} still has issues.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python auto_fix_and_recompile.py <subject>")
        sys.exit(1)
    main(sys.argv[1])
