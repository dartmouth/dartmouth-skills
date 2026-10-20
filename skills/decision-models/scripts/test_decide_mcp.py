"""Offline tests for decide_mcp.py against a mock System One server.

Run:  uv run --with "fastmcp>=4.1,<5" python3 -m unittest skills/decision-models/scripts/test_decide_mcp.py
(or plain `python3 -m unittest ...`: fastmcp/pydantic are stubbed if missing, and the
MCP protocol round-trip test is skipped.)
"""

from __future__ import annotations

import base64
import importlib
import json
import os
import sys
import tempfile
import threading
import types
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def _stub_missing_deps() -> None:
    """Let the core logic be tested where fastmcp can't be installed."""
    try:
        import fastmcp  # noqa: F401
        return
    except ImportError:
        pass

    class _FastMCP:
        def __init__(self, *a, **k):
            self.name = k.get("name")

        def _deco(self, *a, **k):
            return lambda fn: fn

        tool = resource = prompt = _deco

        def run(self):
            raise RuntimeError("stub")

    fm = types.ModuleType("fastmcp")
    fm.FastMCP = _FastMCP
    exc = types.ModuleType("fastmcp.exceptions")
    exc.ToolError = type("ToolError", (Exception,), {})
    server = types.ModuleType("fastmcp.server")
    lifespan_mod = types.ModuleType("fastmcp.server.lifespan")
    lifespan_mod.lifespan = lambda fn: fn
    pyd = types.ModuleType("pydantic")
    pyd.Field = lambda *a, **k: None
    sys.modules.update({"fastmcp": fm, "fastmcp.exceptions": exc, "fastmcp.server": server,
                        "fastmcp.server.lifespan": lifespan_mod, "pydantic": pyd})


_stub_missing_deps()
sys.path.insert(0, str(Path(__file__).parent))
decide_mcp = importlib.import_module("decide_mcp")

ANSWERS = {
    "urgent": {"type": "noul", "noul": 0.52},
    "team": {"type": "choice", "choice": "technical", "probabilities": {"technical": 0.9, "billing": 0.05, "other": 0.05}, "confidence": 0.85},
    "severity": {"type": "score", "score": 1.2, "legend": {"0": "a", "1": "b", "2": "c"}, "probabilities": {"0": 0.1, "1": 0.6, "2": 0.3}, "confidence": 0.3},
}
QUESTIONS = {
    "urgent": {"type": "noul", "instructions": "Does `ticket` describe something blocking customers now?"},
    "team": {"type": "choice", "instructions": "Which team should handle `ticket`?", "criteria": {"technical": "outages", "billing": "payments", "other": None}},
    "severity": {"type": "score", "instructions": "How severe is `ticket`?", "criteria": ["cosmetic", "workaround exists", "blocking"]},
}


def fake_batch_answer(q: dict, subject) -> dict:
    """Deterministic answers for packed requests, derived from the item's text."""
    text = json.dumps(subject).lower()
    if q["type"] == "noul":
        return {"type": "noul", "noul": 0.9 if "down" in text else 0.1}
    if q["type"] == "score":
        level = 2.0 if "down" in text else 1.0 if "slow" in text else 0.0
        return {"type": "score", "score": level, "confidence": 0.9}
    return {"type": "choice", "choice": next(iter(q["criteria"])), "confidence": 0.9}


class Mock(BaseHTTPRequestHandler):
    log: list = []
    fail_429_once = False
    max_questions = 64

    def log_message(self, *a):
        pass

    def _send(self, code, payload):
        raw = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/v1/models":
            return self._send(200, {"data": [{"id": "cloudflare.clef"}, {"id": "clef-flash"}, {"id": "clef"}, {"id": "jev"}]})
        if self.path == "/gw/v1/models":  # a gateway lists every LLM it serves
            return self._send(200, {"data": [{"id": "gpt-6-luna"}, {"id": "cloudflare.clef"}, {"id": "glm-5.3"}]})
        self._send(404, {"error": "nope"})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Mock.log.append({"path": self.path, "body": body, "auth": self.headers.get("Authorization")})
        gateway = self.path.startswith("/gw/")
        if gateway:  # LiteLLM-style /v1/systemone pass-through to the big clef
            self.path = self.path[3:]
        if Mock.fail_429_once:
            Mock.fail_429_once = False
            return self._send(429, {"error": "slow down"})
        if body.get("model") == "bad":
            return self._send(422, {"error": "model must match ^(cloudflare\\.clef|clef|clef-flash)$"})
        ollama_like = self.path == "/v1/systemone" and not gateway
        allowed = {"model", "state", "questions", "images"} | ({"keep_alive"} if ollama_like else set())
        if set(body) - allowed:
            return self._send(400, {"error": f"unexpected {set(body) - allowed}"})
        if len(body["questions"]) > Mock.max_questions:
            return self._send(413, {"error": "request too large"})
        state = body["state"]
        if isinstance(state, dict) and "items" in state:
            answers = {qid: fake_batch_answer(q, state["items"][qid.split(".", 1)[0]]) for qid, q in body["questions"].items()}
        else:
            answers = {k: ANSWERS[k] for k in body["questions"] if k in ANSWERS}
            if "ok" in body["questions"]:  # prewarm
                answers["ok"] = {"type": "noul", "noul": 0.99}
        result = {"model": body["model"], "answers": answers, "usage": {"input_tokens": 100, "output_tokens": 0}}
        if gateway:
            # Big model: confident answers; gateway-style extras (id, object, diagnostics).
            result["model"] = "clef"
            result["answers"] = {
                k: ({"type": "noul", "noul": 0.97, "probabilities": {"yes": 0.97, "no": 0.03}, "confidence": 0.97}
                    if q["type"] == "noul" else {**ANSWERS.get(k, {"type": q["type"]}), "confidence": 0.92})
                for k, q in body["questions"].items()
            }
            result.update({"id": "decision-1", "object": "structured_decision", "created": 1,
                           "diagnostics": {k: {"label_mass": 0.6 if "leaky" in k else 1.0, "argmax_is_label": "offlabel" not in k}
                                           for k in body["questions"]}})
        if self.path.startswith("/client/v4/"):
            return self._send(200, {"result": result, "success": True, "errors": [], "messages": []})
        self._send(200, result)


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), Mock)
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        Mock.log.clear()
        Mock.max_questions = 64
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("DECIDE_", "CLOUDFLARE_", "LITELLM_"))}
        self.addCleanup(self._restore_env)

    def _restore_env(self):
        os.environ.clear()
        os.environ.update(self.env)

    def cfg(self, **env):
        os.environ.clear()
        os.environ.update(self.env)
        os.environ.update({"DECIDE_BASE_URL": self.base, "DECIDE_TIMEOUT": "3", **env})
        return decide_mcp.config()


class DecideTests(Base):
    def test_litellm_default_route_and_auth(self):
        out = decide_mcp.run_decision({"ticket": "checkout down"}, QUESTIONS, cfg=self.cfg(DECIDE_API_KEY="sk-test"))
        call = Mock.log[-1]
        self.assertEqual(call["path"], "/v1/systemone")
        self.assertEqual(call["auth"], "Bearer sk-test")
        self.assertEqual(set(call["body"]), {"model", "state", "questions"})
        self.assertEqual(call["body"]["model"], "cloudflare.clef")
        self.assertEqual(out["answers"]["team"]["choice"], "technical")

    def test_warnings_flag_unsure_noul_and_low_confidence(self):
        out = decide_mcp.run_decision("x", QUESTIONS, cfg=self.cfg())
        joined = " ".join(out["warnings"])
        self.assertIn("`urgent` noul=0.52", joined)
        self.assertIn("`severity` confidence=0.30", joined)
        self.assertNotIn("`team`", joined)

    def test_systemone_backend_with_keep_alive(self):
        decide_mcp.run_decision("x", QUESTIONS, model="clef", cfg=self.cfg(DECIDE_BACKEND="systemone", DECIDE_KEEP_ALIVE="10m"))
        call = Mock.log[-1]
        self.assertEqual(call["path"], "/v1/systemone")
        self.assertEqual(call["body"]["model"], "clef")
        self.assertEqual(call["body"]["keep_alive"], "10m")

    def test_keep_alive_never_sent_to_litellm(self):
        decide_mcp.run_decision("x", QUESTIONS, cfg=self.cfg(DECIDE_KEEP_ALIVE="10m"))
        self.assertNotIn("keep_alive", Mock.log[-1]["body"])

    def test_cloudflare_envelope_unwrapped(self):
        cfg = self.cfg(DECIDE_BACKEND="cloudflare", CLOUDFLARE_ACCOUNT_ID="acct", CLOUDFLARE_AUTH_TOKEN="cf-tok", DECIDE_CLOUDFLARE_API_BASE=self.base)
        out = decide_mcp.run_decision("x", {"team": QUESTIONS["team"]}, model="clef-flash", cfg=cfg)
        self.assertEqual(Mock.log[-1]["path"], "/client/v4/accounts/acct/ai/run/@cf/cloudflare/clef-flash")
        self.assertEqual(Mock.log[-1]["auth"], "Bearer cf-tok")
        self.assertEqual(out["answers"]["team"]["choice"], "technical")

    def test_cloudflare_requires_credentials(self):
        with self.assertRaisesRegex(decide_mcp.DecideError, "CLOUDFLARE_ACCOUNT_ID"):
            decide_mcp.run_decision("x", QUESTIONS, cfg=self.cfg(DECIDE_BACKEND="cloudflare"))

    def test_retry_on_429(self):
        Mock.fail_429_once = True
        out = decide_mcp.run_decision("x", QUESTIONS, cfg=self.cfg())
        self.assertEqual(len(Mock.log), 2)
        self.assertIn("team", out["answers"])

    def test_4xx_fails_fast_with_detail(self):
        with self.assertRaisesRegex(decide_mcp.DecideError, "HTTP 422.*clef-flash"):
            decide_mcp.run_decision("x", QUESTIONS, model="bad", cfg=self.cfg())
        self.assertEqual(len(Mock.log), 1)

    def test_unreachable_backend(self):
        cfg = self.cfg()
        cfg["base_url"] = "http://127.0.0.1:9"
        cfg["timeout"] = 1
        with self.assertRaisesRegex(decide_mcp.DecideError, "Could not reach"):
            decide_mcp.run_decision("x", QUESTIONS, cfg=cfg)

    def test_images_via_litellm_need_media_url(self):
        img = self._png()
        with self.assertRaisesRegex(decide_mcp.DecideError, "DECIDE_MEDIA_BASE_URL"):
            decide_mcp.run_decision("x", QUESTIONS, image_paths=[img], cfg=self.cfg())
        decide_mcp.run_decision("x", QUESTIONS, image_paths=[img], cfg=self.cfg(DECIDE_MEDIA_BASE_URL=self.base))
        call = Mock.log[-1]
        self.assertEqual(call["path"], "/v1/systemone")
        self.assertTrue(call["body"]["images"][0].startswith("data:image/png;base64,"))

    def test_raw_image_format(self):
        img = self._png()
        decide_mcp.run_decision("x", QUESTIONS, image_paths=[img], cfg=self.cfg(DECIDE_BACKEND="systemone", DECIDE_IMAGE_FORMAT="raw"))
        sent = Mock.log[-1]["body"]["images"][0]
        self.assertFalse(sent.startswith("data:"))
        self.assertEqual(base64.b64decode(sent)[:4], b"\x89PNG")

    def test_audit_log_has_metadata_not_state(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "decide.jsonl"
            decide_mcp.run_decision({"ticket": "SECRET-CONTENT"}, QUESTIONS, cfg=self.cfg(DECIDE_LOG=str(log)))
            text = log.read_text()
            rec = json.loads(text.strip())
            self.assertNotIn("SECRET-CONTENT", text)
            self.assertEqual(rec["question_ids"], ["severity", "team", "urgent"])
            self.assertEqual(rec["tool"], "decide")

    def test_list_models(self):
        out = decide_mcp.list_models(cfg=self.cfg())
        self.assertEqual(out["endpoints"][0]["models"], ["cloudflare.clef", "clef-flash", "clef", "jev"])
        self.assertEqual(out["default"], "cloudflare.clef")

    def test_litellm_key_fallback(self):
        decide_mcp.run_decision("x", QUESTIONS, cfg=self.cfg(LITELLM_KEY="lk-1"))
        self.assertEqual(Mock.log[-1]["auth"], "Bearer lk-1")

    def test_prewarm(self):
        self.assertTrue(decide_mcp.prewarm(cfg=self.cfg(DECIDE_BACKEND="systemone")))
        self.assertEqual(Mock.log[-1]["body"]["questions"]["ok"]["type"], "noul")
        Mock.log.clear()
        self.assertFalse(decide_mcp.prewarm(cfg=self.cfg(DECIDE_PREWARM="off")))
        self.assertFalse(decide_mcp.prewarm(cfg=self.cfg(DECIDE_BACKEND="cloudflare")))  # auto skips paid backend
        self.assertEqual(Mock.log, [])

    def test_validation(self):
        cfg = self.cfg()
        bad = [
            ({}, "non-empty"),
            ({f"q{i}": QUESTIONS["urgent"] for i in range(65)}, "limit is 64"),
            ({"a:b": QUESTIONS["urgent"]}, "no ':'"),
            ({"q": {"type": "bool", "instructions": "x"}}, "noul, choice, score"),
            ({"q": {"type": "noul"}}, "instructions"),
            ({"q": {"type": "noul", "instructions": "x", "temperature": 0}}, "unknown fields"),
            ({"q": {"type": "noul", "instructions": "x", "criteria": {"maybe": "?"}}}, "true` / `false"),
            ({"q": {"type": "choice", "instructions": "x", "criteria": {"only": None}}}, "2..26"),
            ({"q": {"type": "choice", "instructions": "x", "criteria": {f"o{i}": None for i in range(27)}}}, "2..26"),
            ({"q": {"type": "score", "instructions": "x", "criteria": {"low": "?"}}}, "ordered list"),
            ({"q": {"type": "score", "instructions": "x", "criteria": [str(i) for i in range(11)]}}, "2..10"),
        ]
        for qs, msg in bad:
            with self.subTest(msg=msg), self.assertRaisesRegex(decide_mcp.DecideError, msg):
                decide_mcp.run_decision("x", qs, cfg=cfg)
        with self.assertRaisesRegex(decide_mcp.DecideError, "state"):
            decide_mcp.run_decision("", QUESTIONS, cfg=cfg)
        self.assertEqual(Mock.log, [], "invalid requests must not reach the backend")

    def test_image_limits(self):
        with self.assertRaisesRegex(decide_mcp.DecideError, "PNG, JPEG or WebP"):
            decide_mcp.load_images(["/tmp/x.gif"], "dataurl")
        with self.assertRaisesRegex(decide_mcp.DecideError, "not found"):
            decide_mcp.load_images(["/nonexistent/x.png"], "dataurl")
        with self.assertRaisesRegex(decide_mcp.DecideError, "At most 4"):
            decide_mcp.load_images(["a.png"] * 5, "dataurl")

    def _png(self) -> str:
        f = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
        f.close()
        self.addCleanup(os.unlink, f.name)
        return f.name


class GatewayTests(Base):
    """Gateway routing, diagnostics, and escalation."""

    def routed(self, **env):
        routes = {"cloudflare.clef": {"backend": "systemone", "base_url": f"{self.base}/gw", "api_key_env": "GW_KEY"}}
        return self.cfg(DECIDE_BACKEND="systemone", DECIDE_MODEL="clef-flash", DECIDE_KEEP_ALIVE="10m", GW_KEY="gw-secret",
                        DECIDE_ROUTES=json.dumps(routes), **env)

    def test_gateway_as_plain_systemone_backend(self):
        cfg = self.cfg(DECIDE_BACKEND="systemone", DECIDE_BASE_URL=f"{self.base}/gw", LITELLM_KEY="lk", DECIDE_MODEL="cloudflare.clef")
        out = decide_mcp.run_decision("Checkout is down.", {"outage": {"type": "noul", "instructions": "Is the service down?"}}, cfg=cfg)
        self.assertEqual(Mock.log[-1]["path"], "/gw/v1/systemone")
        self.assertEqual(Mock.log[-1]["auth"], "Bearer lk")
        self.assertEqual(out["model"], "clef")  # gateway alias in, served name out
        self.assertGreater(out["answers"]["outage"]["noul"], 0.9)
        self.assertEqual(out["warnings"], [])

    def test_routes_send_each_model_to_its_endpoint(self):
        cfg = self.routed()
        decide_mcp.run_decision("x", QUESTIONS, cfg=cfg)
        local = Mock.log[-1]
        self.assertEqual(local["path"], "/v1/systemone")
        self.assertEqual(local["body"]["keep_alive"], "10m")
        self.assertIsNone(local["auth"])
        decide_mcp.run_decision("x", QUESTIONS, model="cloudflare.clef", cfg=cfg)
        gw = Mock.log[-1]
        self.assertEqual(gw["path"], "/gw/v1/systemone")
        self.assertEqual(gw["auth"], "Bearer gw-secret")
        self.assertNotIn("keep_alive", gw["body"], "per-endpoint settings must not leak to the gateway")

    def test_diagnostics_flag_off_label_answers(self):
        cfg = self.cfg(DECIDE_BACKEND="systemone", DECIDE_BASE_URL=f"{self.base}/gw", DECIDE_MODEL="cloudflare.clef")
        qs = {"leaky_q": {"type": "noul", "instructions": "a?"}, "offlabel_q": {"type": "noul", "instructions": "b?"},
              "fine": {"type": "noul", "instructions": "c?"}}
        joined = " ".join(decide_mcp.run_decision("x", qs, cfg=cfg)["warnings"])
        self.assertIn("`leaky_q` only 0.60 of the probability", joined)
        self.assertIn("`offlabel_q` the model's top prediction was not one of your options", joined)
        self.assertNotIn("`fine`", joined)

    def test_escalation_reasks_only_unsure_questions_on_big_model(self):
        cfg = self.routed(DECIDE_ESCALATE_MODEL="cloudflare.clef")
        out = decide_mcp.run_decision("x", QUESTIONS, cfg=cfg)
        self.assertEqual(len(Mock.log), 2)
        self.assertEqual(sorted(Mock.log[1]["body"]["questions"]), ["severity", "urgent"])  # team was confident
        self.assertEqual(Mock.log[1]["path"], "/gw/v1/systemone")
        self.assertEqual(out["escalated"], {"model": "clef", "questions": ["severity", "urgent"]})
        self.assertEqual(out["answers"]["urgent"]["noul"], 0.97)
        self.assertEqual(out["answers"]["team"]["choice"], "technical")  # kept from clef-flash
        self.assertEqual(out["usage"]["input_tokens"], 200)
        self.assertEqual(out["warnings"], [])

    def test_escalation_can_be_disabled_per_call(self):
        out = decide_mcp.run_decision("x", QUESTIONS, cfg=self.routed(DECIDE_ESCALATE_MODEL="cloudflare.clef"), escalate=False)
        self.assertEqual(len(Mock.log), 1)
        self.assertNotIn("escalated", out)
        self.assertTrue(out["warnings"])

    def test_escalation_failure_keeps_first_answers(self):
        routes = {"cloudflare.clef": {"base_url": "http://127.0.0.1:9"}}
        cfg = self.cfg(DECIDE_BACKEND="systemone", DECIDE_MODEL="clef-flash", DECIDE_ROUTES=json.dumps(routes), DECIDE_ESCALATE_MODEL="cloudflare.clef")
        cfg["timeout"] = 1
        out = decide_mcp.run_decision("x", QUESTIONS, cfg=cfg)
        self.assertEqual(out["answers"]["urgent"]["noul"], 0.52)
        self.assertIn("Escalation to cloudflare.clef failed", " ".join(out["warnings"]))

    def test_prewarm_auto_skips_remote_gateway(self):
        routes = {"cloudflare.clef": {"base_url": "https://gateway.example.org"}}
        cfg = self.cfg(DECIDE_ROUTES=json.dumps(routes), DECIDE_MODEL="cloudflare.clef")
        self.assertFalse(decide_mcp.prewarm(cfg=cfg))
        self.assertEqual(Mock.log, [])

    def test_list_models_per_endpoint_filters_gateway_llms(self):
        out = decide_mcp.list_models(cfg=self.routed(DECIDE_ESCALATE_MODEL="cloudflare.clef"))
        self.assertEqual(out["escalate_to"], "cloudflare.clef")
        by = {e["for"]: e for e in out["endpoints"]}
        self.assertEqual(by["cloudflare.clef"]["models"], ["cloudflare.clef"])
        self.assertEqual(by["(default endpoint)"]["models"], ["cloudflare.clef", "clef-flash", "clef", "jev"])

    def test_bad_routes_json(self):
        with self.assertRaisesRegex(decide_mcp.DecideError, "DECIDE_ROUTES"):
            decide_mcp.run_decision("x", QUESTIONS, cfg=self.cfg(DECIDE_ROUTES="{nope"))

    def test_batch_on_gateway_maps_diagnostics(self):
        cfg = self.cfg(DECIDE_BACKEND="systemone", DECIDE_BASE_URL=f"{self.base}/gw", DECIDE_MODEL="cloudflare.clef")
        out = decide_mcp.run_batch({"a": "down", "b": "fine"}, {"leaky": {"type": "noul", "instructions": "Is `item` an outage?"}}, cfg=cfg)
        self.assertEqual(set(out["results"]), {"a", "b"})
        joined = " ".join(out["warnings"])
        self.assertIn("`a.leaky` only 0.60", joined)
        self.assertIn("`b.leaky` only 0.60", joined)


BATCH_Q = {
    "blocking": {"type": "noul", "instructions": "Does `item.text` describe customers being blocked right now?"},
    "severity": {"type": "score", "instructions": "How severe is the issue?", "criteria": ["cosmetic", "degraded", "outage"]},
}
ITEMS = {
    "T-1": {"text": "Typo on the about page"},
    "T-2": {"text": "Checkout is down for everyone"},
    "T-3": {"text": "Search is slow at peak"},
}


class BatchTests(Base):
    def test_packs_items_into_one_request_and_maps_back(self):
        out = decide_mcp.run_batch(ITEMS, BATCH_Q, cfg=self.cfg())
        self.assertEqual(len(Mock.log), 1)
        body = Mock.log[0]["body"]
        self.assertEqual(len(body["questions"]), 6)
        self.assertEqual(set(body["state"]["items"]), {"i0", "i1", "i2"})
        # `item` references are rewritten; questions without one get an explicit scope.
        self.assertEqual(body["questions"]["i1.blocking"]["instructions"], "Does `items.i1.text` describe customers being blocked right now?")
        self.assertTrue(body["questions"]["i2.severity"]["instructions"].startswith("About `items.i2` only:"))
        self.assertEqual(set(out["results"]), set(ITEMS))
        self.assertGreater(out["results"]["T-2"]["blocking"]["noul"], 0.8)
        self.assertEqual(out["usage"], {"input_tokens": 100, "requests": 1, "splits": 0})

    def test_chunks_by_question_limit(self):
        many = {f"x{n}": {"text": f"item {n}"} for n in range(40)}  # 2 questions each -> 32 items per request
        out = decide_mcp.run_batch(many, BATCH_Q, cfg=self.cfg())
        self.assertEqual([len(c["body"]["questions"]) for c in Mock.log], [64, 16])
        self.assertEqual(len(out["results"]), 40)

    def test_chunks_by_state_size(self):
        decide_mcp.run_batch(ITEMS, BATCH_Q, cfg=self.cfg(DECIDE_BATCH_MAX_STATE_CHARS="40"))
        self.assertEqual(len(Mock.log), 3)

    def test_splits_oversize_pack_on_413(self):
        Mock.max_questions = 4
        out = decide_mcp.run_batch({f"x{n}": {"text": "down"} for n in range(4)}, BATCH_Q, cfg=self.cfg())
        self.assertEqual(out["usage"]["splits"], 1)
        self.assertEqual(out["usage"]["requests"], 2)
        self.assertTrue(all(r["blocking"]["noul"] > 0.8 for r in out["results"].values()))

    def test_rank_filter_and_top_k(self):
        out = decide_mcp.run_batch(ITEMS, BATCH_Q, rank_by="severity", min_value=0.5, top_k=1, cfg=self.cfg())
        self.assertEqual(out["ranking"], [{"id": "T-2", "value": 2.0}])

    def test_rank_filter_falls_back_when_everything_is_dropped(self):
        out = decide_mcp.run_batch(ITEMS, BATCH_Q, rank_by="severity", min_value=5, top_k=2, cfg=self.cfg())
        self.assertEqual([r["id"] for r in out["ranking"]], ["T-2", "T-3"])
        self.assertIn("returning the top items unfiltered", " ".join(out["warnings"]))

    def test_batch_validation(self):
        cfg = self.cfg()
        with self.assertRaisesRegex(decide_mcp.DecideError, "non-empty"):
            decide_mcp.run_batch({}, BATCH_Q, cfg=cfg)
        with self.assertRaisesRegex(decide_mcp.DecideError, "item `a` is empty"):
            decide_mcp.run_batch({"a": ""}, BATCH_Q, cfg=cfg)
        with self.assertRaisesRegex(decide_mcp.DecideError, "rank_by"):
            decide_mcp.run_batch(ITEMS, BATCH_Q, rank_by="nope", cfg=cfg)
        self.assertEqual(Mock.log, [])


@unittest.skipUnless(hasattr(sys.modules["fastmcp"], "Client"), "real fastmcp not installed")
class ProtocolTests(Base):
    def test_mcp_roundtrip(self):
        """In-memory FastMCP client: components are listed and tools return structured answers."""
        import asyncio
        from fastmcp import Client

        self.cfg(DECIDE_PREWARM="off")

        async def go():
            async with Client(decide_mcp.mcp) as client:
                tools = {t.name for t in await client.list_tools()}
                prompts = {p.name for p in await client.list_prompts()}
                resources = {str(r.uri) for r in await client.list_resources()}
                single = await client.call_tool("decide", {"state": {"ticket": "down"}, "questions": QUESTIONS})
                batch = await client.call_tool("decide_batch", {"items": ITEMS, "questions": BATCH_Q, "rank_by": "severity"})
                guide = await client.read_resource("decide://guide")
                return tools, prompts, resources, single.data, batch.data, guide

        tools, prompts, resources, single, batch, guide = asyncio.run(go())
        self.assertEqual(tools, {"decide", "decide_batch", "decision_models"})
        self.assertIn("design_questions", prompts)
        self.assertIn("decide://guide", resources)
        self.assertEqual(single["answers"]["team"]["choice"], "technical")
        self.assertEqual(batch["ranking"][0]["id"], "T-2")
        self.assertIn("Writing decide questions", guide[0].text)


if __name__ == "__main__":
    unittest.main()
