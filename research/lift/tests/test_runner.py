"""Tests for pilot/run_participants.py with fake backends (no network, no subprocess)."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

PILOT = Path(__file__).resolve().parents[1] / "pilot"
sys.path.insert(0, str(PILOT))
import pilotlib as pl  # noqa: E402


def _load(name):
    spec = importlib.util.spec_from_file_location("pilot_" + name, PILOT / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


make_packets, freeze, rp, ingest = (_load(n) for n in ("make_packets", "freeze", "run_participants", "ingest"))
BMAP = rp.parse_map(rp.DEFAULT_MAP)


def build(tmp, name="pilot", do_freeze=True):
    d = Path(tmp) / name
    with contextlib.redirect_stdout(io.StringIO()):
        assert make_packets.main(["--vendors", "sonnet,haiku,qwen", "--per-arm-per-vendor", "1",
                                  "--seed", "1", "--out-dir", str(d)]) == 0
        if do_freeze:
            assert freeze.main(["--dir", str(d)]) == 0
    return d


def fake(tag, sent):
    def call(packet):
        sent.append((tag, packet))
        return {"text": f"reply from {tag}", "thinking": "hmm" if tag == "ollama" else "", "model_ids": [f"id-{tag}"],
                "temperature": "default", "system_prompt": "x", "other_settings": {"tag": tag}}
    return call


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = self._t.name
        self.addCleanup(self._t.cleanup)

    def backends(self, sent):
        return {("claude", "sonnet"): fake("sonnet", sent), ("claude", "haiku"): fake("haiku", sent),
                ("ollama", "qwen3.5:9b"): fake("ollama", sent)}

    def test_writes_txt_and_meta_for_every_pid(self):
        d = build(self.tmp)
        sent = []
        done = rp.run(d, BMAP, self.backends(sent), log=lambda *_: None)
        pids = [r["participant_id"] for r in pl.read_allocation(d)]
        self.assertEqual(len(done), len(pids))
        for pid in pids:
            self.assertTrue((d / "responses" / f"{pid}.txt").is_file())
            meta = json.loads((d / "responses" / f"{pid}.meta.json").read_text())
            for k in ("vendor", "model_id", "date", "temperature", "other_settings", "system_prompt",
                      "duration_s", "transport_retries"):
                self.assertIn(k, meta)
            self.assertTrue(meta["model_id"])
            # participant received exactly its packet text
            self.assertIn((d / "packets" / f"{pid}.md").read_text(), [p for _, p in sent])
        self.assertEqual(len((d / "run_log.jsonl").read_text().splitlines()), len(pids))
        self.assertTrue(list((d / "responses").glob("*.thinking.txt")))

    def test_skips_existing_and_only(self):
        d = build(self.tmp)
        first = pl.read_allocation(d)[0]["participant_id"]
        (d / "responses" / f"{first}.txt").write_text("already")
        sent = []
        done = rp.run(d, BMAP, self.backends(sent), log=lambda *_: None)
        self.assertNotIn(first, [r["participant_id"] for r in done])
        self.assertEqual((d / "responses" / f"{first}.txt").read_text(), "already")
        sent2 = []
        self.assertEqual(rp.run(d, BMAP, self.backends(sent2), log=lambda *_: None), [])
        self.assertEqual(sent2, [])

    def test_ingest_ignores_thinking_files(self):
        d = build(self.tmp)
        rp.run(d, BMAP, self.backends([]), log=lambda *_: None)
        with contextlib.redirect_stdout(io.StringIO()):
            ingest.main(["--dir", str(d)])
        log = json.loads((d / "ingest_log.json").read_text())
        self.assertNotIn("unknown_participant_id", [x["reason"] for x in log["excluded"]])

    def test_refuses_unfrozen_dir(self):
        d = build(self.tmp, do_freeze=False)
        with self.assertRaises(ValueError):
            rp.run(d, BMAP, self.backends([]))
        self.assertFalse((d / "run_log.jsonl").exists())

    def test_refuses_private_path(self):
        d = build(self.tmp, name="my-private-pilot")
        with self.assertRaises(ValueError):
            rp.run(d, BMAP, self.backends([]))
        # macOS /private/tmp prefix alone is not a private-gold marker
        parts = Path("/private/tmp/x").parts
        self.assertEqual(parts[1], "private")

    def test_transport_retry_max_two_no_retry_on_content(self):
        d = build(self.tmp)
        calls = []
        def flaky(packet):
            calls.append(1)
            raise rp.TransportError("boom")
        b = self.backends([])
        b[("claude", "sonnet")] = flaky
        done = rp.run(d, BMAP, b, only={next(r["participant_id"] for r in pl.read_allocation(d) if r["vendor"] == "sonnet")},
                      log=lambda *_: None)
        self.assertEqual(len(calls), 3)
        self.assertTrue(done[0]["failed"])

    def test_claude_command_has_every_isolation_flag(self):
        cmd = rp.claude_command("sonnet")
        self.assertEqual(cmd[:2], ["claude", "-p"])
        for flag, val in (("--model", "sonnet"), ("--tools", ""), ("--setting-sources", ""),
                          ("--system-prompt", "You are a helpful assistant."), ("--output-format", "json")):
            self.assertEqual(cmd[cmd.index(flag) + 1], val, flag)
        self.assertIn("--strict-mcp-config", cmd)
        self.assertIn("--no-session-persistence", cmd)

    def test_ollama_payload_and_backend(self):
        p = rp.ollama_payload("qwen3.5:9b", "PKT", 32768)
        self.assertIs(p["stream"], False)
        self.assertEqual(p["options"], {"num_ctx": 32768})
        self.assertNotIn("temperature", p["options"])
        self.assertEqual(p["messages"], [{"role": "user", "content": "PKT"}])
        seen = []
        def http(url, payload, timeout):
            seen.append((url, payload))
            if url.endswith("/api/chat"):
                return {"message": {"content": "ans", "thinking": "th"}}
            return {"models": [{"name": "qwen3.5:9b", "digest": "abc"}]}
        r = rp.ollama_backend("qwen3.5:9b", "http://h:1", 4096, 5, http=http)("PKT")
        self.assertEqual((r["text"], r["thinking"], r["model_ids"]), ("ans", "th", ["qwen3.5:9b"]))
        self.assertEqual(r["other_settings"]["model_digest"], "abc")
        self.assertIs(seen[0][1]["stream"], False)
        self.assertEqual(seen[0][1]["options"]["num_ctx"], 4096)


if __name__ == "__main__":
    unittest.main()
