"""A plain rhythm bed to sit under narration (no melody, no samples: everything is synthesized here).
  rhythm.py OUT.wav SECONDS [BPM]
Soft kick on beats 1 and 3, a muted wood click on 2 and 4, very quiet shaker on the off-beats; 3 s fade in, 5 s fade out."""
import sys
import numpy as np, soundfile as sf

out, dur = sys.argv[1], float(sys.argv[2]); bpm = float(sys.argv[3]) if len(sys.argv) > 3 else 84
sr = 48000; n = int(dur * sr); y = np.zeros(n + sr); beat = 60 / bpm; rng = np.random.default_rng(3)


def add(t, x, g):
    i = int(t * sr); y[i:i + len(x)] += g * x[:max(0, len(y) - i)]


def kick():
    t = np.arange(int(.32 * sr)) / sr; f = 46 + 60 * np.exp(-t / .035)
    return np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t / .11) * np.minimum(1, t / .004)


def click():
    t = np.arange(int(.09 * sr)) / sr
    return (np.sin(2 * np.pi * 820 * t) + .5 * np.sin(2 * np.pi * 1240 * t)) * np.exp(-t / .018) * np.minimum(1, t / .002)


def shaker():
    t = np.arange(int(.06 * sr)) / sr; x = rng.standard_normal(len(t)); x = np.diff(x, prepend=0)   # high-passed noise
    return x * np.exp(-t / .014) * np.minimum(1, t / .003)


K, C = kick(), click(); b = 0
while b * beat < dur:
    t = b * beat
    if b % 4 in (0, 2): add(t, K, 1.0 if b % 4 == 0 else .8)
    if b % 4 in (1, 3): add(t, C, .32)
    add(t + beat / 2, shaker(), .05 if b % 2 else .035)
    b += 1
y = y[:n]; t = np.arange(n) / sr
y *= np.clip(t / 3, 0, 1) * np.clip((dur - t) / 5, 0, 1)
y *= 0.5 / np.abs(y).max()
sf.write(out, np.stack([y, y], 1), sr, subtype="PCM_16")
print(out, round(dur, 2), "s", bpm, "bpm")
