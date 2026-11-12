"""Narration with stock (not cloned) voices. One item = one paragraph read in one go.
  tts.py gemini OUT_DIR ITEMS.json --voices Sulafat [--takes 1] [--model gemini-3.8-flash-tts]
  tts.py gpt    OUT_DIR ITEMS.json --voices cedar   [--takes 1] [--model gpt-audio-1.5]      (chat completions audio)
  tts.py speech OUT_DIR ITEMS.json --voices cedar   [--takes 1] [--model gpt-4o-mini-tts]    (/v1/audio/speech)
ITEMS.json = [{"id": "P1", "text": "..."}] -> OUT_DIR/<id>_<voice>_t<k>.wav. Existing files are kept, so a rerun only fills gaps.
--say "..."      pronunciation notes for this film, e.g. "'GEO' is spoken as the letters G, E, O."
--style-file F   replace the default narrator style with the text in F
The API key is read from the file named by TTS_KEYFILE, else from GOOGLE_API_KEY / OPENAI_API_KEY, else from
~/.config/sci-video/{google_key,openai_key}. It is never printed (error bodies are masked)."""
import argparse, base64, json, os, struct, sys, time, wave
from pathlib import Path
import httpx

STYLE = ("A scientist narrating a short film about their own research to colleagues. Warm, clear and conversational, as if "
         "explaining it to a friend across a table: natural melody inside sentences, small pauses between sentences, a slightly "
         "longer pause after a result. Unhurried, about 150 words per minute. Never announcer-like, never salesy, never "
         "dramatic. Sentence endings land gently and do not sink into a low creaky voice.")
SAY = "Numbers are read exactly as written."


def pcm_of(raw, sr):
    """The API may return a whole WAV file (RIFF header, data chunk, then a provenance chunk) instead of bare PCM.
    Writing that as samples puts a click at the start and a burst of noise at the end, so keep only the data chunk."""
    if raw[:4] != b"RIFF": return raw, sr
    i = 12
    while i + 8 <= len(raw):
        cid, n = raw[i:i + 4], struct.unpack("<I", raw[i + 4:i + 8])[0]
        if cid == b"fmt ": sr = struct.unpack("<I", raw[i + 12:i + 16])[0]
        if cid == b"data": return raw[i + 8:i + 8 + n], sr
        i += 8 + n + (n & 1)
    return raw, sr


def gemini(c, key, model, voice, text):
    prompt = ("# AUDIO PROFILE: Research film narrator\n" + STYLE + "\n\n## DIRECTOR'S NOTES\nPronunciation: " + SAY +
              "\nRead the transcript exactly, word for word.\n\n## TRANSCRIPT\n" + text)
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseModalities": ["AUDIO"], "temperature": 1.0,
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    for i in range(5):
        r = c.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", json=body, headers={"x-goog-api-key": key})
        if r.status_code == 200: break
        print("HTTP", r.status_code, r.text[:200].replace(key, "***"), file=sys.stderr); time.sleep(8 * (i + 1))
    else: return None
    cand = r.json().get("candidates", [{}])[0]
    if "content" not in cand: print("no audio, finishReason", cand.get("finishReason"), file=sys.stderr); return None
    d = next(p for p in cand["content"]["parts"] if "inlineData" in p)["inlineData"]
    sr = int(d["mimeType"].split("rate=")[1].split(";")[0]) if "rate=" in d.get("mimeType", "") else 24000
    return pcm_of(base64.b64decode(d["data"]), sr)


def gpt(c, key, model, voice, text):
    sysmsg = ("You are a voice-over artist recording the narration of a short research film. Read the user's script EXACTLY as "
              "written, word for word: do not add, drop or change any word, do not greet, do not comment. " + STYLE + " " + SAY)
    body = {"model": model, "modalities": ["text", "audio"], "audio": {"voice": voice, "format": "pcm16"},
            "messages": [{"role": "system", "content": sysmsg}, {"role": "user", "content": "Script:\n" + text}]}
    r = c.post("https://api.openai.com/v1/chat/completions", json=body, headers={"Authorization": f"Bearer {key}"})
    if r.status_code != 200: print("HTTP", r.status_code, r.text[:200].replace(key, "***"), file=sys.stderr); return None
    return base64.b64decode(r.json()["choices"][0]["message"]["audio"]["data"]), 24000


def speech(c, key, model, voice, text):
    """OpenAI /v1/audio/speech (gpt-4o-mini-tts): the style goes in `instructions`, the script in `input`."""
    body = {"model": model, "voice": voice, "input": text, "instructions": STYLE + " " + SAY, "response_format": "wav"}
    r = c.post("https://api.openai.com/v1/audio/speech", json=body, headers={"Authorization": f"Bearer {key}"})
    if r.status_code != 200: print("HTTP", r.status_code, r.text[:200].replace(key, "***"), file=sys.stderr); return None
    return pcm_of(r.content, 24000)


ap = argparse.ArgumentParser(); ap.add_argument("engine"); ap.add_argument("out"); ap.add_argument("items"); ap.add_argument("--voices", required=True)
ap.add_argument("--takes", type=int, default=1); ap.add_argument("--start", type=int, default=0); ap.add_argument("--model"); ap.add_argument("--say", default=""); ap.add_argument("--style-file")
a = ap.parse_args()
if a.style_file: STYLE = Path(a.style_file).read_text().strip()
SAY = (a.say.strip() + " " + SAY).strip()
O = Path(a.out); O.mkdir(parents=True, exist_ok=True)
var = "GOOGLE_API_KEY" if a.engine == "gemini" else "OPENAI_API_KEY"
kf = os.environ.get("TTS_KEYFILE") or (None if os.environ.get(var) else "~/.config/sci-video/" + ("google_key" if a.engine == "gemini" else "openai_key"))
key = Path(kf).expanduser().read_text().strip() if kf else os.environ[var].strip()
fn, model = {"gemini": (gemini, a.model or "gemini-3.8-flash-tts"), "gpt": (gpt, a.model or "gpt-audio-1.5"),
             "speech": (speech, a.model or "gpt-4o-mini-tts")}[a.engine]
with httpx.Client(timeout=httpx.Timeout(600, connect=20)) as c:
    for it in json.load(open(a.items)):
        for v in a.voices.split(","):
            for k in range(a.start, a.start + a.takes):
                f = O / f"{it['id']}_{v}_t{k}.wav"
                if f.exists(): continue
                t0 = time.time(); res = fn(c, key, model, v, it["text"])
                if not res: continue
                with wave.open(str(f), "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(res[1]); w.writeframes(res[0])
                print("wrote", f.name, round(len(res[0]) / 2 / res[1], 2), "s audio in", round(time.time() - t0), "s", flush=True)
