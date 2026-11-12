"""Cut ONE paragraph take into the script's lines, and check every piece by transcribing it again.
  split_lines.py TAKE.wav PARA.json OUT_DIR [--model small.en]
PARA.json = [{"id": "a1", "text": "..."}, ...] in spoken order -> OUT_DIR/line_<id>_0.wav + OUT_DIR/split_<take>.json
1. faster-whisper word times are matched (edit distance) to the script words, so each line's last and first word have a time.
2. Each boundary is cut in the middle of the LAST silence (>= 60 ms) before the next line's first word. The longest
   silence is not used: it can be a pause inside a line, which would move a word into the wrong clip.
3. Each piece is transcribed again; a word error rate above 0.15 is printed with CHECK (read the printed transcript: the
   recogniser writing "300,000" for "three hundred thousand" also counts as errors). Then run scan_stray.py:
   the word check cannot hear a doubled "s" or a click.
Needs faster-whisper, soundfile, numpy, scipy."""
import argparse, json, re
from pathlib import Path
import numpy as np, soundfile as sf, scipy.signal as ss
from faster_whisper import WhisperModel

NUM = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"}


def norm(s):
    return re.findall(r"[a-z0-9']+", s.lower().replace("-", " ").replace(",", ""))


def align(hyp, ref):
    """Edit-distance alignment; returns {ref index: hyp index} for matched or substituted words."""
    n, m = len(hyp), len(ref); d = np.zeros((n + 1, m + 1), int); d[:, 0] = range(n + 1); d[0, :] = range(m + 1)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (hyp[i - 1] != ref[j - 1]))
    mp, i, j = {}, n, m
    while i > 0 and j > 0:
        if d[i, j] == d[i - 1, j - 1] + (hyp[i - 1] != ref[j - 1]): mp[j - 1] = i - 1; i -= 1; j -= 1
        elif d[i, j] == d[i - 1, j] + 1: i -= 1
        else: j -= 1
    return mp


def wer(ref, hyp):
    r, h = norm(ref), norm(hyp); mp = align(h, r)
    return 1 - sum(h[v] == r[k] for k, v in mp.items()) / max(1, len(r))


ap = argparse.ArgumentParser(); ap.add_argument("take"); ap.add_argument("para"); ap.add_argument("out"); ap.add_argument("--model", default="small.en")
a = ap.parse_args()
lines = json.load(open(a.para)); O = Path(a.out); O.mkdir(parents=True, exist_ok=True)
y, sr = sf.read(a.take, always_2d=True); y = y.mean(1); y16 = ss.resample_poly(y, 16000, sr).astype("float32")
asr = WhisperModel(a.model, device="cpu", compute_type="int8")
rec = lambda x: " ".join(s.text for s in asr.transcribe(x, language="en", beam_size=5)[0])
segs, _ = asr.transcribe(y16, language="en", beam_size=5, word_timestamps=True)
words, starts, ends = [], [], []
for s in segs:
    for w in s.words:
        for p in norm(w.word): words.append(p); starts.append(w.start); ends.append(w.end)
ref, owner = [], []
for li, ln in enumerate(lines):
    for w in norm(ln["text"]): ref.append(w); owner.append(li)
mp = align(words, ref); first, last = {}, {}
for ri, li in enumerate(owner):
    if ri in mp: first.setdefault(li, starts[mp[ri]]); last[li] = ends[mp[ri]]
hop = int(.02 * sr); rms = np.array([np.sqrt(np.mean(y[i:i + hop] ** 2) + 1e-12) for i in range(0, len(y) - hop, hop)])
q = rms < np.percentile(rms, 95) * 10 ** (-35 / 20)
cuts = [0.0]
for li in range(len(lines) - 1):
    lo = max(last.get(li, cuts[-1]) - 0.15, cuts[-1] + 0.2); hi = max(first.get(li + 1, lo + 1.0) + 0.1, lo + 0.1)
    ia, ib = int(lo / .02), min(int(hi / .02), len(q)); best, i = None, ib - 1
    while i >= ia:
        if q[i]:
            j = i
            while j >= ia and q[j]: j -= 1
            if (i - j) * .02 >= .06: best = (i + j + 1) // 2; break
            i = j
        i -= 1
    if best is None and ib > ia: best = ia + int(np.argmin(rms[ia:ib]))       # run-on read: the quietest frame instead
    cuts.append(best * .02 if best is not None else (lo + hi) / 2)
cuts.append(len(y) / sr)
rep = []
for li, ln in enumerate(lines):
    seg = y[int(cuts[li] * sr):int(cuts[li + 1] * sr)]
    nz = np.flatnonzero(np.abs(seg) > 10 ** (-40 / 20) * np.abs(seg).max())
    seg = seg[max(0, nz[0] - int(.08 * sr)): nz[-1] + int(.08 * sr)]
    sf.write(O / f"line_{ln['id']}_0.wav", seg, sr, subtype="PCM_16")
    h = rec(ss.resample_poly(seg, 16000, sr).astype("float32")).strip(); e = round(wer(ln["text"], h), 3)
    rep.append({"id": ln["id"], "sec": round(len(seg) / sr, 2), "wer": e, "asr": h})
    print(ln["id"], rep[-1]["sec"], "s wer", e, "CHECK" if e > 0.15 else "", "|", h, flush=True)
(O / f"split_{Path(a.take).stem}.json").write_text(json.dumps({"take": a.take, "cuts": [round(c, 3) for c in cuts], "lines": rep}, indent=1))
