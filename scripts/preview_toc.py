"""Quick preview of extracted TOC data."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import EXTRACTED_DIR

subject = sys.argv[1] if len(sys.argv) > 1 else "biology"
toc_path = EXTRACTED_DIR / subject / "_toc.json"
toc = json.loads(toc_path.read_text(encoding="utf-8"))

print(f"BOOK: {toc['book_title']}")
print(f"CHAPTERS: {len(toc['chapters'])}")
print()

for ch in toc["chapters"]:
    sections = ch.get("sections", [])
    hy = sum(1 for s in sections if s.get("is_high_yield"))
    pct = ch.get("chapter_profile", {}).get("mcat_relevance_percent", "?")
    title = ch["chapter_title"]
    num = ch["chapter_number"]
    print(f"  Ch {num:2d}: {title:<50} {len(sections)} sec ({hy} HY) | {pct}% MCAT")
    for s in sections:
        hy_tag = " [HY]" if s.get("is_high_yield") else ""
        print(f"         {s['section_id']} {s['section_title']}{hy_tag}")
    print()

g = toc.get("glossary_pages")
if g:
    print(f"GLOSSARY: pages {g['page_start']}-{g['page_end']}")
else:
    print("GLOSSARY: not detected (may need manual page range)")
