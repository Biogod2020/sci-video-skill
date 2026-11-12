#!/usr/bin/env python3
"""Review page for a film: the user watches in a browser, marks every scene pass / fix, writes comments; they are saved to disk.
  review_server.py REVIEW.json [port]        (binds 127.0.0.1 only; default port 8770)
REVIEW.json sits in the film folder (paths are relative to it):
{"title": "My film", "note": "current version: v3, 4:48. What changed: ...",
 "videos": [{"label": "voice + rhythm", "file": "film_voice_rhythm.mp4"}, {"label": "voice only", "file": "film_voice_only.mp4"}],
 "audio":  [{"label": "voice A", "file": "audio/test/A.wav"}],                      (optional: samples to choose from by ear)
 "changes": ["0:32 removed a doubled s", "..."],                                      (optional: what is new, newest first)
 "scenes": [{"id": "s1", "t": 12.5, "title": "The problem", "say": "narration of this scene", "thumb": "stills/t012.5.png"}]}
Only the files named in REVIEW.json are served. Feedback goes to review_feedback.json next to REVIEW.json; read it
before the next round and answer every comment."""
import html, json, os, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import re

CONF = os.path.abspath(sys.argv[1]); ROOT = os.path.dirname(CONF); FEEDBACK = os.path.join(ROOT, 'review_feedback.json')
TYPES = {'.jpg': 'image/jpeg', '.png': 'image/png', '.mp4': 'video/mp4', '.wav': 'audio/wav', '.mp3': 'audio/mpeg'}
PAGE = """<!doctype html><meta charset="utf-8"><title>%(title)s</title>
<style>body{font:16px/1.6 system-ui,sans-serif;max-width:1100px;margin:32px auto;padding:0 20px;color:#14171f}
video{width:100%%;background:#000;border-radius:8px}h1{font-size:26px}h2{font-size:19px;margin-top:36px}
.tabs button,.sc button{font:inherit;padding:6px 14px;border:1px solid #cfd4dc;background:#fff;border-radius:6px;cursor:pointer;margin-right:6px}
.tabs button.on{background:#14171f;color:#fff}.sc{display:grid;grid-template-columns:260px 1fr;gap:18px;padding:16px 0;border-top:1px solid #e5e8ee}
.sc img{width:260px;border:1px solid #e5e8ee;border-radius:6px;cursor:pointer}.say{color:#4b5563}
.sc button.ok.on{background:#1b8a4b;color:#fff}.sc button.fix.on{background:#cf3b34;color:#fff}
textarea{width:100%%;min-height:54px;font:inherit;margin-top:8px;box-sizing:border-box}#saved{color:#6b7280;margin-left:12px}
.a{display:flex;align-items:center;gap:12px;margin:6px 0}</style>
<h1>%(title)s</h1><p>%(note)s</p><div class="tabs" id="tabs"></div><video id="v" controls preload="metadata"></video>
<div id="changes"></div><div id="audio"></div><h2>Scene by scene</h2><div id="scenes"></div>
<h2>Overall</h2><textarea id="overall" placeholder="Anything about the whole film"></textarea>
<p><button id="save" style="font:inherit;padding:8px 20px">Save feedback</button><span id="saved"></span></p>
<script>const C=%(conf)s;const v=document.getElementById('v');let fb={scenes:{},overall:''};
const fmt=t=>Math.floor(t/60)+':'+String(Math.floor(t%%60)).padStart(2,'0');
C.videos.forEach((x,i)=>{const b=document.createElement('button');b.textContent=x.label;b.onclick=()=>{const t=v.currentTime;v.src='/media/v'+i;v.currentTime=t;
[...tabs.children].forEach(c=>c.classList.toggle('on',c===b))};tabs.appendChild(b);if(!i)b.click()});
if(C.changes&&C.changes.length)changes.innerHTML='<h2>What changed</h2><ul>'+C.changes.map(c=>'<li>'+c+'</li>').join('')+'</ul>';
if(C.audio&&C.audio.length)audio.innerHTML='<h2>Listen and choose</h2>'+C.audio.map((a,i)=>'<div class="a"><span style="width:220px">'+a.label+'</span><audio controls preload="none" src="/media/a'+i+'"></audio></div>').join('');
function draw(){scenes.innerHTML='';(C.scenes||[]).forEach((s,i)=>{const f=fb.scenes[s.id]||(fb.scenes[s.id]={mark:'',text:''});const d=document.createElement('div');d.className='sc';
d.innerHTML=(s.thumb?'<img src="/media/t'+i+'">':'<div></div>')+'<div><b>'+fmt(s.t)+' · '+s.title+'</b><div class="say">'+(s.say||'')+'</div><p><button class="ok">pass</button><button class="fix">fix</button></p><textarea placeholder="What should change here?"></textarea></div>';
const [ok,fx]=d.querySelectorAll('button'),ta=d.querySelector('textarea');ta.value=f.text;ok.classList.toggle('on',f.mark==='pass');fx.classList.toggle('on',f.mark==='fix');
ok.onclick=()=>{f.mark='pass';draw()};fx.onclick=()=>{f.mark='fix';draw()};ta.oninput=()=>{f.text=ta.value};
const im=d.querySelector('img');if(im)im.onclick=()=>{v.currentTime=s.t;v.play();v.scrollIntoView({behavior:'smooth'})};scenes.appendChild(d)});overall.value=fb.overall||''}
overall.oninput=()=>{fb.overall=overall.value};
save.onclick=async()=>{const r=await fetch('/api/feedback',{method:'POST',body:JSON.stringify(fb)});const j=await r.json();saved.textContent=j.ok?'saved '+j.saved_at:'not saved'};
fetch('/api/feedback').then(r=>r.json()).then(j=>{if(j.scenes)fb=j;draw()}).catch(draw);</script>"""


def conf():
    return json.load(open(CONF, encoding='utf-8'))


class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a):
        pass

    def resolve(self, path):          # /media/v0, /media/a1, /media/t3 -> only files named in REVIEW.json
        m = re.fullmatch(r'/media/([vat])(\d+)', path); c = conf()
        if not m: return None
        items = {'v': c.get('videos', []), 'a': c.get('audio', []), 't': c.get('scenes', [])}[m.group(1)]; i = int(m.group(2))
        f = items[i].get('thumb' if m.group(1) == 't' else 'file') if i < len(items) else None
        f = os.path.realpath(os.path.join(ROOT, f)) if f else None
        return f if f and f.startswith(os.path.realpath(ROOT) + os.sep) else None

    def send_bytes(self, code, body, ctype='application/json'):
        self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/api/feedback':
            return self.send_bytes(200, open(FEEDBACK, 'rb').read() if os.path.exists(FEEDBACK) else b'{}')
        if path in ('/', ''):
            c = conf(); esc = lambda o: json.dumps(o, ensure_ascii=False).replace('</', '<\\/')
            body = PAGE % {'title': html.escape(c.get('title', 'Film review')), 'note': html.escape(c.get('note', '')),
                           'conf': esc({k: c.get(k, []) for k in ('videos', 'audio', 'changes', 'scenes')})}
            return self.send_bytes(200, body.encode(), 'text/html; charset=utf-8')
        f = self.resolve(path)
        if not f or not os.path.isfile(f):
            return self.send_bytes(404, b'not found', 'text/plain')
        size = os.path.getsize(f); start, end, code = 0, size - 1, 200
        m = re.match(r'bytes=(\d*)-(\d*)', self.headers.get('Range', ''))     # browsers need Range to seek in a video
        if m and (m.group(1) or m.group(2)):
            if m.group(1):
                start = int(m.group(1)); end = min(int(m.group(2)), size - 1) if m.group(2) else size - 1
            else:
                start = max(0, size - int(m.group(2)))
            if start > end:
                self.send_response(416); self.send_header('Content-Range', f'bytes */{size}'); self.send_header('Content-Length', '0')
                return self.end_headers()
            code = 206
        self.send_response(code)
        self.send_header('Content-Type', TYPES.get(os.path.splitext(f)[1].lower(), 'application/octet-stream'))
        self.send_header('Accept-Ranges', 'bytes'); self.send_header('Content-Length', str(end - start + 1))
        if code == 206: self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        try:
            with open(f, 'rb') as fh:
                fh.seek(start); left = end - start + 1
                while left > 0:
                    chunk = fh.read(min(1 << 18, left))
                    if not chunk: break
                    self.wfile.write(chunk); left -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        if self.path != '/api/feedback':
            return self.send_bytes(404, b'not found', 'text/plain')
        n = int(self.headers.get('Content-Length', 0))
        if n > 1 << 20:
            return self.send_bytes(413, b'too large', 'text/plain')
        try:
            data = json.loads(self.rfile.read(n)); assert isinstance(data, dict)
        except Exception:
            return self.send_bytes(400, b'bad json', 'text/plain')
        data['saved_at'] = time.strftime('%Y-%m-%d %H:%M:%S'); tmp = FEEDBACK + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as fh: json.dump(data, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, FEEDBACK)
        self.send_bytes(200, json.dumps({'ok': True, 'saved_at': data['saved_at']}).encode())


if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', int(sys.argv[2]) if len(sys.argv) > 2 else 8770), H).serve_forever()
