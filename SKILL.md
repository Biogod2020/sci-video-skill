---
name: sci-video-skill
description: Make a narrated academic explainer film about a research project (a paper, a dataset, a method, a tool) as a deterministic HTML-canvas animation with stock-voice narration, rendered to MP4. Use this skill whenever the user asks for a research video, demo film, video abstract, project explainer, "科研视频", "学术展示视频", "给论文/项目做个视频", an animated walkthrough of a method or pipeline, or wants narration/TTS added to such a film, even if they only say "make a video of this project". Use it for academic and explanatory films; for a commercial product pitch film use a product-film skill such as ai-product-film instead (a separate skill, not part of this one).
---

# sci-video-skill

These are instructions for the assistant that runs the skill: "you" is the assistant, "the user" is the researcher
who asked for the film.

An academic explainer film: white background, one continuous moving shot, a narrator telling the story of the research,
captions that match the voice, and a quiet rhythm under it. The goal is that the first full cut is already close to
final. Almost every rework round in the film this skill was distilled from came from a small set of causes; they are
written here as rules with their reasons, and as checks that run before the user sees anything.

Read in this order:

1. This file: the rules and the workflow.
2. [references/preferences.md](references/preferences.md) before writing the story: what the user wants, in their own words.
3. [references/defects.md](references/defects.md) before showing any cut: the defects that were caught late, how to detect each one.
4. [references/narration.md](references/narration.md) when you reach the voice: models, prompts, cost, what an AI judge can and cannot hear.
5. [references/film-page.md](references/film-page.md) when you write the animation: how the canvas film is built and timed.

## What the film is (and is not)

| It is | It is not | Why |
| --- | --- | --- |
| An academic visualization: calm, clear, a little surprising | A commercial demo with effects and big music | "我们不是商业demo，是学术可视化展示" |
| Full of motion: things form, move, sort, connect | A stiff screen recording or a static figure | "不要那么生硬的demo，要充满动感的动画展示" |
| One world with one moving camera | Slides: a title, a framed panel, a cut, the next panel | "还是太像ppt/slides了" |
| White background, few colours, one accent | Dark, glowing, gradient-heavy | asked for directly; it reads as a paper figure in motion |
| A story told by one person | A list of features read by an announcer | "开头像是在讲故事了，但是后续还是有点机械" |
| Understandable by a researcher outside the subfield | Understandable only by the authors | "读者又不知道 classA 是什么" |

Lively but not flashy is the hard part. Motion must carry meaning (a dot moving into a group *is* the classification);
motion that only decorates gets removed in review.

## The story comes first

Fix the story before any drawing. The order that worked:

1. **Cover**: the project's name and one line saying what it is. A film that starts in the middle of an animation feels abrupt.
2. **Background**: what exists in the world, shown with one real example.
3. **The problem**: what is wrong with it, shown with real records (two labs writing the same thing differently), not stated abstractly.
4. **"So we built X"**: the turn of the story, said in those plain words.
5. **How it works**: each step on one real input, with the real output.
6. **What it is good for**: the result and why it matters next (training, scale, reuse).
7. **Close**: the name again, where to find it.

Rules for every sentence of narration (each one caused a rework round when it was broken):

- **Every term is explained when it first appears**, in a few words, or it is replaced. Internal labels (class A, stage 2, v3) never reach the screen.
- **An abstract sentence becomes a concrete example.** "Metadata is heterogeneous" → "one lab writes ‘Sex: F’, another writes ‘gender: female’".
- **A number appears only when the story has earned it.** Do not announce totals before the viewer knows what is being counted. Every number on screen must be traceable to a log or a table; check it there, do not copy it from memory.
- **No detail whose meaning or origin the viewer cannot see.** "18 yes/no questions" or "a probability of 0.83" raises "why 18? how computed?". Either explain it in one clause or leave it out. Training details stay out.
- **Captions carry the story, not the drawing.** "Each dot is ten datasets" explains the picture; the caption should say what the viewer should take away.
- **The user's wording wins.** When they name something ("a fast decision model"), use exactly that everywhere.
- **Pace: slow enough to read every caption once, aloud.** Length is not capped; 4-5 minutes is fine if every part is needed.

Write the script in `story.py` (template in `assets/template/`): one row per line with its caption, its spoken form and
its time. It is the only place where narration, captions and timing live; everything else is generated from it. A
caption and its spoken form can differ ("‘Sex: F’" on screen, "sex, F" spoken).

Then send the whole script out for review before anything is rendered or voiced (see "Outside review" below). Fixing a
sentence costs nothing now and a full re-voice and re-render later.

## Workflow

Set up a film folder by copying `assets/template/` into it. Scripts live in this skill's `scripts/`; run them from the
film folder. They need `node` with `puppeteer`, `ffmpeg`, and Python with `numpy scipy soundfile pillow httpx`
(`faster-whisper` for splitting; `aiohttp certifi` only for the realtime engine).

| Step | Do | Gate before moving on |
| --- | --- | --- |
| 1. Material | Read the paper / repo / logs. Collect real examples: real inputs, real records, real model outputs. Note where every number comes from. | Every claim has a source file. |
| 2. Story | Write the script in `story.py`; `python3 story.py`. | Gemini judge + cold reader + human-listener pass done; the user has read the script (short, in their language, with the English lines). |
| 3. Picture | Write the world, camera path and scenes (`film_core.js` + scene files). `node render.mjs stills t1,t2,...` then `sheet.py`. | You have looked at a still for every caption. Storyboard sheets reviewed by Gemini and shown to the user **before** any full render. |
| 4. Voice samples | 3-4 stock voices reading the same first paragraph (`tts.py`), equal loudness, on the review page. | The user picked one by ear. Never clone a voice. |
| 5. Narration | One TTS call per paragraph → `clean_takes.py take` → `split_lines.py` → `clean_takes.py clips` → `scan_stray.py`. | Every line transcribes to its text; no clip is flagged, or each flag was listened to and fixed. |
| 6. Timing | `vo_plan.py` lays the lines on the clock and stretches the picture where speech is longer. | Stills re-checked at the new times of a few lines; nothing sped up. |
| 7. Render | `node render.mjs frames 30 8` (30 fps, 8 parallel Chrome workers), then `mux.sh` (voice only, and voice + rhythm). | Durations of picture and sound match; final checklist in `references/defects.md` passed. |
| 8. Review | Write `REVIEW.json` (videos, scenes, change list; format in the script's header), run `review_server.py REVIEW.json`, give the user the link. | `review_feedback.json` (saved by the page when the user presses Save) read; every comment answered. |

Steps 2-4 are where one-pass quality is decided. Do not skip a gate to save time: every skipped gate in the source
project came back as a full re-render.

### Picture rules

- `renderAt(t)`, the function in `film_core.js` that draws the frame for time `t`, alone decides the frame: no timers, no `Math.random()` without a seed, no CSS animation. This is what
  lets frames render in parallel (one Chrome per worker, so 8 workers is close to 8× faster) and lets an
  audio-only fix skip the re-render.
- One world, larger than the screen. Objects persist; the camera travels between them. No panel frames, no slide titles,
  no hard cuts. A scene change is a camera move or a transformation of what is already there.
- Show the experiment's design on **one real input**: the real image, the real record, the real answer the model gave.
  Choose examples by a rule you can state ("the first sample of the largest study"), not the prettiest one.
- White `#fff`, near-black text, grey for context, one accent colour for "the thing we are talking about now",
  red/green only for wrong/right. Load fonts in the page before the first frame.
- Text on screen is large (captions ≈ 40 px at 1080p) and stays long enough to be read once aloud.
- Keep an "agent at work" or "data flowing" element only when it shows what really happens, with real content in it.

### Sound rules

- **Stock TTS voice, never a clone**, even if a reference recording of the user exists.
- **One call per paragraph.** A whole-script take drifts (measured: 75 → 101 words per 30 s, +3 dB by the end); one call
  per line loses the melody between sentences and sounds mechanical. A paragraph is 3-5 lines of one thought.
- **Never speed speech up to fit the picture.** `vo_plan.py` lengthens the picture instead.
- **No music.** A plain synthesized rhythm about 10 dB under the voice (`rhythm.py`) is the most the user accepted;
  always deliver a voice-only version beside it.
- **Check sound with more than a transcript.** Speech recognition passes a clip that has the right words plus a click or
  a doubled "s". Run `scan_stray.py`, and listen to the joins between paragraphs yourself if you can attach audio to a
  reviewer.
- **When an audio fix changes a clip's length, pad it back to the old length** so `plan.json` (the timing file written by `vo_plan.py`) stays identical and only the
  sound is muxed again.
- Keep spending small: voice samples on one paragraph only; rerun only the paragraphs that changed (`tts.py` skips
  files that exist).

### Outside review (Gemini through agy)

Use `scripts/agy_call_media.sh` (one round, no tools, attachments allowed) or the gemini-humanize-skill if installed.
Everything the reviewer needs must be in the one message. Remove keys and personal information first.

- **Script, before voicing**: (a) a *judge* (an editor of science films: is the story order right, where does it drag);
  (b) a *cold reader* from a neighbouring field (retell it, then list where you got lost and every term you did not
  know); (c) a *human listener* (which sentences sound written by an AI or by a committee; which would a person never
  say aloud).
- **Storyboard sheets, before rendering**: attach the contact sheets; ask what each frame is trying to say and where it
  looks like a slide.
- **Narration, after splitting**: one clip per call, for concrete defects only (see `references/narration.md`).

Check every remark yourself before acting. The reviewer invents facts and numbers, and it cannot rank voices. When the
user says a sentence "still feels odd", ask the reviewer for three rewrites and offer them; do not keep guessing.

### Showing the user

- Reply in the user's language, conclusion first, short. Say what changed, what was verified and how, and what was not.
- Review happens on the review page (videos with tabs, per-scene pass/fix + comment, audio samples to choose from, a
  "what changed" list), not through file paths in chat.
- **When the user flags one problem, search the whole film for the same pattern** and fix all of them in the same round
  (one unexplained term → check every term; one click → scan every clip).
- Verify speed and number claims against logs before they go into the film or into your report.

## Before you say "done"

Run the final checklist at the end of [references/defects.md](references/defects.md). The short form:

1. Stills at every caption time read correctly (no overlap, no cut-off text, nothing left over from the previous scene).
2. Every line: transcript matches; `scan_stray.py` clean; no pause over 0.7 s inside a line.
3. First and last second: starts on the cover in silence, no click; ends without a cut-off word.
4. Picture and sound durations equal; voice at −17 LUFS; rhythm does not mask any word.
5. Every number and name in captions matches the source; every term is explained at first use.
6. Both versions (voice only, voice + rhythm) are on the review page with the change list.
