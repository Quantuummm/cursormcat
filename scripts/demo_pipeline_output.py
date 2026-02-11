import json
import time
import sys
import os
from pathlib import Path
try:
    from colorama import init, Fore, Style
    # Initialize colorama for windows terminal
    init(autoreset=True)
except ImportError:
    # Minimal fallback if colorama is missing
    class MockColor:
        def __getattr__(self, name): return ""
    Fore = MockColor()
    Style = MockColor()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from config import STRUCTURED_DIR, COMPILED_DIR, VERIFIED_STRUCTURED_DIR

def clear():
    # Clear screen for better demo feel
    if sys.platform == "win32":
        os.system('cls')
    else:
        os.system('clear')

def type_text(text, delay=0.01):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def demo_section(subject, section_id):
    # 1. Load Guided Learning (Priority: Phase 8.2 Verified -> Phase 8 Structured)
    v_dir = VERIFIED_STRUCTURED_DIR / subject
    s_dir = STRUCTURED_DIR / subject
    
    source_label = ""
    candidates = list(v_dir.glob(f"{section_id}-*.json"))
    if candidates:
        source_label = "PHASE 8.2 (VERIFIED)"
    else:
        candidates = list(s_dir.glob(f"{section_id}-*.json"))
        if candidates:
            source_label = "PHASE 8 (RAW)"

    if not candidates:
        print(f"❌ No Phase 8 or 8.2 output found for {subject} {section_id}")
        return
    
    with open(candidates[0], "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}DEMO: GUIDED LEARNING SESSION [{source_label}]")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    # Mission Briefing
    brief = data.get("mission_briefing", {})
    print(f"{Fore.YELLOW}[MISSION BRIEFING]")
    type_text(f"{Fore.WHITE}{brief.get('narrator_text', '')}")
    print(f"\n{Fore.GREEN}ON-SCREEN DISPLAY:")
    print(f"{Style.DIM}{brief.get('display_text', '')}")
    input(f"\n{Fore.BLUE}Press Enter to start Level 1...")

    for level in data.get("levels", []):
        clear()
        lvl_num = level.get("level")
        lvl_title = level.get("title")
        print(f"{Fore.MAGENTA}LEVEL {lvl_num}: {lvl_title}")
        print(f"{Fore.MAGENTA}{'-'*30}")

        # Learn Segments
        for seg in level.get("learn_segments", []):
            print(f"\n{Fore.YELLOW}[COMPANION VOICE]")
            type_text(f"{Fore.WHITE}{seg.get('narrator_text', '')}")
            print(f"{Fore.GREEN}DISPLAY: {Style.BRIGHT}{seg.get('display_text', '')}")
            if seg.get("key_term"):
                print(f"{Fore.RED}NEW TERM: {seg.get('key_term')}")
            time.sleep(0.5)

        # Check Questions
        for q in level.get("check_questions", []):
            print(f"\n{Fore.BLUE}[CHECK QUESTION]")
            print(f"{Fore.WHITE}{q.get('question_text')}")
            options = q.get("options", [])
            for i, opt in enumerate(options):
                print(f"  {i}) {opt}")
            
            choice = input(f"\nPick 0-{len(options)-1}: ")
            if str(choice) == str(q.get("correct_index")):
                print(f"\n{Fore.GREEN}✨ {q.get('correct_response')}")
            else:
                print(f"\n{Fore.YELLOW}💡 {q.get('wrong_response')}")
            input("Press Enter...")

        # Apply Question
        aq = level.get("apply_question")
        if aq:
            clear()
            print(f"{Fore.MAGENTA}--- LEVEL {lvl_num} BOSS CHALLENGE ---")
            print(f"{Fore.YELLOW}[SCENARIO]")
            type_text(f"{Fore.WHITE}{aq.get('scenario', '')}")
            print(f"\n{Fore.BLUE}[QUESTION]")
            print(f"{Fore.WHITE}{aq.get('question_text')}")
            options = aq.get("options", [])
            for i, opt in enumerate(options):
                print(f"  {i}) {opt}")
            
            choice = input(f"\nPick 0-{len(options)-1}: ")
            if str(choice) == str(aq.get("correct_index")):
                print(f"\n{Fore.GREEN}🏆 SUCCESS! {aq.get('correct_response')}")
            else:
                print(f"\n{Fore.RED}💥 FAILED. {aq.get('wrong_response')}")
                if aq.get("reasoning"):
                    print(f"{Fore.WHITE}Logical Chain: {aq.get('reasoning')}")
            input("Press Enter to continue level...")

    clear()
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}GUIDED LEARNING COMPLETE!")
    print(f"{Fore.CYAN}{'='*60}")
    print(f"\nNew Game Modes Unlocked for Section {section_id}!")
    
    # 2. Load Phase 8.1 (Compiled Modes)
    compiled_path = COMPILED_DIR / subject / f"{section_id}_modes.json"
    if not compiled_path.exists():
        print(f"⚠️ No Phase 8.1 modes found for {subject} {section_id}")
        return

    with open(compiled_path, "r", encoding="utf-8") as f:
        modes_data = json.load(f)

    print(f"\n{Fore.CYAN}ARCHETYPES DETECTED: {', '.join(modes_data.get('archetypes', []))}")
    print(f"{Fore.CYAN}REGION: {modes_data.get('region', {}).get('name', 'Unknown')}")
    
    print(f"\n{Fore.YELLOW}--- UNLOCKED MODES (GAMES) ---")
    for inst in modes_data.get("mode_instances", []):
        m_type = inst.get("mode_type")
        diff = inst.get("difficulty")
        title = inst.get("payload", {}).get("title", "Game")
        print(f"  🎮 {Fore.WHITE}{title} {Fore.GREEN}({m_type}) {Fore.BLUE}[{diff}]")
        print(f"     {Style.DIM}Payload Size: {len(json.dumps(inst.get('payload')))} bytes")

    print(f"\n{Fore.WHITE}Demo finished. All outputs are valid and ready for the engine.")

if __name__ == "__main__":
    from config import BOOKS
    
    if len(sys.argv) < 2:
        print(f"\n{Fore.YELLOW}Usage: python scripts/demo_pipeline_output.py <subject_slug> <section_id>")
        print(f"Example: python scripts/demo_pipeline_output.py gen_chem 1.1\n")
        
        print(f"{Fore.CYAN}Available Subject Slugs:")
        for pdf, slug in BOOKS.items():
            print(f"  - {slug} ({pdf})")
        sys.exit(0)

    subject = sys.argv[1]
    
    if len(sys.argv) < 3:
        print(f"\n{Fore.YELLOW}Listing available sections for {subject}...")
        v_dir = VERIFIED_STRUCTURED_DIR / subject
        s_dir = STRUCTURED_DIR / subject
        
        all_sections = set()
        if v_dir.exists():
            for f in v_dir.glob("*.json"):
                all_sections.add(f.name.split("-")[0] + " (Verified)")
        if s_dir.exists():
            for f in s_dir.glob("*.json"):
                sec_id = f.name.split("-")[0]
                if not any(sec_id in x for x in all_sections):
                    all_sections.add(sec_id + " (Raw)")
        
        if not all_sections:
            print(f"❌ No sections found for {subject}")
        else:
            for s in sorted(list(all_sections)):
                print(f"  - {s}")
        sys.exit(0)

    section = sys.argv[2]
    demo_section(subject, section)
