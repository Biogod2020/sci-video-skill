# What the user wants: preferences, in their own words

Collected from 13 versions of one film (a 4:48 explainer of a research database built by an AI agent). Each row is a
remark the user made after seeing a cut, what it meant, and the rule it became. Read this before writing a story;
apply it from the first draft so the same remarks are not needed again.

## Style

| The user said | What it meant | Rule |
| --- | --- | --- |
| 我不要那么生硬的demo，要充满动感的动画展示 | A recording of the tool with labels is not a film. | Animate the ideas: data forms, moves, sorts, connects. |
| 当前的特效+音乐太浮夸了，我希望学术+易懂 | The first animated cut overshot: glow, fast cuts, big music. | Motion must explain something. No effects for their own sake, no music. |
| 要灵动+惊艳，但是不要太浮夸 | Both at once: alive and restrained. | One or two "wow" moments that are also the clearest explanation (thousands of dots sorting themselves), the rest calm. |
| 我们不是商业demo，是学术可视化展示 | No pitch language, no product-launch look. | Paper-figure look in motion; plain claims; no slogans. |
| (asked for a pure white background) | Dark themes read as marketing. | `#fff`, near-black text, grey context, one accent. |
| 还是太像ppt/slides了 | Framed panels, titles and cuts feel like slides even when animated. | One world, one moving camera, objects persist, no panel frames, no slide titles. |
| (opening felt abrupt) | The film started inside an animation. | Open on a cover: project name + one line, then move into the world. |

## Story and wording

| The user said | What it meant | Rule |
| --- | --- | --- |
| 读者又不知道 classA 是什么 | Internal labels leaked into captions. | Explain every term at first use or replace it with plain words. |
| (asked for: background → problem → so we built X → how → what for) | The cut explained the pipeline but not why it exists. | Use that story order. The problem is shown with real, inconsistent records; the turn is "so we built …". |
| 我不太清楚你说每个 spot 是 10 个有什么意义 | The caption described the drawing's encoding. | Captions say what to take away; legends are small and optional. |
| 提前泄漏有多少个…有点问题 | A total appeared before the film had explained what was counted. | Numbers come when the story has earned them. |
| 18 个 yes or no question 有什么意义，以及概率是怎么算出来的 | A method detail with no visible meaning or derivation. | Explain in one clause or leave out. Never put training details in. |
| 这句话我没太懂 | An abstract sentence about inconsistent metadata. | Replace with an example: ‘Sex: F’ vs ‘gender: female’. |
| a fast language model 改成 a fast decision model … 其他的我接受 | The user has exact names for their things. | Their wording is used verbatim, everywhere it occurs. |
| 还是有点奇怪，你让 gemini 建议一下 | Repeated guessing at a sentence wastes rounds. | Ask the outside reviewer for alternatives and offer a choice. |
| (asked to explain selection with real records and real model answers) | Schematic placeholders are not convincing. | Real inputs, real outputs, chosen by a stated rule. |
| (pace) | Captions changed before they could be read. | Slow enough to read once aloud; length is not capped. |

## Voice and sound

| The user said | What it meant | Rule |
| --- | --- | --- |
| 开头已经很人性化了，像是在讲故事了，但是后续还是有点机械 | Later lines were voiced one by one and lost the storyteller. | One narrator persona for the whole film; one take per paragraph; the same style prompt throughout. |
| (no voice cloning; use the best natural stock voice) | A cloned voice of the user was tried and rejected. | Stock voices only. Offer 3-4 samples of one paragraph; the user chooses by ear. |
| (too flashy music → "simple rhythm + voice") | Music competes with the explanation. | Voice only, or voice over a plain quiet rhythm; deliver both. |
| (heard a click at the very start, noise at the ends of takes) | Raw API audio was written with its file header as samples. | Strip container headers; clean every take; check the first and last second. |
| 这两个地方衔接的时候似乎 t's 的音出现了两次 | A stray "s" sat at the join of two lines. | Scan every clip for stray sounds; a transcript check cannot hear them. |
| (bad split points, unnatural joins) | Cuts landed inside a line's own pause. | Cut at the last silence before the next line's first word; verify each piece by transcription. |
| 请你稍微省着点用 | TTS credit is limited. | Samples on one paragraph; rerun only changed paragraphs; report what was spent. |

## Working together

| The user said | What it meant | Rule |
| --- | --- | --- |
| (asks for a front-end page to review) | File paths in chat are not a review. | Build the review page every round: videos, scenes with pass/fix, audio choices, change list. |
| 这也太久了…你看看如何加速 | A serial render of a long film took far too long. | Parallel frame rendering from the start; never re-render for an audio-only fix. |
| (one flagged problem often had siblings) | Fixing only the named instance costs another round. | Search the whole film for the same pattern before reporting. |
| (wants conclusions, not process) | Long reports bury the decision. | Conclusion first, in the user's language, plain words, few numbers; say what is verified and what is not. |
| 我觉得差不多了 | The bar is "good enough to show", reached by removing every small annoyance. | The last rounds are small audio and wording fixes; plan time for them and catch them with the checks first. |

## How to use this for a different user

These are one researcher's preferences. For someone else keep the mechanism: show a storyboard and voice samples
early, record every remark as a rule with its reason, and check the next cut against the list before showing it.
