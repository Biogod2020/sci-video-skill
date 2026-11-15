"""Lay the split narration lines on the film's clock and write the picture's time warp.
  vo_plan.py LINES_JSON SPLIT_DIR OUT_DIR --end PICTURE_SECONDS
LINES_JSON = [{"id": "a1", "para": "P1", "at": 3.2, "text": "...", "until": 5.9}]: `at` is the second ON THE PICTURE'S OWN CLOCK
(the clock the animation was written on) at which the line's caption appears; SPLIT_DIR holds line_<id>_0.wav.
Optional `until`: a picture time inside the line's slot that the picture may not pass before the line has been spoken
(+0.25 s); after it the picture plays at normal speed. Use it wherever the scene starts to leave (fold away, camera move,
result fades) before the next caption: without it the extra time is spread over the whole slot, so the scene leaves
while the narrator is still talking about it.
Each line starts LEAD s after its caption appears. A caption's slot keeps its picture length unless the spoken line plus
GAP s is longer; then the slot (and the picture under it) is stretched. Nothing is ever sped up: speech that is too
long makes the film longer, it does not make the voice faster.
Lines of one paragraph came from one take, so each paragraph is brought to the same speech level by gain alone.
Writes OUT_DIR/vo_warp.js (window.VO_WARP = [[film time, picture time], ...]; window.VO_LINES = [[start, end, id], ...]),
voice.wav (48 kHz mono) and plan.json. If plan.json's duration is unchanged after an audio fix, the picture need not be rendered again."""
import argparse, json
from pathlib import Path
import numpy as np, soundfile as sf, scipy.signal as ss

ap = argparse.ArgumentParser(); ap.add_argument("lines"); ap.add_argument("split"); ap.add_argument("out")
ap.add_argument("--end", type=float, required=True, help="length of the picture on its own clock")
ap.add_argument("--gap", type=float, default=0.45, help="silence kept after a line before the next caption")
ap.add_argument("--lead", type=float, default=0.12, help="caption appears this long before its line is spoken")
a = ap.parse_args()
lines = json.load(open(a.lines)); S, O = Path(a.split), Path(a.out); SR = 48000; O.mkdir(parents=True, exist_ok=True)


def load(i):
    y, sr = sf.read(S / f"line_{i}_0.wav", always_2d=True); y = y.mean(1)
    return ss.resample_poly(y, SR, sr) if sr != SR else y


def level(x):          # RMS of the frames that hold speech
    f = x[:len(x) // 960 * 960].reshape(-1, 960); r = np.sqrt((f ** 2).mean(1)); return np.sqrt((r[r > r.max() * 0.05] ** 2).mean())


raw = {ln["id"]: load(ln["id"]) for ln in lines}; clip = {}
for p in sorted({ln.get("para", "") for ln in lines}):
    ids = [ln["id"] for ln in lines if ln.get("para", "") == p]; gain = 0.08 / level(np.concatenate([raw[i] for i in ids]))
    for i in ids: clip[i] = raw[i] * gain
s = [float(ln["at"]) for ln in lines] + [a.end]
assert all(y > x for x, y in zip(s, s[1:])), "caption times must increase and end before --end"
dur = [len(clip[ln["id"]]) / SR for ln in lines]
HOLD = 0.25
n, extra = [s[0]], []
for i, ln in enumerate(lines):
    if "until" in ln:
        u = float(ln["until"]); assert s[i] < u < s[i + 1], ln["id"] + ": until must lie inside the line's slot"
        first = max(u - s[i], a.lead + dur[i] + HOLD); extra.append([n[-1] + first, u])
        n.append(n[-1] + max(first + (s[i + 1] - u), dur[i] + a.gap + a.lead))
    else:
        n.append(n[-1] + max(s[i + 1] - s[i], dur[i] + a.gap + a.lead))
warp = sorted([[0, 0]] + [[round(x, 3), round(y, 3)] for x, y in zip(n, s)] + [[round(x, 3), round(y, 3)] for x, y in extra])
voice = np.zeros(int(n[-1] * SR) + SR)
for i, ln in enumerate(lines):
    c = clip[ln["id"]]; k = int((n[i] + a.lead) * SR); voice[k:k + len(c)] += c
voice = voice[:int(n[-1] * SR)]
voice *= 10 ** (-3 / 20) / np.abs(voice).max()          # gain only, no limiter
sf.write(O / "voice.wav", voice, SR, subtype="PCM_16")
(O / "vo_warp.js").write_text("window.VO_WARP = " + json.dumps(warp) + ";\nwindow.VO_LINES = " +
                              json.dumps([[round(n[i], 2), round(n[i + 1] - 0.15, 2), ln["id"]] for i, ln in enumerate(lines)]) + ";\n")
plan = [{"id": ln["id"], "text": ln["text"], "picture_start": round(s[i], 2), "start": round(n[i], 2), "voice_sec": round(dur[i], 2),
         "slot_picture": round(s[i + 1] - s[i], 2), "slot": round(n[i + 1] - n[i], 2)} for i, ln in enumerate(lines)]
(O / "plan.json").write_text(json.dumps({"duration": round(n[-1], 3), "lines": plan}, indent=1))
st = sum(p["slot"] > p["slot_picture"] + 1e-6 for p in plan)
print("duration", round(n[-1], 2), "s; stretched slots", st, "of", len(plan), "; speech", round(sum(dur), 1), "s")
for p in plan: print(p["id"], p["start"], p["voice_sec"], p["slot_picture"], "->", p["slot"])
