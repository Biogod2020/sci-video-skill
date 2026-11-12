# sci-video-skill

A Claude Code skill for making a narrated explainer film about a research project: a paper, a dataset, a method or a tool.

The film is an HTML-canvas animation on a white background, shot as one continuous camera move, with a stock text-to-speech narrator, captions, and an optional quiet rhythm. It is rendered frame by frame with headless Chrome and encoded with ffmpeg.

The skill was written after making one such film through 13 versions. It records what the reviewer asked for each time and the defects that were found late, so that the next film needs fewer rounds.

## What is in it

| Path | Content |
| --- | --- |
| `SKILL.md` | The rules and the eight-step workflow, with a gate after each step |
| `references/preferences.md` | Each remark the reviewer made, what it meant, and the rule it became |
| `references/defects.md` | Each late defect, its cause, how to check for it, and a final checklist |
| `references/narration.md` | TTS chain, style prompt, a small voice comparison, and what an AI listener can and cannot judge |
| `references/film-page.md` | How the canvas film is structured and timed |
| `assets/template/` | A working 24-second film to copy and edit |
| `scripts/` | Rendering, contact sheets, TTS, cleaning, splitting, stray-sound scan, timing, mux, review page, blind listening check |

## Install

```bash
git clone https://github.com/Biogod2020/sci-video-skill ~/.claude/skills/sci-video-skill
```

Then ask Claude Code for a research video, for example: "make an explainer film for this project".

## Requirements

- `node` with `puppeteer`, and `ffmpeg`
- Python 3.8+ with `numpy scipy soundfile pillow httpx`; `faster-whisper` to split narration into lines; `aiohttp certifi` only for the OpenAI realtime engine
- An API key for Google (Gemini TTS) or OpenAI, kept in a file outside the repository: `~/.config/sci-video/google_key` or `~/.config/sci-video/openai_key`, or the variables `GOOGLE_API_KEY` / `OPENAI_API_KEY`
- Optional: the `agy` CLI for outside review by Gemini (`scripts/agy_call_media.sh`)

## Try the template

```bash
mkdir myfilm && cp ~/.claude/skills/sci-video-skill/assets/template/* myfilm/ && cd myfilm
S=~/.claude/skills/sci-video-skill/scripts
python3 story.py
node $S/render.mjs stills 2,7,13,17,22
python3 $S/sheet.py board 2,7,13,17,22
```

`stills/board_0.jpg` now shows five moments of the film. The full chain, with narration, is in `references/narration.md` and `references/film-page.md`.

## Notes

- No keys, voices or project data are stored in this repository.
- The voice comparison in `references/narration.md` was measured in November 2026 on one film. Check current models and prices before relying on it.
