"""Isolated participant runner for the Lift pilot (stdlib only).

PILOT - EXPLORATORY, NOT CONFIRMATORY. Sends each packets/<pid>.md ONCE as the single user message to a
backend and saves the raw reply to responses/<pid>.txt plus responses/<pid>.meta.json. No repo content,
canon, matrix or gold is ever sent. No retry on a poor answer; transport errors are retried at most twice.

  python run_participants.py --dir PILOT_DIR [--only p01,p02] [--dry-run]
      [--backend-map sonnet=claude:sonnet,haiku=claude:haiku,qwen=ollama:qwen3.5:9b]
      [--ollama-url http://localhost:11434] [--num-ctx 32768] [--timeout 900]
"""
from __future__ import annotations
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pilotlib as pl  # noqa: E402

DEFAULT_MAP = "sonnet=claude:sonnet,haiku=claude:haiku,qwen=ollama:qwen3.5:9b"
SYSTEM_PROMPT = "You are a helpful assistant."
MAX_TRANSPORT_RETRIES = 2


class TransportError(Exception):
    pass


def claude_command(model):
    return ["claude", "-p", "--model", model, "--tools", "", "--strict-mcp-config", "--setting-sources", "",
            "--no-session-persistence", "--system-prompt", SYSTEM_PROMPT, "--output-format", "json"]


def claude_backend(model, timeout):
    """Return call(packet_text) -> dict(text, model_ids, settings). Runs in a fresh empty neutral temp dir."""
    def call(packet):
        cwd = tempfile.mkdtemp(prefix="p.", dir="/tmp")
        try:
            try:
                r = subprocess.run(claude_command(model), input=packet, capture_output=True, text=True,
                                   timeout=timeout, cwd=cwd)
            except (subprocess.TimeoutExpired, OSError) as exc:
                raise TransportError(f"claude: {exc}")
            if r.returncode != 0:
                raise TransportError(f"claude exit {r.returncode}: {r.stderr[:300]}")
            try:
                env = json.loads(r.stdout)
            except ValueError as exc:
                raise TransportError(f"claude: bad JSON envelope: {exc}")
            if env.get("is_error") or not isinstance(env.get("result"), str):
                raise TransportError(f"claude: error envelope: {str(env)[:300]}")
            return {"text": env["result"], "model_ids": sorted((env.get("modelUsage") or {}).keys()),
                    "temperature": "default", "system_prompt": SYSTEM_PROMPT,
                    "other_settings": {"backend": "claude -p", "alias": model, "command": claude_command(model),
                                       "cwd": "fresh empty temp dir"}}
        finally:
            shutil.rmtree(cwd, ignore_errors=True)
    return call


def _http_json(url, payload, timeout):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise TransportError(f"ollama {url}: {exc}")


def ollama_payload(model, packet, num_ctx):
    return {"model": model, "messages": [{"role": "user", "content": packet}], "stream": False,
            "options": {"num_ctx": num_ctx}}


def ollama_backend(model, url, num_ctx, timeout, http=_http_json):
    def call(packet):
        out = http(url.rstrip("/") + "/api/chat", ollama_payload(model, packet, num_ctx), timeout)
        msg = out.get("message") or {}
        if not isinstance(msg.get("content"), str):
            raise TransportError(f"ollama: no message.content: {str(out)[:300]}")
        digest = ""
        try:
            tags = http(url.rstrip("/") + "/api/tags", None, 30)
            for m in tags.get("models", []):
                if m.get("name") == model or m.get("model") == model:
                    digest = m.get("digest", "")
        except TransportError:
            pass
        return {"text": msg["content"], "thinking": msg.get("thinking") or "", "model_ids": [model],
                "temperature": "default", "system_prompt": "none",
                "other_settings": {"backend": "ollama /api/chat", "num_ctx": num_ctx, "stream": False,
                                   "model_digest": digest}}
    return call


def parse_map(s):
    m = {}
    for part in s.split(","):
        vendor, _, spec = part.partition("=")
        kind, _, model = spec.partition(":")
        if not vendor or kind not in ("claude", "ollama") or not model:
            raise ValueError(f"bad --backend-map entry: {part!r}")
        m[vendor.strip()] = (kind, model)
    return m


def check_dir(d):
    d = Path(d)
    parts = [x.lower() for x in d.absolute().parts[1:]]
    if parts[:1] == ["private"] and parts[1:2] in (["tmp"], ["var"], ["etc"]):
        parts = parts[1:]  # macOS firmlink prefix of /tmp, /var: not a private-gold marker
    if any("private" in x for x in parts):
        raise ValueError("refusing a --dir whose path contains 'private'")
    problems = pl.verify_freeze(d)
    if problems:
        raise ValueError("freeze check failed, refusing to run: " + "; ".join(problems[:5]))


def plan(d, bmap, only=None):
    """[(pid, vendor, kind, model)] for participants with a mapped backend and no reply yet."""
    out = []
    for row in pl.read_allocation(d):
        pid, vendor = row["participant_id"], row["vendor"]
        if only is not None and pid not in only:
            continue
        if vendor not in bmap or (Path(d) / "responses" / f"{pid}.txt").exists():
            continue
        out.append((pid, vendor, *bmap[vendor]))
    return out


def run(d, bmap, backends, only=None, dry_run=False, log=print):
    """backends: {(kind, model): call}. Returns list of dicts describing each processed pid."""
    d = Path(d)
    check_dir(d)
    todo = plan(d, bmap, only)
    done = []
    for pid, vendor, kind, model in todo:
        if dry_run:
            log(f"{pid}\t{vendor}\t{kind}:{model}")
            done.append({"participant_id": pid, "vendor": vendor, "backend": f"{kind}:{model}"})
            continue
        packet = (d / "packets" / f"{pid}.md").read_text(encoding="utf-8")
        call = backends[(kind, model)]
        retries, t0, res = 0, time.time(), None
        while True:
            try:
                res = call(packet)
                break
            except TransportError as exc:
                retries += 1
                _append_log(d, {"participant_id": pid, "event": "transport_error", "attempt": retries, "error": str(exc)})
                if retries > MAX_TRANSPORT_RETRIES:
                    break
        dur = round(time.time() - t0, 3)
        if res is None:
            _append_log(d, {"participant_id": pid, "event": "failed", "transport_retries": retries - 1})
            done.append({"participant_id": pid, "vendor": vendor, "backend": f"{kind}:{model}", "failed": True})
            continue
        resp = d / "responses"
        resp.mkdir(exist_ok=True)
        if res.get("thinking"):
            (resp / f"{pid}.thinking.txt").write_text(res["thinking"], encoding="utf-8")
        meta = {"vendor": vendor, "model_id": ",".join(res["model_ids"]), "model_ids": res["model_ids"],
                "date": datetime.date.today().isoformat(), "temperature": res["temperature"],
                "other_settings": res["other_settings"], "system_prompt": res["system_prompt"],
                "duration_s": dur, "transport_retries": retries}
        (resp / f"{pid}.meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (resp / f"{pid}.txt").write_text(res["text"], encoding="utf-8")  # last: its presence marks "done"
        _append_log(d, {"participant_id": pid, "event": "ok", "backend": f"{kind}:{model}", "duration_s": dur,
                        "transport_retries": retries, "model_id": meta["model_id"]})
        done.append({"participant_id": pid, "vendor": vendor, "backend": f"{kind}:{model}", "meta": meta})
    return done


def _append_log(d, rec):
    rec = dict(rec, ts=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    with open(Path(d) / "run_log.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--only", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--backend-map", default=DEFAULT_MAP)
    ap.add_argument("--ollama-url", default="http://localhost:11434")
    ap.add_argument("--num-ctx", type=int, default=32768)
    ap.add_argument("--timeout", type=int, default=900)
    a = ap.parse_args(argv)
    try:
        bmap = parse_map(a.backend_map)
        backends = {}
        for kind, model in set(bmap.values()):
            backends[(kind, model)] = (claude_backend(model, a.timeout) if kind == "claude"
                                       else ollama_backend(model, a.ollama_url, a.num_ctx, a.timeout))
        only = set(a.only.split(",")) if a.only else None
        done = run(a.dir, bmap, backends, only, a.dry_run)
        failed = [x["participant_id"] for x in done if x.get("failed")]
        print(json.dumps({"status": "DRY_RUN" if a.dry_run else "DONE", "processed": len(done), "failed": failed}))
        return 1 if failed else 0
    except (ValueError, OSError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
