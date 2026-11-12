# The film page: one canvas, one world, one camera

`assets/template/` is a small working film (5 lines, 24 s). Copy it and replace the world, the camera path and the
script. It already has the parts that are easy to get wrong.

## Files

| File | Role |
| --- | --- |
| `story.py` | The script: id, paragraph, picture time, caption, spoken form. Generates everything under `build/` and `captions.js`. |
| `film.html` | Loads fonts and images before the first frame, then the scripts; `?t=12.5` shows one moment in a browser. |
| `film_core.js` | Easing helpers, seeded random, the time warp, the world, the camera, captions, `renderAt(t)`. |
| `build/vo_warp.js` | Written by `vo_plan.py` once narration exists. Without it the film runs on the picture clock, so the picture can be developed first. |

For a long film split scenes into several files (`film_scene_problem.js`, …) that each add draw functions; keep one
`renderAt`.

## Two clocks

- **Picture clock `T`**: the clock the animation is written on. Camera keyframes and all object timings use it.
  `story.py` gives each line the picture time at which its caption appears.
- **Film clock `t`**: real playback time. `vo_plan.py` makes each caption's slot at least as long as its spoken line
  and writes `VO_WARP`, a list of `[film time, picture time]` pairs; `pic(t)` interpolates between them.

So when a spoken line is longer than the animation under it, that stretch of animation simply plays a little slower.
Write the picture at a comfortable silent pace first; speech will only lengthen it. If a scene must not stretch (a
physical-looking motion), give it a line break right before and after so the stretch falls on a hold.

## Determinism

`renderAt(t)` must draw the same frame for the same `t`, from nothing: clear, set the camera transform, draw the
world, draw the overlay. Use `rng(seed)` for any scatter. Precompute layouts once at load. Do not depend on the
previous frame (no accumulating particles); express motion as a function of `T`
(`pos = lerp(a, b, io((T - t0) / d))`).

## Camera and continuity

- World coordinates are larger than the screen; place each act in its own region and move the camera
  (`CAM` keyframes: time, centre, zoom, eased).
- Carry an object across acts when you can: the dot that stood for one dataset becomes the record that is examined,
  then returns to its place in the final atlas. This is what removes the slide feeling.
- Overlays that do not belong to the world (captions, a small provenance label) are drawn after resetting the
  transform. Keep them few.
- Fade objects with a window (`win(T, a, b)`), and check a still shortly after each scene change for leftovers.

## Cover and close

The cover is part of the same world: the name is set in large type on white, a first caption line is spoken, and the
camera then moves or the letters dissolve into the first objects. Hold the final frame for about 2 s after the last
word.

## Looking before rendering

```bash
node $S/render.mjs stills 0,2,7,13,17,22       # stills/t00002.png ...
python3 $S/sheet.py board 0,2,7,13,17,22       # stills/board_0.jpg: six per sheet
```

Make stills at every caption time. Read the sheets yourself, send them to the reviewer, show them to the user. Only
then:

```bash
node $S/render.mjs frames 30 8                 # frames/f00000.jpg ... with 8 Chrome workers
bash $S/mux.sh myfilm build/voice.wav 30 --rhythm
```

Environment: `PUPPETEER_DIR` (a `node_modules` holding puppeteer, if it is not installed in the film folder), `CHROME`
(browser binary), `FILM` (page name, default `film.html`).
