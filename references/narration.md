# Narration: voices, prompts, cost, and what an AI judge can hear

## The chain

```bash
python3 story.py                                             # build/paras.json, build/para_P*.json, build/lines.json
python3 $S/tts.py gemini build/takes build/paras.json --voices Sulafat --say "'GEO' is spoken as the letters G, E, O."
for p in P1 P2 P3; do
  python3 $S/clean_takes.py take build/takes/${p}_Sulafat_t0.wav build/clean/$p.wav
  python3 $S/split_lines.py build/clean/$p.wav build/para_$p.json build/split
done
python3 $S/clean_takes.py clips build/split                  # trim, fade, drop isolated bursts; prints CHECK lines
python3 $S/scan_stray.py build/split                         # stray hiss / click / pause that a transcript cannot show
python3 $S/vo_plan.py build/lines.json build/split build --end 150
```

`$S` is this skill's `scripts/` folder. Keys are read from a file (`TTS_KEYFILE`, or `~/.config/sci-video/google_key`
/ `openai_key`) or from `GOOGLE_API_KEY` / `OPENAI_API_KEY`. Never print a key, never put one in a script, a prompt or
a repository; error bodies are masked by the scripts.

## Style prompt

The default style in `tts.py` is the one that produced the accepted narration:

> A scientist narrating a short film about their own research to colleagues. Warm, clear and conversational, as if
> explaining it to a friend across a table: natural melody inside sentences, small pauses between sentences, a slightly
> longer pause after a result. Unhurried, about 150 words per minute. Never announcer-like, never salesy, never
> dramatic. Sentence endings land gently and do not sink into a low creaky voice.

For Gemini TTS the prompt has three parts (`# AUDIO PROFILE`, `## DIRECTOR'S NOTES` with pronunciation,
`## TRANSCRIPT`); for OpenAI the style goes in the system message or `instructions` together with "read EXACTLY as
written". Pronunciation notes (`--say`) are needed for every acronym, letter name and unusual term. Where the written
form reads badly aloud, give a spoken form in `story.py` ("sex, F" for "‘Sex: F’").

## Which voice (measured November 2026, one 4.8-minute English film)

| System | Voice | Blind naturalness (3 repeats × 2 paragraphs) | Cost for the film | Notes |
| --- | --- | --- | --- | --- |
| gemini-3.8-flash-tts | Sulafat | 7.3 | not measured (low) | Chosen by the user by ear. Judge noted occasional sinking endings. |
| gpt-audio-1.5 | cedar | 6.8 | ≈ $0.33 | Close second. |
| gpt-realtime-2.1 | cedar | 6.5 | ≈ $0.33 | Judge heard a swallowed "t" in "Agent" in 2 of 3 repeats. Needs the websocket API (`tts_realtime.py`). |
| gpt-realtime-2.1 | marin | 6.0 | ≈ $0.33 | Judge heard "gene activity" as "G activity" in 3 of 3 repeats. |
| gpt-audio-mini, gpt-4o-mini-tts | cedar | not blind-tested | cheaper | Usable for drafts. |

The differences are inside the judge's noise (see below), so this table is a starting point, not a ranking. Models and
prices change quickly: check the current model list and price before a new film, then run the same small comparison on
the film's first paragraph and let the user choose by ear.

All systems read an isolated letter ("F") unnaturally. Avoid single letters in the spoken form where possible.

## One take per what?

| Unit of one TTS call | Result |
| --- | --- |
| One line | Each sentence starts from zero: no melody across sentences, "mechanical". |
| One paragraph (3-5 lines, one thought) | Used. Natural flow, level and pace stay even, a bad line costs one small re-take. |
| Whole script (4-5 min) | Complete and fluent, but pace drifted from 75 to 101 words per 30 s and loudness rose 3 dB; some words recognized worse late in the take. |

## What an AI listener (Gemini with audio attached) can and cannot do

Measured with 36 blind calls:

- Scores for the **same clip** vary by 1-2 points between repeats. A 0.5-point difference between systems means nothing.
- With **two clips in one call** it chose the first-played clip in 10 of 12 comparisons. Pairwise judging is unusable.
- It rates every modern TTS as "ai" and tends to rate real human recordings **below** TTS.
- It **does** report concrete defects, with times: a mispronounced word, a swallowed consonant, an odd pause. Treat a
  defect reported in at least 2 of 3 repeats as worth listening to; a defect reported once usually does not repeat.
- It sometimes reports a defect that cannot be confirmed by measurement (an acronym "read as a word"). Then ask the
  user to listen at that time; do not re-take on the judge's word alone.

So: `blind_review.py prepare` (random clip names, loudness made equal first), `single` with 3 repeats, `report`; act
only on repeated concrete defects; the user's ear decides between voices.

## Fixing a clip without re-rendering

1. Edit the clip (cut the stray sound, 10 ms fades at the cut).
2. Pad the end with silence back to the clip's old length.
3. Rerun `vo_plan.py`; confirm `plan.json` is identical in duration and starts.
4. Rerun `mux.sh` only. The picture frames are reused.

Keep the original clips in a backup folder until the user has heard the fix.
