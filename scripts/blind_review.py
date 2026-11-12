"""Blind listening check of narration clips by Gemini through agy (agy_call_media.sh, next to this script).
  blind_review.py prepare DIR label=clip.wav:script.txt ...   copy clips under random names -> DIR/clips, DIR/key.json
  blind_review.py single DIR REPS                             one clip per call, REPS times -> DIR/out/single_<clip>_<rep>.txt
  blind_review.py report DIR                                  scores per label, and every concrete defect with its time
What this is good for, measured: finding CONCRETE defects (a mispronounced word, a swallowed consonant, an odd pause).
What it is not good for: ranking voices. Repeat scores of the same clip differ by 1-2 points, and when two clips are
sent in one call the judge picks the first-played one about 5 times in 6. So: one clip per call, >= 3 repeats, loudness
made equal beforehand, and a defect counts only when it is reported in at least 2 of 3 repeats. The user's ear decides."""
import json, random, re, shutil, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROMPT = """You are a sound editor checking one narration clip before it goes into a short academic research film (white, calm,
explanatory; the audience is researchers). Listen to the whole attached clip. The script it should read is:

"{text}"

Judge only what you hear. Be strict: 10 means a skilled human narrator reading naturally; 5 means clearly synthetic but usable.
Reply with JSON only:
{{"first_six_words": "...",
 "naturalness": 1-10,
 "clarity": 1-10,
 "fits_academic_film": 1-10,
 "pace": "slow" | "right" | "fast",
 "human_or_ai": "human" | "ai",
 "defects": [{{"time_s": number, "what": "concrete defect: mispronounced word, extra or missing sound, glitch, odd pause, wrong stress, creaky or sinking ending"}}],
 "one_line": "the main impression in one sentence"}}"""

mode, B = sys.argv[1], Path(sys.argv[2]); OUT = B / "out"
if mode == "prepare":
    (B / "clips").mkdir(parents=True, exist_ok=True); key = {}; names = random.sample(range(100, 999), len(sys.argv) - 3)
    for n, spec in zip(names, sys.argv[3:]):
        label, rest = spec.split("=", 1); clip, script = rest.rsplit(":", 1)
        shutil.copy(clip, B / "clips" / f"clip_{n}.wav"); key[f"clip_{n}.wav"] = {"label": label, "text": Path(script).read_text().strip()}
    (B / "key.json").write_text(json.dumps(key, indent=1)); print("prepared", len(key), "clips; key.json stays local, it is never sent")
elif mode == "single":
    OUT.mkdir(exist_ok=True); KEY = json.load(open(B / "key.json"))

    def call(name, prompt, clip):
        f = OUT / (name + ".txt")
        if f.exists() and f.stat().st_size > 20: return name, "cached"
        r = subprocess.run(["bash", str(HERE / "agy_call_media.sh"), "--attach", str(B / "clips" / clip)], input=prompt,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if r.returncode == 0: f.write_text(r.stdout)
        return name, r.returncode or "ok"
    jobs = [(f"single_{c[:-4]}_{rep}", PROMPT.format(text=k["text"]), c) for rep in range(int(sys.argv[3])) for c, k in KEY.items()]
    with ThreadPoolExecutor(4) as ex:
        for name, st in ex.map(lambda j: call(*j), jobs): print(name, st, flush=True)
else:
    KEY = json.load(open(B / "key.json")); by = {}
    for c, k in KEY.items():
        for f in sorted(OUT.glob(f"single_{c[:-4]}_*.txt")):
            m = re.search(r"\{.*\}", f.read_text(), re.S)
            try: by.setdefault(k["label"], []).append(json.loads(m.group(0)))
            except Exception: print("unreadable reply:", f.name)
    for label, rs in by.items():
        print(f"\n{label}: naturalness {[r.get('naturalness') for r in rs]} clarity {[r.get('clarity') for r in rs]} pace {[r.get('pace') for r in rs]}")
        for r in rs:
            for d in r.get("defects", []): print("   ", d.get("time_s"), "s:", d.get("what"))
