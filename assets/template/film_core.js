/* One canvas, one world, one camera. Objects stay where they are; the camera moves between them instead of cutting.
   renderAt(t) draws the frame for film time t and nothing else decides what is on screen: no timers, no Math.random(),
   no CSS animation. That is what makes every frame reproducible and lets frames be rendered in parallel. */
const cv = document.getElementById('c'), g = cv.getContext('2d'), W = 1920, H = 1080;
const FG = '#14171f', DIM = '#6b7280', LINE = '#dfe3ea', ACC = '#1f5fd6', GREY = '#b6bcc8';
const clamp = (x) => Math.max(0, Math.min(1, x));
const eo = (x) => { x = clamp(x); return 1 - Math.pow(1 - x, 3); };
const io = (x) => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const lerp = (a, b, p) => a + (b - a) * p;
function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const F = (px, w = 400) => `${w} ${px}px Inter, "Helvetica Neue", Arial, sans-serif`;
const win = (T, a, b, fi = 0.4, fo = 0.4) => Math.min(eo((T - a) / fi), eo((b - T) / fo));   // fade in at a, out by b

/* ---------- time: film time (with narration) -> picture time (the clock the animation is written on) ---------- */
const WARP = window.VO_WARP || null;
window.DURATION = WARP ? WARP[WARP.length - 1][0] : PICTURE_END;
function pic(t) {
  if (!WARP) return t;
  for (let i = 1; i < WARP.length; i++) if (t <= WARP[i][0]) { const [a, pa] = WARP[i - 1], [b, pb] = WARP[i]; return lerp(pa, pb, (t - a) / (b - a || 1)); }
  return WARP[WARP.length - 1][1];
}

/* ---------- world (example: a field of dots, a few of them marked, and two records further right) ---------- */
const N = 1200, dots = [];
{ const R = rng(7); for (let k = 0; k < N; k++) { const r = 13 * Math.sqrt(k + .5), a = k * 2.39996; dots.push([Math.cos(a) * r, Math.sin(a) * r, R() < 0.04]); } }
const REC = [[900, -90, 'Sex: F'], [900, 60, 'gender: female']];

/* ---------- camera: keyframes on the picture clock [time, centre x, centre y, zoom]; eased between ---------- */
const CAM = [[0, 0, 0, 0.9], [9, 0, 0, 1.0], [11.5, 900, 0, 1.5], [18.5, 900, 0, 1.5], [21, 450, 0, 0.75], [24, 450, 0, 0.72]];
function cam(T) {
  let i = 1; while (i < CAM.length - 1 && T > CAM[i][0]) i++;
  const a = CAM[i - 1], b = CAM[i], p = io((T - a[0]) / (b[0] - a[0]));
  return [lerp(a[1], b[1], p), lerp(a[2], b[2], p), lerp(a[3], b[3], p)];
}

function drawWorld(T) {
  for (const [x, y, hit] of dots) {
    const on = hit ? eo((T - 5) / 1.2) : 0;                       // the marked ones turn blue when the narration names them
    g.fillStyle = on > 0 ? ACC : GREY; g.globalAlpha = hit ? 1 : lerp(1, 0.45, eo((T - 5) / 1.2));
    g.beginPath(); g.arc(x, y, 3 + 2.5 * on, 0, 7); g.fill();
  }
  g.globalAlpha = 1;
  REC.forEach(([x, y, s], k) => {
    const a = eo((T - 10.5 - k * 0.5) / 0.8); if (a <= 0) return;
    g.globalAlpha = a; g.fillStyle = '#fff'; g.strokeStyle = LINE; g.lineWidth = 2;
    g.beginPath(); g.roundRect(x - 190, y - 48 + (1 - a) * 20, 380, 96, 14); g.fill(); g.stroke();
    g.fillStyle = FG; g.font = F(34, 500); g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(s, x, y + (1 - a) * 20);
    g.globalAlpha = 1;
  });
}

/* ---------- captions: shown on film time when the narration is planned, on the picture clock before that ---------- */
function caption(t, T) {
  let text = '', a = 0;
  if (window.VO_LINES) { for (const [s, e, id] of VO_LINES) if (t >= s && t <= e) { text = CAPS.find((c) => c.id === id).text; a = win(t, s, e, 0.3, 0.3); } }
  else CAPS.forEach((c, i) => { const e = (CAPS[i + 1] ? CAPS[i + 1].at : PICTURE_END) - 0.15; if (T >= c.at && T <= e) { text = c.text; a = win(T, c.at, e, 0.3, 0.3); } });
  if (!text) return;
  g.globalAlpha = a; g.fillStyle = FG; g.font = F(40, 500); g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(text, W / 2, H - 110); g.globalAlpha = 1;
}

window.renderAt = function (t) {
  const T = pic(t), [cx, cy, z] = cam(T);
  g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = '#fff'; g.fillRect(0, 0, W, H);
  g.setTransform(z, 0, 0, z, W / 2 - cx * z, H / 2 - 40 - cy * z); drawWorld(T);
  g.setTransform(1, 0, 0, 1, 0, 0); caption(t, T);
};
