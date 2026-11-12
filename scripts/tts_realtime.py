"""Narration through OpenAI's Realtime API (the gpt-realtime models have no plain HTTP speech endpoint).
The key is read from the file named by TTS_KEYFILE, else OPENAI_API_KEY, else ~/.config/sci-video/openai_key; never printed.
  tts_realtime.py OUT_DIR ITEMS.json --voices cedar [--model gpt-realtime-2.1] [--takes 1] [--say "pronunciation notes"]
ITEMS.json = [{"id": "P1", "text": "..."}] -> OUT_DIR/<id>_<voice>_t<k>.wav, same naming as tts.py.
Needs aiohttp and certifi; honours https_proxy."""
import argparse, asyncio, base64, json, os, ssl, sys, time, wave
from pathlib import Path
import aiohttp, certifi

STYLE = ("A scientist narrating a short film about their own research to colleagues. Warm, clear and conversational, as if "
         "explaining it to a friend across a table: natural melody inside sentences, small pauses between sentences, a slightly "
         "longer pause after a result. Unhurried, about 150 words per minute. Never announcer-like, never salesy, never "
         "dramatic. Sentence endings land gently and do not sink into a low creaky voice.")
SAY = "Numbers are read exactly as written."
HEAD = ("You are a voice-over artist recording the narration of a short research film. Read the user's script EXACTLY as "
        "written, word for word: do not add, drop or change any word, do not greet, do not comment. ")


async def one(s, key, model, voice, text, SYS):
    proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    async with s.ws_connect(f"wss://api.openai.com/v1/realtime?model={model}", headers={"Authorization": f"Bearer {key}"},
                            proxy=proxy, ssl=ssl.create_default_context(cafile=certifi.where()), max_msg_size=0, heartbeat=20) as ws:
        await ws.send_json({"type": "session.update", "session": {"type": "realtime", "output_modalities": ["audio"], "instructions": SYS,
                            "audio": {"output": {"voice": voice, "format": {"type": "audio/pcm", "rate": 24000}}}}})
        await ws.send_json({"type": "conversation.item.create", "item": {"type": "message", "role": "user",
                            "content": [{"type": "input_text", "text": "Script:\n" + text}]}})
        await ws.send_json({"type": "response.create"})
        pcm, usage = bytearray(), None
        async for m in ws:
            if m.type != aiohttp.WSMsgType.TEXT: break
            ev = json.loads(m.data); t = ev.get("type", "")
            if t in ("response.output_audio.delta", "response.audio.delta"): pcm += base64.b64decode(ev["delta"])
            elif t == "error": print("error:", json.dumps(ev.get("error"))[:300].replace(key, "***"), file=sys.stderr)
            elif t == "response.done":
                r = ev.get("response", {}); usage = r.get("usage")
                if r.get("status") != "completed": print("status:", r.get("status"), json.dumps(r.get("status_details"))[:300], file=sys.stderr)
                break
        return bytes(pcm), usage


async def main():
    ap = argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("items"); ap.add_argument("--voices", required=True)
    ap.add_argument("--takes", type=int, default=1); ap.add_argument("--model", default="gpt-realtime-2.1"); ap.add_argument("--say", default=""); a = ap.parse_args()
    SYS = HEAD + STYLE + " " + (a.say.strip() + " " + SAY).strip()
    O = Path(a.out); O.mkdir(parents=True, exist_ok=True)
    kf = os.environ.get("TTS_KEYFILE") or (None if os.environ.get("OPENAI_API_KEY") else "~/.config/sci-video/openai_key")
    key = Path(kf).expanduser().read_text().strip() if kf else os.environ["OPENAI_API_KEY"].strip()
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as s:
        for it in json.load(open(a.items)):
            for v in a.voices.split(","):
                for k in range(a.takes):
                    f = O / f"{it['id']}_{v}_t{k}.wav"
                    if f.exists(): continue
                    t0 = time.time(); pcm, usage = await one(s, key, a.model, v, it["text"], SYS)
                    if not pcm: continue
                    with wave.open(str(f), "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
                    out = (usage or {}).get("output_token_details", {})
                    print("wrote", f.name, round(len(pcm) / 48000, 2), "s audio in", round(time.time() - t0), "s; audio tokens out",
                          out.get("audio_tokens"), flush=True)

asyncio.run(main())
