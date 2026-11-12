"""The film's script: the ONE place where narration, captions and timing are written. Everything else is generated.
  python3 story.py      -> build/lines.json (for vo_plan.py), build/paras.json (for tts.py), build/para_<P>.json (for
                           split_lines.py), captions.js (for film.html), build/script.txt (for reviewers)
A row = (id, paragraph, at, caption, spoken)
  at       second on the picture's own clock at which the caption appears (the animation is written on this clock)
  caption  what is shown on screen
  spoken   what the voice says when it must differ from the caption ("Sex: F" on screen, "sex, F" spoken); None = same
One paragraph = one TTS take = one thought. Keep a paragraph to 3-5 lines so the voice keeps one melody across it."""
import json, os

PICTURE_END = 24.0
ROWS = [
    ("c1", "P1", 0.8, "Every dot here is one public dataset.", None),
    ("c2", "P1", 5.0, "A few of them, in blue, are the kind we need.", None),
    ("p1", "P2", 10.0, "The problem: each lab describes its samples in its own words.", None),
    ("p2", "P2", 15.0, "One lab writes ‘Sex: F’, another writes ‘gender: female’.", "One lab writes sex, F; another writes gender, female."),
    ("s1", "P3", 19.5, "So we built a tool that reads them all and writes one common record.", None),
]

os.makedirs("build", exist_ok=True)
lines = [{"id": i, "para": p, "at": at, "text": sp or cap} for i, p, at, cap, sp in ROWS]
json.dump(lines, open("build/lines.json", "w"), indent=1, ensure_ascii=False)
paras = sorted({p for _, p, *_ in ROWS})
json.dump([{"id": p, "text": " ".join(l["text"] for l in lines if l["para"] == p)} for p in paras], open("build/paras.json", "w"), indent=1, ensure_ascii=False)
for p in paras:
    json.dump([{"id": l["id"], "text": l["text"]} for l in lines if l["para"] == p], open(f"build/para_{p}.json", "w"), indent=1, ensure_ascii=False)
open("captions.js", "w").write("window.CAPS = " + json.dumps([{"id": i, "at": at, "text": cap} for i, _, at, cap, _ in ROWS], ensure_ascii=False) +
                               ";\nwindow.PICTURE_END = %s;\n" % PICTURE_END)
open("build/script.txt", "w").write("\n\n".join(p + "\n" + "\n".join(l["text"] for l in lines if l["para"] == p) for p in paras) + "\n")
words = sum(len(l["text"].split()) for l in lines)
print(len(lines), "lines,", words, "words, about", round(words / 150 * 60), "s of speech at 150 wpm; picture", PICTURE_END, "s")
