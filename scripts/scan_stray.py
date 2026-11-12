"""Find stray sounds that speech recognition does not report: a click, a doubled "s", a leftover syllable, a noise burst.
  scan_stray.py DIR_OR_WAV...        (every *.wav in a folder; nothing is changed)
A word check (ASR) passes a clip that says the right words plus an extra hiss, so run this on every split line as well.
Flags, per clip:
  HEAD  a short sound (< 180 ms) at the start that is separated from the speech by >= 70 ms of silence
  TAIL  the same at the end
  EDGE  the clip does not start or end in silence (it will click when placed on the timeline)
  PAUSE a silence longer than 0.7 s inside the clip
"hiss" marks a sound whose energy sits above 4 kHz (s, t, ts), the usual leftover of a cut made inside a word boundary.
Listen to every flagged clip around the printed time before deciding; soft breaths can be flagged too."""
import glob, os, sys
import numpy as np, soundfile as sf

HOP = 0.005


def runs(mask):
    d = np.diff(np.r_[0, mask.astype(int), 0]); return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def scan(f):
    x, sr = sf.read(f, dtype="float64", always_2d=True); x = x.mean(1); n = int(sr * HOP); k = len(x) // n
    if k < 20: return ["too short"]
    fr = x[:k * n].reshape(k, n); e = np.sqrt((fr ** 2).mean(1) + 1e-12); lvl = np.percentile(e, 95)
    R = [list(r) for r in runs(e > lvl * 10 ** (-36 / 20))]
    merged = []
    for a, b in R:                                   # join stretches less than 70 ms apart
        if merged and a - merged[-1][1] < 0.07 / HOP: merged[-1][1] = b
        else: merged.append([a, b])
    def hiss(a, b):
        seg = x[a * n:b * n]; sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2; fq = np.fft.rfftfreq(len(seg), 1 / sr)
        return sp[fq > 4000].sum() / (sp.sum() + 1e-20) > 0.5
    out = []
    if len(merged) > 1:
        for tag, (a, b) in (("HEAD", merged[0]), ("TAIL", merged[-1])):
            if (b - a) * HOP < 0.18 and e[a:b].max() > lvl * 0.06:
                out.append("%s %.0f ms sound at %.2f s%s" % (tag, (b - a) * HOP * 1000, a * HOP, " (hiss)" if hiss(a, b) else ""))
    h, t = np.abs(x[:int(.005 * sr)]).max(), np.abs(x[-int(.005 * sr):]).max()
    if max(h, t) > 0.01: out.append("EDGE head %.3f tail %.3f" % (h, t))
    for (a, b), (c, d) in zip(merged, merged[1:]):
        if (c - b) * HOP > 0.7: out.append("PAUSE %.2f s at %.2f s" % ((c - b) * HOP, b * HOP))
    return out


files = sum((sorted(glob.glob(os.path.join(p, "*.wav"))) if os.path.isdir(p) else [p] for p in sys.argv[1:]), [])
bad = 0
for f in files:
    r = scan(f)
    if r: bad += 1; print(os.path.basename(f), "|", "; ".join(r))
print("%d of %d clips flagged" % (bad, len(files)))
