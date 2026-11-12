#!/usr/bin/env bash
# agy_call_media.sh — send one prompt (stdin) to Gemini through the agy CLI (Antigravity), print the text reply (stdout).
#
#   agy_call_media.sh [--attach FILE]...  < prompt.txt
#
# One round, no tools. The prompt must carry everything Gemini needs; this script
#   - runs agy in an empty temporary folder (no project files, no --add-dir, no slash commands),
#   - puts a "do not use tools, answer in one turn" header in front of the prompt,
#   - watches agy's event stream and stops it at the first tool call, then tries once more;
#     if the second try also reaches for a tool, it gives up (exit 3). A reply is never printed
#     from a run that used a tool.
# --attach: text files and PDFs (via pdftotext) are pasted into the prompt. Images, video and audio cannot be pasted:
#   agy's input takes text only (its stream-json input rejects image blocks, and "@file" in a prompt
#   attaches nothing; tested 2026-11-10). So they are copied into the temporary folder and Gemini may
#   open exactly those copies and nothing else.
#
# Settings may live in ${GEMINI_HUMANIZE_ENV:-~/.config/gemini-humanize.env} (plain KEY=VALUE lines).
# Env: GEMINI_MODEL (default gemini-3.8-flash-high), GEMINI_TIMEOUT (seconds, default 1200),
#      AGY_ENV_SH (optional shell file to source first, e.g. one that defines an `agy` function or a proxy)
# exit: 0 ok | 2 bad usage | 3 agy unavailable, failed, or would not answer without tools
set -uo pipefail

envfile="${GEMINI_HUMANIZE_ENV:-$HOME/.config/gemini-humanize.env}"
[ -r "$envfile" ] && { set -a; . "$envfile"; set +a; }

attach=()
while [ $# -gt 0 ]; do
  case "$1" in
    --attach) [ -r "${2:-}" ] || { echo "cannot read attachment: ${2:-}" >&2; exit 2; }; attach+=("$(readlink -f "$2")"); shift 2 ;;
    -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

work="$(mktemp -d "${TMPDIR:-/tmp}/agy_call.XXXXXX")" || exit 3
trap 'rm -rf "$work"' EXIT
cat > "$work/.prompt"
[ -s "$work/.prompt" ] || { echo "empty prompt" >&2; exit 2; }

AGY_ENV_SH="${AGY_ENV_SH:-}" \
GEMINI_MODEL="${GEMINI_MODEL:-gemini-3.8-flash-high}" GEMINI_TIMEOUT="${GEMINI_TIMEOUT:-1200}" \
python3 -I - "$work" "${attach[@]}" <<'PY'
import json, os, shutil, signal, subprocess, sys

work, *attach = sys.argv[1:]
model, timeout = os.environ["GEMINI_MODEL"], int(os.environ["GEMINI_TIMEOUT"])
prompt = open(f"{work}/.prompt", encoding="utf-8").read()
os.remove(f"{work}/.prompt")

# Attachments: paste text and PDFs; copy images next to the run.
pasted, images = [], []
for i, f in enumerate(attach):
    name = os.path.basename(f)
    mime = subprocess.run(["file", "--mime-type", "-b", f], stdout=subprocess.PIPE, universal_newlines=True).stdout.strip()
    if mime == "application/pdf":
        r = subprocess.run(["pdftotext", "-layout", f, "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode or not r.stdout.strip():
            sys.stderr.write(f"cannot extract text from PDF {f} (needs pdftotext); render pages to PNG and attach those\n")
            sys.exit(2)
        pasted.append(f"=== ATTACHED PDF (text only): {name} ===\n" + r.stdout.decode("utf-8", "replace").strip())
    elif mime.startswith(("image/", "video/", "audio/")):
        dst = f"{work}/attachment{i}_{name}"
        shutil.copy(f, dst)
        images.append(dst)
    elif mime.startswith("text/") or mime in ("application/json", "application/xml", "application/csv"):
        pasted.append(f"=== ATTACHED FILE: {name} ===\n" + open(f, encoding="utf-8", errors="replace").read().strip())
    else:
        sys.stderr.write(f"cannot attach {f} ({mime}): only text, PDF, images, video and audio\n")
        sys.exit(2)

def header(strict: bool) -> str:
    h = ("HOW TO ANSWER: everything you need is in this one message. Answer directly, in a single turn. "
         "Do not call any tool: do not read, list or search files, do not run commands, do not browse, "
         "do not ask questions, do not write files or plans. If something you need is missing, say what is missing "
         "in your answer instead of looking for it.")
    if images:
        h += ("\nThe only exception: you may open these media files (images, video, audio), each once, to watch or listen to them, and nothing else:\n"
              + "\n".join(images))
    if strict:
        h += "\nYour previous attempt was stopped because it called a tool. Answer from this message only."
    return h

def run(strict: bool):
    """One agy run. Returns (reply, None) or (None, reason)."""
    full = "\n\n".join([header(strict), prompt] + pasted)
    if len(full.encode()) > 1_500_000:
        sys.stderr.write(f"prompt is {len(full.encode())} bytes; too long for one round. Split the material.\n")
        sys.exit(2)
    # The prompt goes in on stdin as one NDJSON message (agy accepts only text blocks there), so its
    # length is not bound by the command-line limit.
    sh = ('[ -r "$AGY_ENV_SH" ] && . "$AGY_ENV_SH" >/dev/null 2>&1; '
          'agy --model "$1" --print-timeout "$2" --input-format stream-json --output-format stream-json '
          '--disable-slash-commands -p ""')
    msg = json.dumps({"event": "user", "message": {"content": [{"type": "text", "text": full}]}})
    with open(f"{work}/.msg", "w", encoding="utf-8") as fh:
        fh.write(msg + "\n")
    with open(f"{work}/.msg", encoding="utf-8") as fh:
        os.remove(f"{work}/.msg")
        p = subprocess.Popen(["bash", "-c", sh, "agy_call", model, f"{timeout}s"], cwd=work,
                             stdin=fh, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             universal_newlines=True, start_new_session=True)
    def stop():
        try:
            os.killpg(p.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    signal.signal(signal.SIGALRM, lambda *_: (stop(), sys.stderr.write("agy timed out\n"), sys.exit(3)))
    signal.alarm(timeout + 60)
    reply = reason = None
    for line in p.stdout:
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        step = ev.get("step_update") or {}
        if step.get("step_type") == "tool":
            info = json.dumps(step.get("tool_info") or {}, ensure_ascii=False)
            if not (images and any(im in info for im in images)):
                reason = f"tool call {step.get('tool_name')}: {info[:200]}"
                stop()
                break
        if ev.get("event") == "result":
            r = ev["result"]
            if r.get("status") == "SUCCESS" and (r.get("response") or "").strip():
                reply = r["response"].strip()
            else:
                reason = "agy error: " + str(r.get("error") or r.get("status"))[:300]
    p.wait()
    signal.alarm(0)
    if reply is None and reason is None:
        reason = "agy gave no reply: " + (p.stderr.read() or "")[-300:].strip()
    return (None, reason) if reason else (reply, None)

for strict in (False, True):
    reply, reason = run(strict)
    if reply is not None:
        print(reply)
        sys.exit(0)
    sys.stderr.write(f"agy_call: {reason}\n")
    if not reason.startswith("tool call"):
        break
sys.exit(3)
PY
