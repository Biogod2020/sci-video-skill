"""Remove the usual faults from TTS narration audio (clicks at clip starts, noise bursts at take ends, long silences).
  clean_takes.py take IN.wav OUT.wav     a whole TTS take: drop isolated bursts before/after the speech, keep 150 ms around it
  clean_takes.py clips DIR               every line_*.wav in DIR, in place: drop isolated bursts, keep 60 ms before and
                                     120 ms after the speech, 10 ms fade in and out; prints what is left to look at
A burst = a loud stretch of sound (within 20 dB of speech level) shorter than 90 ms that is separated from the rest of the speech by >= 120 ms of silence."""
import sys, glob, os
import numpy as np, soundfile as sf

HOP = 0.005


def env(x, sr):
    n = int(sr * HOP); k = len(x) // n
    return np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(1) + 1e-12)


def runs(mask):
    d = np.diff(np.r_[0, mask.astype(int), 0]); return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def clean(x, sr, pre, post):
    e = env(x, sr); lvl = np.percentile(e, 95); on = e > lvl * 10 ** (-38 / 20)
    R = runs(on); merged = []
    for a, b in R:                                    # join stretches less than 120 ms apart
        if merged and a - merged[-1][1] < 0.12 / HOP: merged[-1][1] = b
        else: merged.append([a, b])
    n = int(sr * HOP); dropped = []
    loud = lambda a, b: (b - a) * HOP < 0.09 and e[a:b].max() > lvl * 0.1     # quiet short sounds are breaths or soft consonants: keep
    keep = [m for m in merged if not loud(*m)]
    for a, b in merged:
        if loud(a, b):
            x[max(0, a * n - n):b * n + n] = 0; dropped.append((round(a * HOP, 2), round((b - a) * HOP, 3), round(float(e[a:b].max() / lvl), 2)))
    if not keep: return x, dropped, []
    s, t = max(0, keep[0][0] * n - int(pre * sr)), min(len(x), keep[-1][1] * n + int(post * sr))
    y = x[s:t].copy(); f = int(0.010 * sr); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    gaps = [(round((keep[i][1] * n - s) / sr, 2), round((keep[i + 1][0] - keep[i][1]) * HOP, 2)) for i in range(len(keep) - 1) if (keep[i + 1][0] - keep[i][1]) * HOP > 0.7]
    return y, dropped, gaps


if sys.argv[1] == "take":
    x, sr = sf.read(sys.argv[2], dtype="float64"); y, d, g = clean(x, sr, 0.15, 0.15); sf.write(sys.argv[3], y, sr, subtype="PCM_16")
    print(os.path.basename(sys.argv[2]), "%.2f -> %.2f s" % (len(x) / sr, len(y) / sr), "bursts removed (at s, len, rel level):", d, "| pauses > 0.7 s (at, len):", g)
else:
    for f in sorted(glob.glob(os.path.join(sys.argv[2], "line_*.wav"))):
        x, sr = sf.read(f, dtype="float64"); y, d, g = clean(x, sr, 0.06, 0.12); sf.write(f, y, sr, subtype="PCM_16")
        h, t = np.abs(y[:int(.005 * sr)]).max(), np.abs(y[-int(.005 * sr):]).max()
        flag = " <-- CHECK" if d or g or h > 0.01 or t > 0.01 else ""
        print("%-18s %5.2f -> %5.2f s  head %.4f tail %.4f  bursts %s  pauses %s%s" % (os.path.basename(f), len(x) / sr, len(y) / sr, h, t, d, g, flag))
