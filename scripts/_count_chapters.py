import json, os
root = r'c:\Users\Rauf\Documents\GitHub\cursormcat\phases\phase1\output\extracted'
for subj in sorted(os.listdir(root)):
    toc_path = os.path.join(root, subj, '_toc.json')
    if os.path.exists(toc_path):
        with open(toc_path, encoding='utf-8') as f:
            d = json.load(f)
        chs = d.get('chapters', [])
        nums = [c['chapter_number'] for c in chs]
        print(f"{subj}: {len(chs)} chapters {nums}")
