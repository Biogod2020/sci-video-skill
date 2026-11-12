# Defects that were caught late, and how to catch each one first

Every row cost at least one extra round in the source project. "Check" is something you can run or look at before the
user sees the cut.

## Story and captions

| Defect | Root cause | Prevent | Check |
| --- | --- | --- | --- |
| Unexplained term or internal label on screen | Script written from the author's view | Gloss at first use | Cold-reader review lists every unknown term; grep captions for labels used in the code or the paper's tables |
| Abstract sentence nobody can picture | Summarizing instead of showing | One concrete pair or record per claim | Ask of each line: could a frame show this? If not, rewrite |
| Number before its meaning | Front-loading results | Introduce the thing, then count it | Read captions in order: is each number's unit already defined? |
| Number that does not match the source | Copied from memory or an older run | Keep a `facts` note: number → file and line | Re-read each number in the log or table before the final cut |
| Method detail that raises "why / how computed" | Completeness instinct | One clause of explanation, or cut | Human-listener review flags sentences that invite an unanswered question |
| Caption explains the drawing, not the point | Writing captions from the picture | Write captions from the story; legend separately | Read captions alone, without the picture: do they tell the story? |
| Film starts or ends abruptly | No cover, no close | Cover with the name; closing hold | Look at t = 0 and the last 3 s |
| Mechanical narration | Feature list; lines voiced separately | Storyteller persona; paragraph takes | Human-listener review; listen to a middle paragraph, not only the opening |

## Picture

| Defect | Root cause | Prevent | Check |
| --- | --- | --- | --- |
| Looks like slides | Framed panels, titles, cuts | One world, camera moves | Contact sheet: do neighbouring stills share objects? Any frame with a title bar? |
| Too flashy | Glow, particles, speed for effect | Each motion stands for an operation | For each effect: what does it explain? No answer → remove |
| Schematic placeholders | Drawing the idea instead of the data | Real inputs/outputs chosen by a rule | Every picture and record on screen exists in the project files |
| Text overlap, cut-off, leftovers of the previous scene | Scenes tuned alone | Fade windows per object | Still at every caption time, and 0.2 s after every scene change |
| First frames in a fallback font | Fonts not loaded before frame 0 | Reference fonts in the page; wait for `document.fonts.ready` | Compare the still at t = 0 with one at t = 1 |
| Render takes far too long | One browser, serial frames | `render.mjs frames 30 8` | Time 100 frames first |
| Full re-render for a small audio fix | Clip length changed → plan shifted | Pad the fixed clip to its old length | `plan.json` duration identical before and after |
| Caption gone before it can be read | Slot shorter than the speech | `vo_plan.py` stretches the slot | `plan.json`: every `slot` ≥ `voice_sec` + gap |

## Sound

| Defect | Root cause | Prevent | Check |
| --- | --- | --- | --- |
| Click at the very start, noise burst at the end of a take | API returned a whole WAV (header + provenance chunk) and it was written as samples | `tts.py` keeps only the data chunk | `clean_takes.py take` prints removed bursts; `scan_stray.py` EDGE flag |
| Doubled "s" / leftover syllable at a join | Extra sound in the raw take, or a cut inside a word boundary | Cut at the last silence before the next line | `scan_stray.py` HEAD/TAIL (hiss) on every clip; listen to flagged ones |
| Word in the wrong clip | Cut at the longest silence, which was a pause inside a line | `split_lines.py` rule + per-piece transcription | WER per piece printed; read every CHECK line |
| Long dead pause inside a line | TTS hesitation | Re-take that paragraph, or shorten the silence | `clean_takes.py` and `scan_stray.py` PAUSE flag (> 0.7 s) |
| Pace and loudness drift | Whole script in one take | Paragraph takes; per-paragraph gain | Words per 30 s at the start vs the end; loudness per paragraph |
| Acronym read as a word, letter read oddly | No pronunciation note | `--say "'GEO' is spoken as the letters G, E, O"`; write the spoken form in `story.py` | Transcript shows it only sometimes: listen to each acronym once, or ask the user to |
| Voice masked by the bed | Music, or rhythm too loud | No music; rhythm ≈ 10 dB under, limited together | Listen to the densest sentence; deliver voice-only as well |
| Sinking, creaky sentence endings | Voice habit | Style prompt asks for endings that land gently | Listener review per paragraph |
| Unnatural join between paragraphs | Different energy between takes | Same style prompt; gain match; 0.45 s gap | Listen to each paragraph boundary |

## Process

| Defect | Root cause | Prevent |
| --- | --- | --- |
| Rendering before the story is agreed | Eagerness to show motion | Gates: script review → storyboard stills → then render |
| Fixing only the instance the user named | Reading feedback literally | Search the whole film for the pattern |
| Trusting an AI judge's ranking | Position bias, score noise | Use judges for concrete defects; the user chooses voices by ear |
| Reporting a claim that was not checked | Speed/number taken from memory | Check logs first; say plainly what was not verified |
| Guessing at wording for several rounds | No outside view | Ask the reviewer for three rewrites, offer the choice |

## Final checklist

Run all of it; tick nothing from memory.

- [ ] `python3 story.py` rerun after the last script edit; captions on screen equal the script.
- [ ] Stills at every caption start (+0.5 s) looked at on contact sheets.
- [ ] Still at t = 0 (cover, fonts right) and at the last frame.
- [ ] Every line's transcript read against its text (numbers and names especially).
- [ ] `scan_stray.py` on the split folder: 0 flagged, or each flag listened to.
- [ ] Each acronym and each number heard once in the final mix.
- [ ] `plan.json`: no negative gaps, nothing sped up; film duration equals audio duration (ffprobe).
- [ ] Voice −17 LUFS; rhythm version and voice-only version both produced.
- [ ] Every number in captions matched to its source file today.
- [ ] Every term explained at first use (list them and point to the line that explains each).
- [ ] No keys, private paths or private recordings in anything sent to a reviewer or published.
- [ ] Review page updated: current version, length, change list; link given to the user.
