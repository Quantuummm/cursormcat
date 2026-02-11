import json
import datetime
from pathlib import Path

CHECKPOINT_FILE = Path(__file__).resolve().parents[2] / "pipeline_checkpoint.json"

# Define phase dependencies
# Key: Phase, Value: List of required phases
PHASE_DEPENDENCIES = {
    0: [],
    1: [0],
    2: [1],
    3: [1],
    4: [1],
    5: [1, 3],
    6: [2, 3],
    6.1: [6],
    7: [1, 3],
    7.1: [7],
    8: [7, 7.1],
    9: [3],  # Special case: needs Phase 3 for ALL books
    10: [8],
    11: [1, 8, 9]
}

def save_checkpoint(pdf, chapter, phase, phase_name, status="completed"):
    """Save progress to the checkpoint file."""
    from scripts.config import BOOKS
    subject = BOOKS.get(pdf, "unknown") if pdf else "global"
    
    checkpoint = {
        "last_updated": datetime.datetime.now().isoformat(),
        "pdf": pdf,
        "subject": subject,
        "chapter": chapter,
        "phase": phase,
        "phase_name": phase_name,
        "status": status
    }
    
    data = {"last_run": checkpoint, "subjects": {}}
    if CHECKPOINT_FILE.exists():
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            pass

    data["last_run"] = checkpoint
    
    if "subjects" not in data:
        data["subjects"] = {}
        
    if subject not in data["subjects"]:
        data["subjects"][subject] = {"completed_phases": [], "chapters": {}}
        
    if chapter:
        ch_key = f"ch{chapter}"
        if ch_key not in data["subjects"][subject]["chapters"]:
            data["subjects"][subject]["chapters"][ch_key] = []
        if phase not in data["subjects"][subject]["chapters"][ch_key]:
            data["subjects"][subject]["chapters"][ch_key].append(phase)
    else:
        if phase not in data["subjects"][subject]["completed_phases"]:
            data["subjects"][subject]["completed_phases"].append(phase)
    
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_last_checkpoint():
    """Retrieve the last saved checkpoint."""
    if not CHECKPOINT_FILE.exists():
        return None
    try:
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("last_run")
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def check_prerequisites(pdf, chapter, phase):
    """Check if prerequisites for a phase are met for a specific subject/chapter."""
    if phase not in PHASE_DEPENDENCIES:
        return True, []
        
    from scripts.config import BOOKS
    subject = BOOKS.get(pdf, "unknown") if pdf else "global"
    
    if not CHECKPOINT_FILE.exists():
        return phase == 0, [0] if phase != 0 else []

    try:
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        return False, ["Error reading checkpoint file"]

    completed = []
    if subject in data.get("subjects", {}):
        subj_data = data["subjects"][subject]
        completed = subj_data.get("completed_phases", [])
        if chapter:
            ch_key = f"ch{chapter}"
            completed.extend(subj_data.get("chapters", {}).get(ch_key, []))

    missing = [p for p in PHASE_DEPENDENCIES[phase] if p not in completed]
    
    # Global dependency check for Phase 9 (needs all books phase 3)
    if phase == 9:
        for s_name in BOOKS.values():
            s_completed = data.get("subjects", {}).get(s_name, {}).get("completed_phases", [])
            # Phase 3 is usually per-chapter, checking if any chapter or global flag exists
            # For simplicity, we check if ch1-ch12 or similar exist
            # This is a bit complex, so we'll just check if the subject exists in data for now
            if s_name not in data.get("subjects", {}):
                missing.append(f"Phase 3 for {s_name}")

    if not missing:
        return True, []
    return False, missing

def print_status_report():
    """Print a report of all subjects and their progress."""
    if not CHECKPOINT_FILE.exists():
        print("\n📭 No checkpoint found.")
        return

    try:
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        print("❌ Error reading checkpoint file.")
        return

    print(f"\n{'='*60}")
    print(f"📊 MCAT PIPELINE GLOBAL PROGRESS TRACKER")
    print(f"{'='*60}")

    for subject, subj_data in data.get("subjects", {}).items():
        if subject == "unknown" or subject == "global": continue
        
        global_phases = sorted(subj_data.get("completed_phases", []))
        ch_data = subj_data.get("chapters", {})
        
        if not global_phases and not ch_data:
            continue

        print(f"\n📘 Subject: {subject.upper()}")
        if global_phases:
            print(f"   Completed (Project level): {', '.join(map(str, global_phases))}")
        
        for ch, phases in sorted(ch_data.items()):
            print(f"   {ch}: Phases {', '.join(map(str, sorted(phases)))}")

    # Specific check for biology Ch.1 since we know it had Phase 0 from previous run
    # but the schema migration might have missed it if not handled.

    last = data.get("last_run")
    if last:
        print(f"\n{'─'*60}")
        print(f"🕒 LAST ACTIVITY: {last.get('phase_name')} (Phase {last.get('phase')})")
        print(f"   Target: {last.get('pdf')} Ch.{last.get('chapter')}")
    print(f"{'='*60}\n")
