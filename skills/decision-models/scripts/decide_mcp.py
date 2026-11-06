#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["fastmcp>=4.1,<5"]
# ///
"""decide: an MCP server that lets a coding agent ask a decision model (Clef / Jev).

The agent keeps its own LLM. This server gives it read-only tools that send
`state` + typed `questions` to a System One-compatible endpoint and return
per-option probabilities. Use it for judgments whose answers can be listed in
advance (route, triage, yes/no, score, rerank); never for writing or math.

Tools:    decide (one state), decide_batch (many items, packed), decision_models
Prompt:   design_questions  (OpenCode shows it as /decide:design_questions)
Resource: decide://guide    (question-writing rules)

Backends (DECIDE_BACKEND):
  litellm     POST {DECIDE_BASE_URL}/v1/systemone   (default; Dartmouth Chat API / LiteLLM, text/JSON state)
  systemone   POST {DECIDE_BASE_URL}/v1/systemone   (direct vLLM /v1/systemone endpoint; images OK)
  cloudflare  POST https://api.cloudflare.com/client/v4/accounts/{id}/ai/run/@cf/cloudflare/{model}

Environment:
  DECIDE_BACKEND            litellm | systemone | cloudflare   (default litellm)
  DECIDE_BASE_URL           gateway / server base URL          (default https://chat.dartmouth.edu/api)
  DECIDE_API_KEY            Dartmouth Chat API key (Settings > Account > API Key); falls back to
                            DCHAT_KEY, then LITELLM_API_KEY, then LITELLM_KEY
  DECIDE_MODEL              default model                      (default cloudflare.clef)
  DECIDE_ROUTES             JSON: per-model endpoints, e.g.
                            {"<model>": {"backend": "litellm", "base_url": "...", "api_key_env": "DCHAT_KEY"}}
                            A routed model uses its route's settings; unrouted models use the DECIDE_* defaults.
  DECIDE_ESCALATE_MODEL     opt-in cascade: answers flagged unsure on the default model are re-asked
                            once on this model
  DECIDE_MEDIA_BASE_URL     /v1/systemone base used when images are sent through
                            the litellm backend (LiteLLM's native route strips media fields)
  DECIDE_IMAGE_FORMAT       dataurl | raw                      (default dataurl)
  DECIDE_KEEP_ALIVE         optional keep_alive field on systemone requests
  DECIDE_PREWARM            auto | on | off  (auto = on for localhost endpoints) (default auto)
  DECIDE_MAX_CHOICE_OPTIONS client-side cap on choice options  (default 26)
  DECIDE_BATCH_MAX_STATE_CHARS  JSON size cap per packed batch request (default 24000)
  DECIDE_TIMEOUT            seconds per HTTP attempt           (default 15)
  DECIDE_LOG                optional JSONL audit path (metadata only, never state)
  CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_AUTH_TOKEN   for the cloudflare backend
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.lifespan import lifespan
from pydantic import Field

QUESTION_TYPES = {"noul", "choice", "score"}
MAX_QUESTIONS = 64
MAX_SCORE_LEVELS = 10
MAX_IMAGES = 4
MAX_IMAGE_BYTES = 4 * 1024 * 1024
IMAGE_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
RETRYABLE_STATUS = {429, 502, 503, 504}
SPLITTABLE_STATUS = {400, 413}
UNSURE_BAND = (0.35, 0.65)
LOW_CONFIDENCE = 0.5
MIN_LABEL_MASS = 0.9
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
ITEM_REF = re.compile(r"`item((?:\.[A-Za-z_][\w-]*|\[\d+\])*)`")


class DecideError(Exception):
    """Raised for invalid requests or backend failures; surfaced to the agent verbatim."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


# --------------------------------------------------------------------------- config


def fallback_key() -> str | None:
    env = os.environ
    return env.get("DCHAT_KEY") or env.get("LITELLM_API_KEY") or env.get("LITELLM_KEY")


def config() -> dict[str, Any]:
    env = os.environ
    return {
        "backend": env.get("DECIDE_BACKEND", "litellm").strip().lower(),
        "base_url": env.get("DECIDE_BASE_URL", "https://chat.dartmouth.edu/api").rstrip("/"),
        "api_key": env.get("DECIDE_API_KEY") or fallback_key(),
        "model": env.get("DECIDE_MODEL", "cloudflare.clef"),
        "routes_raw": env.get("DECIDE_ROUTES") or "",
        "escalate_model": env.get("DECIDE_ESCALATE_MODEL") or None,
        "media_base_url": (env.get("DECIDE_MEDIA_BASE_URL") or "").rstrip("/") or None,
        "image_format": env.get("DECIDE_IMAGE_FORMAT", "dataurl").strip().lower(),
        "keep_alive": env.get("DECIDE_KEEP_ALIVE") or None,
        "prewarm": env.get("DECIDE_PREWARM", "auto").strip().lower(),
        "max_choice_options": int(env.get("DECIDE_MAX_CHOICE_OPTIONS", "26")),
        "batch_max_state_chars": int(env.get("DECIDE_BATCH_MAX_STATE_CHARS", "24000")),
        "timeout": float(env.get("DECIDE_TIMEOUT", "15")),
        "log_path": env.get("DECIDE_LOG"),
        "cf_account": env.get("CLOUDFLARE_ACCOUNT_ID"),
        "cf_token": env.get("CLOUDFLARE_AUTH_TOKEN"),
        "cf_api_base": env.get("DECIDE_CLOUDFLARE_API_BASE", "https://api.cloudflare.com").rstrip("/"),
    }


def routes(cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = cfg.get("routes_raw") or ""
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise DecideError(f"DECIDE_ROUTES is not valid JSON: {e}") from None
    if not isinstance(parsed, dict) or not all(isinstance(v, dict) for v in parsed.values()):
        raise DecideError('DECIDE_ROUTES must map model -> {"base_url": ..., ...}.')
    return parsed


def route_cfg(cfg: dict[str, Any], model: str) -> dict[str, Any]:
    """Settings for one model: its DECIDE_ROUTES entry if any, else the defaults.

    A route inherits no transport settings, so per-endpoint options or keys never
    leak across endpoints.
    """
    route = routes(cfg).get(model)
    if route is None:
        return cfg
    if not route.get("base_url") and route.get("backend", "systemone") != "cloudflare":
        raise DecideError(f"DECIDE_ROUTES[{model!r}] needs a base_url.")
    key_env = route.get("api_key_env")
    api_key = (os.environ.get(key_env) or fallback_key()) if key_env else None
    return {
        **cfg,
        "backend": route.get("backend", "systemone").strip().lower(),
        "base_url": (route.get("base_url") or "").rstrip("/"),
        "api_key": api_key,
        "keep_alive": route.get("keep_alive"),
        "image_format": route.get("image_format", "dataurl"),
        "media_base_url": (route.get("media_base_url") or "").rstrip("/") or None,
    }


def is_local(url: str) -> bool:
    return (urllib.parse.urlparse(url).hostname or "") in LOCAL_HOSTS


# ----------------------------------------------------------------------- validation


def validate_questions(questions: Any, max_choice_options: int) -> None:
    """Catch the common agent mistakes before spending a request."""
    if not isinstance(questions, dict) or not questions:
        raise DecideError("`questions` must be a non-empty object mapping id -> question.")
    if len(questions) > MAX_QUESTIONS:
        raise DecideError(f"{len(questions)} questions; the limit is {MAX_QUESTIONS} per request. Use decide_batch for many items.")
    for qid, q in questions.items():
        where = f"question `{qid}`"
        if not qid or ":" in qid or "\n" in qid:
            raise DecideError(f"{where}: ids must be non-empty and contain no ':' or newlines.")
        if not isinstance(q, dict):
            raise DecideError(f"{where}: must be an object with `type` and `instructions`.")
        qtype = q.get("type")
        if qtype not in QUESTION_TYPES:
            raise DecideError(f"{where}: `type` must be one of noul, choice, score (got {qtype!r}).")
        if not q.get("instructions"):
            raise DecideError(f"{where}: `instructions` is required and must carry the full meaning (ids are not read as the question).")
        extra = set(q) - {"type", "instructions", "criteria"}
        if extra:
            raise DecideError(f"{where}: unknown fields {sorted(extra)}; allowed are type, instructions, criteria.")
        crit = q.get("criteria")
        if qtype == "noul":
            if crit is not None and (not isinstance(crit, dict) or set(crit) - {"true", "false"}):
                raise DecideError(f"{where}: noul `criteria` is optional and may only have `true` / `false` keys.")
        elif qtype == "choice":
            if not isinstance(crit, dict) or not (2 <= len(crit) <= max_choice_options):
                raise DecideError(f"{where}: choice `criteria` must map 2..{max_choice_options} option ids to descriptions (or null).")
        elif qtype == "score":
            if not isinstance(crit, list) or not (2 <= len(crit) <= MAX_SCORE_LEVELS):
                raise DecideError(f"{where}: score `criteria` must be an ordered list of 2..{MAX_SCORE_LEVELS} levels, lowest first.")


def require_state(state: Any) -> None:
    if state is None or state == "" or state == {} or state == []:
        raise DecideError("`state` is required: the text or JSON the questions are about.")


def load_images(paths: list[str], fmt: str) -> list[str]:
    if len(paths) > MAX_IMAGES:
        raise DecideError(f"At most {MAX_IMAGES} images per request.")
    out = []
    for p in paths:
        path = Path(p).expanduser()
        mime = IMAGE_MIME.get(path.suffix.lower())
        if mime is None:
            raise DecideError(f"{p}: only PNG, JPEG or WebP images are supported.")
        if not path.is_file():
            raise DecideError(f"{p}: file not found.")
        data = path.read_bytes()
        if len(data) > MAX_IMAGE_BYTES:
            raise DecideError(f"{p}: {len(data)} bytes; the limit is 4 MiB. Downscale it first (about 1024 px wide is plenty).")
        b64 = base64.b64encode(data).decode()
        out.append(b64 if fmt == "raw" else f"data:{mime};base64,{b64}")
    return out


# --------------------------------------------------------------------------- transport


def build_request(cfg: dict[str, Any], body: dict[str, Any], has_media: bool) -> tuple[str, dict[str, str], dict[str, Any]]:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    backend = cfg["backend"]
    if backend == "cloudflare":
        if not (cfg["cf_account"] and cfg["cf_token"]):
            raise DecideError("cloudflare backend needs CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_AUTH_TOKEN.")
        url = f"{cfg['cf_api_base']}/client/v4/accounts/{cfg['cf_account']}/ai/run/@cf/cloudflare/{body['model']}"
        headers["Authorization"] = f"Bearer {cfg['cf_token']}"
        return url, headers, body
    if backend == "systemone":
        url = f"{cfg['base_url']}/v1/systemone"
        if cfg["keep_alive"]:
            body = {**body, "keep_alive": cfg["keep_alive"]}
    elif backend == "litellm":
        if has_media:
            if not cfg["media_base_url"]:
                raise DecideError("LiteLLM's native route strips images. Set DECIDE_MEDIA_BASE_URL to a vLLM /v1/systemone server, or drop the images.")
            url = f"{cfg['media_base_url']}/v1/systemone"
        else:
            url = f"{cfg['base_url']}/v1/systemone"
    else:
        raise DecideError(f"Unknown DECIDE_BACKEND {backend!r}; use litellm, systemone or cloudflare.")
    if cfg["api_key"]:
        headers["Authorization"] = f"Bearer {cfg['api_key']}"
    return url, headers, body


def post_json(url: str, headers: dict[str, str], body: dict[str, Any], timeout: float, retries: int = 2) -> dict[str, Any]:
    """POST with retries on 429/5xx-gateway/transport errors only; other 4xx fail fast."""
    data = json.dumps(body).encode()
    last: Exception | None = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            with e:
                detail = e.read().decode(errors="replace")[:2000]
            if e.code not in RETRYABLE_STATUS or attempt == retries:
                raise DecideError(f"Decision backend returned HTTP {e.code}: {detail}", status=e.code) from None
            last = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
            if attempt == retries:
                raise DecideError(f"Could not reach decision backend at {url}: {e}") from None
        time.sleep(0.5 * (2**attempt))
    raise DecideError(f"Decision backend failed: {last}")


def unwrap(payload: dict[str, Any]) -> dict[str, Any]:
    """Cloudflare REST wraps answers in {success, result, errors}; others return them directly."""
    if "success" in payload and "result" in payload:
        if not payload.get("success"):
            raise DecideError(f"Cloudflare error: {json.dumps(payload.get('errors'))[:2000]}")
        return payload["result"] or {}
    return payload


def send(cfg: dict[str, Any], body: dict[str, Any], has_media: bool = False) -> tuple[dict[str, Any], int]:
    rcfg = route_cfg(cfg, body["model"])
    if has_media and rcfg["image_format"] == "raw":
        body = {**body, "images": [i.split(",", 1)[1] if i.startswith("data:") else i for i in body["images"]]}
    url, headers, body = build_request(rcfg, body, has_media)
    started = time.monotonic()
    result = unwrap(post_json(url, headers, body, rcfg["timeout"]))
    if not isinstance(result.get("answers"), dict):
        raise DecideError(f"Backend response had no `answers`: {json.dumps(result)[:500]}")
    return result, round((time.monotonic() - started) * 1000)


def answer_value(a: Any) -> float | None:
    """Single number for ranking: P(yes) for noul, expected level for score."""
    if not isinstance(a, dict):
        return None
    v = a.get("noul") if a.get("type") == "noul" else a.get("score") if a.get("type") == "score" else None
    return float(v) if isinstance(v, (int, float)) else None


def flags_for(answers: dict[str, Any], diagnostics: dict[str, Any] | None = None) -> dict[str, str]:
    """question id -> reason the answer shouldn't be trusted as-is."""
    flags: dict[str, str] = {}
    for qid, a in answers.items():
        if not isinstance(a, dict):
            continue
        if a.get("type") == "noul" and isinstance(a.get("noul"), (int, float)):
            if UNSURE_BAND[0] <= a["noul"] <= UNSURE_BAND[1]:
                flags[qid] = f"noul={a['noul']:.2f}: the model can't tell. Say concretely what counts as yes, or add the missing evidence to state."
        elif isinstance(a.get("confidence"), (int, float)) and a["confidence"] < LOW_CONFIDENCE:
            flags[qid] = f"confidence={a['confidence']:.2f}: probability is spread out. Check the options are distinct and an `other` exit exists; don't act on it irreversibly."
    # Some servers (e.g. vLLM behind LiteLLM) report how much probability landed on your labels.
    for qid, d in (diagnostics or {}).items():
        if not isinstance(d, dict):
            continue
        if d.get("argmax_is_label") is False:
            flags[qid] = "the model's top prediction was not one of your options; treat this answer as unreliable and rewrite the question or its options."
        elif isinstance(d.get("label_mass"), (int, float)) and d["label_mass"] < MIN_LABEL_MASS:
            flags[qid] = f"only {d['label_mass']:.2f} of the probability fell on your options; the answer is renormalised and may be unreliable."
    return flags


def warnings_for(answers: dict[str, Any], prefix: str = "", diagnostics: dict[str, Any] | None = None) -> list[str]:
    return [f"`{prefix}{qid}` {why}" for qid, why in flags_for(answers, diagnostics).items()]


def audit(cfg: dict[str, Any], record: dict[str, Any]) -> None:
    if not cfg["log_path"]:
        return
    try:
        with open(Path(cfg["log_path"]).expanduser(), "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "backend": cfg["backend"], **record}) + "\n")
    except OSError:
        pass  # auditing must never break a decision


# -------------------------------------------------------------------------- decide


def run_decision(
    state: Any,
    questions: dict[str, Any],
    model: str | None = None,
    image_paths: list[str] | None = None,
    cfg: dict[str, Any] | None = None,
    escalate: bool = True,
) -> dict[str, Any]:
    cfg = cfg or config()
    require_state(state)
    validate_questions(questions, cfg["max_choice_options"])
    body: dict[str, Any] = {"model": model or cfg["model"], "state": state, "questions": questions}
    if image_paths:
        body["images"] = load_images(image_paths, "dataurl")  # converted per route in send()
    result, latency_ms = send(cfg, body, has_media=bool(image_paths))
    answers = dict(result["answers"])
    diagnostics = dict(result.get("diagnostics") or {})
    usage = dict(result.get("usage") or {})
    out: dict[str, Any] = {"model": result.get("model", body["model"])}
    notes: list[str] = []

    # Cascade: re-ask only the unsure questions, once, on the bigger model.
    esc = cfg["escalate_model"] if escalate else None
    flagged = sorted(flags_for(answers, diagnostics))
    if esc and esc != body["model"] and flagged:
        sub = {**body, "model": esc, "questions": {q: questions[q] for q in flagged if q in questions}}
        try:
            esc_result, esc_ms = send(cfg, sub, has_media=bool(image_paths))
            for q in sub["questions"]:
                if q in esc_result["answers"]:
                    answers[q] = esc_result["answers"][q]
                    diagnostics.pop(q, None)
                    if q in (esc_result.get("diagnostics") or {}):
                        diagnostics[q] = esc_result["diagnostics"][q]
            latency_ms += esc_ms
            usage["input_tokens"] = (usage.get("input_tokens") or 0) + ((esc_result.get("usage") or {}).get("input_tokens") or 0)
            out["escalated"] = {"model": esc_result.get("model", esc), "questions": list(sub["questions"])}
        except DecideError as e:
            notes.append(f"Escalation to {esc} failed ({e}); answers below are from {out['model']} only.")

    missing = sorted(set(questions) - set(answers))
    out.update({
        "answers": answers,
        "usage": usage or None,
        "latency_ms": latency_ms,
        "warnings": warnings_for(answers, diagnostics=diagnostics) + notes + ([f"No answer returned for: {missing}"] if missing else []),
    })
    audit(cfg, {"tool": "decide", "model": out["model"], "question_ids": sorted(questions), "images": len(image_paths or []),
                "escalated": out.get("escalated", {}).get("questions"), "usage": out["usage"], "latency_ms": latency_ms})
    return out


# -------------------------------------------------------------------- decide_batch


def _rewrite_refs(value: Any, key: str) -> Any:
    """Point `item`-relative references at this item's slot in the packed state."""
    if isinstance(value, str):
        return ITEM_REF.sub(lambda m: f"`items.{key}{m.group(1)}`", value)
    if isinstance(value, list):
        return [_rewrite_refs(v, key) for v in value]
    if isinstance(value, dict):
        return {k: _rewrite_refs(v, key) for k, v in value.items()}
    return value


def _item_questions(questions: dict[str, Any], key: str) -> dict[str, Any]:
    out = {}
    for qid, q in questions.items():
        instr = q["instructions"]
        rewritten = _rewrite_refs(instr, key)
        if rewritten == instr:  # no `item` reference: say which item explicitly
            rewritten = f"About `items.{key}` only: {instr}" if isinstance(instr, str) else {"about": f"`items.{key}` only", "question": instr}
        out[f"{key}.{qid}"] = {**q, "instructions": rewritten}
    return out


def _chunks(keys: list[str], items: dict[str, Any], per_chunk: int, max_chars: int) -> list[list[str]]:
    chunks, cur, size = [], [], 0
    for k in keys:
        n = len(json.dumps(items[k], ensure_ascii=False))
        if cur and (len(cur) >= per_chunk or size + n > max_chars):
            chunks.append(cur)
            cur, size = [], 0
        cur.append(k)
        size += n
    if cur:
        chunks.append(cur)
    return chunks


def _send_chunk(cfg, model, chunk, slot_items, questions, stats) -> dict[str, dict[str, Any]]:
    body = {
        "model": model,
        "state": {"items": {k: slot_items[k] for k in chunk}},
        "questions": {qid: q for k in chunk for qid, q in _item_questions(questions, k).items()},
    }
    try:
        result, latency_ms = send(cfg, body)
    except DecideError as e:
        # A packed request that is too big or malformed for the server: split and retry.
        if e.status in SPLITTABLE_STATUS and len(chunk) > 1:
            mid = len(chunk) // 2
            stats["splits"] += 1
            return {**_send_chunk(cfg, model, chunk[:mid], slot_items, questions, stats),
                    **_send_chunk(cfg, model, chunk[mid:], slot_items, questions, stats)}
        raise
    stats["calls"] += 1
    stats["latency_ms"] += latency_ms
    stats["input_tokens"] += (result.get("usage") or {}).get("input_tokens", 0) or 0
    stats["model"] = result.get("model", model)
    per_item: dict[str, dict[str, Any]] = {k: {} for k in chunk}
    for full_id, ans in result["answers"].items():
        k, _, qid = full_id.partition(".")
        if k in per_item:
            per_item[k][qid] = ans
    for full_id, diag in (result.get("diagnostics") or {}).items():
        k, _, qid = full_id.partition(".")
        stats["diagnostics"].setdefault(k, {})[qid] = diag
    return per_item


def run_batch(
    items: dict[str, Any],
    questions: dict[str, Any],
    model: str | None = None,
    rank_by: str | None = None,
    min_value: float | None = None,
    top_k: int | None = None,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = cfg or config()
    if not isinstance(items, dict) or not items:
        raise DecideError("`items` must be a non-empty object mapping your item id -> item state.")
    for item_id, item in items.items():
        try:
            require_state(item)
        except DecideError:
            raise DecideError(f"item `{item_id}` is empty.") from None
    validate_questions(questions, cfg["max_choice_options"])
    if rank_by is not None:
        if rank_by not in questions or questions[rank_by]["type"] not in {"noul", "score"}:
            raise DecideError("`rank_by` must name a noul or score question in `questions`.")

    # Internal slot keys keep question ids short and free of user-id characters.
    slots = {f"i{n}": item_id for n, item_id in enumerate(items)}
    slot_items = {k: items[v] for k, v in slots.items()}
    per_chunk = max(1, MAX_QUESTIONS // len(questions))
    chunks = _chunks(list(slots), slot_items, per_chunk, cfg["batch_max_state_chars"])

    stats = {"calls": 0, "splits": 0, "latency_ms": 0, "input_tokens": 0, "model": model or cfg["model"], "diagnostics": {}}
    by_slot: dict[str, dict[str, Any]] = {}
    for chunk in chunks:
        by_slot.update(_send_chunk(cfg, model or cfg["model"], chunk, slot_items, questions, stats))

    results, warnings = {}, []
    for k, item_id in slots.items():
        answers = by_slot.get(k, {})
        results[item_id] = answers
        warnings += warnings_for(answers, prefix=f"{item_id}.", diagnostics=stats["diagnostics"].get(k))
        missing = sorted(set(questions) - set(answers))
        if missing:
            warnings.append(f"`{item_id}`: no answer for {missing}")

    out: dict[str, Any] = {
        "model": stats["model"],
        "results": results,
        "usage": {"input_tokens": stats["input_tokens"], "requests": stats["calls"], "splits": stats["splits"]},
        "latency_ms": stats["latency_ms"],
        "warnings": warnings,
    }
    if rank_by:
        ranked = sorted(
            ({"id": i, "value": answer_value(results[i].get(rank_by))} for i in results),
            key=lambda r: -1e9 if r["value"] is None else r["value"],
            reverse=True,
        )
        kept = [r for r in ranked if min_value is None or (r["value"] is not None and r["value"] >= min_value)]
        if min_value is not None and not kept:
            # Vague judgments can push every item under the bar; return the best rather than nothing.
            kept = ranked
            out["warnings"].append(f"No item reached {rank_by} >= {min_value}; returning the top items unfiltered. The question may be too vague.")
        out["ranking"] = kept[:top_k] if top_k else kept
    audit(cfg, {"tool": "decide_batch", "model": out["model"], "question_ids": sorted(questions), "items": len(items),
                "usage": out["usage"], "latency_ms": out["latency_ms"]})
    return out


# ------------------------------------------------------------------ models / warmup


DECISION_MODEL_HINT = re.compile(r"clef|jev|decision|system.?one", re.I)


def _endpoint_models(rcfg: dict[str, Any], requested: str | None = None) -> list[str]:
    if rcfg["backend"] == "cloudflare":
        return ["clef-flash", "clef"]
    headers = {"Accept": "application/json"}
    if rcfg["api_key"]:
        headers["Authorization"] = f"Bearer {rcfg['api_key']}"
    req = urllib.request.Request(f"{rcfg['base_url']}/v1/models", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=rcfg["timeout"]) as resp:
            data = json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        e.close()
        raise DecideError(f"{rcfg['base_url']}/v1/models returned HTTP {e.code}") from None
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        raise DecideError(f"Could not list models at {rcfg['base_url']}/v1/models: {e}") from None
    ids = [m.get("id") for m in data.get("data", []) if isinstance(m, dict) and m.get("id")]
    # Gateways list every LLM they serve; keep the decision models so the answer stays short.
    hinted = [i for i in ids if DECISION_MODEL_HINT.search(i)]
    listed = hinted or ids
    # A gateway may serve a model under a different name (e.g. route id cloudflare.clef
    # served as "clef") and omit the route id from /v1/models entirely. Always include the
    # model this endpoint is configured for so it stays callable.
    if requested and requested not in listed:
        listed = [requested, *listed]
    return listed


def list_models(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or config()
    targets: dict[str, tuple[dict[str, Any], str | None]] = {"(default endpoint)": (cfg, cfg["model"])}
    for name in routes(cfg):
        targets[name] = (route_cfg(cfg, name), name)
    endpoints = []
    for label, (rcfg, requested) in targets.items():
        entry: dict[str, Any] = {"for": label, "backend": rcfg["backend"],
                                 "url": "cloudflare" if rcfg["backend"] == "cloudflare" else rcfg["base_url"]}
        try:
            entry["models"] = _endpoint_models(rcfg, requested)
        except DecideError as e:
            entry["error"] = str(e)
        endpoints.append(entry)
    return {"default": cfg["model"], "escalate_to": cfg["escalate_model"], "routed_models": sorted(routes(cfg)), "endpoints": endpoints}


def prewarm(cfg: dict[str, Any] | None = None) -> bool:
    """One tiny decision for localhost endpoints when DECIDE_PREWARM is on/auto.

    `auto` skips shared remote gateways, which keep their models loaded.
    """
    cfg = cfg or config()
    rcfg = route_cfg(cfg, cfg["model"])
    local = rcfg["backend"] != "cloudflare" and is_local(rcfg["base_url"])
    enabled = cfg["prewarm"] == "on" or (cfg["prewarm"] == "auto" and local)
    if not enabled:
        return False
    try:
        send({**cfg, "timeout": max(cfg["timeout"], 30)},
             {"model": cfg["model"], "state": "warmup", "questions": {"ok": {"type": "noul", "instructions": "Is this a warmup?"}}})
        return True
    except DecideError as e:
        print(f"decide: prewarm failed ({e}); first call may be slow or fail.", file=sys.stderr)
        return False


# ------------------------------------------------------------------------- MCP server

GUIDE = """# Writing decide questions

Use a decision model when the answer is one of a set you can list in advance:
classify, route, triage, pick a tool/handler/file, yes/no checks, rate on a
described scale, pick one value from candidates you already found, rerank,
decide whether to escalate. Do NOT use it for writing, summarising, code,
multi-step reasoning, arithmetic, counting or date comparisons.

- Batch: all independent questions about one state go in ONE `decide` call.
  Many items with the same questions go in ONE `decide_batch` call.
- Full meaning in `instructions`: ids are not read as the question. Reference
  state with backticked paths (`ticket.body`); in decide_batch use `item`
  (`item.title`).
- noul = P(yes); about 0.5 means "can't tell", not "medium". Use score for degree.
- Every choice that might not fit needs an exit such as `"other": null`.
- Multi-label: one noul per label. One narrow judgment per question; say what
  counts ("names the browser and the action that triggers it").
- Score levels describe concrete situations, lowest first, and stand alone.
- Speculative branch questions state their premise ("If this is a refund
  request, which order is it about?").
- Warnings mean rewrite the question, add evidence, or ask the user. Never act
  irreversibly on an unsure answer.
- If decide errors or times out, fall back to your own judgment and say so.

Shapes:
  {"type": "noul",   "instructions": "...", "criteria": {"true": "...", "false": "..."}}
  {"type": "choice", "instructions": "...", "criteria": {"opt_a": "desc", "other": null}}
  {"type": "score",  "instructions": "...", "criteria": ["lowest", "...", "highest"]}
"""

DECIDE_DESCRIPTION = """Ask a decision model (Clef / Jev) typed questions about ONE `state`.
Returns calibrated probabilities per option; it never writes text. Fast (well
under a second when warm).

Use for calibrated rubric checks on a diff, log or screenshot, testing decision
questions you are authoring for application code, or structured classification /
triage where calibrated probabilities matter. Don't call this for everyday
single-item navigation already in your context (like picking which file to read);
for many items (search hits, TODOs, issues, candidates), use decide_batch instead.
Not for writing, reasoning chains, math, counting or dates.

Put ALL independent questions about this state in this one call. Full meaning
goes in `instructions` (ids are not read). noul≈0.5 means "can't tell". Every
choice needs an exit like "other": null. See the decide://guide resource for the full rules.

Models: call decision_models to see what is available on the configured endpoint
(e.g. cloudflare.clef). If the server has an escalation model, unsure answers are
re-asked on it automatically and the result lists them under `escalated`.

Shapes: noul {type, instructions, criteria?: {true, false}};
choice {type, instructions, criteria: {option: description|null}} (2..26);
score {type, instructions, criteria: [lowest, ..., highest]} (2..10)."""

BATCH_DESCRIPTION = """Ask the same typed questions about MANY items in as few requests as
possible (items are packed up to 64 questions per request; oversize packs are
split automatically). Much faster than one decide call per item.

`items` maps your id -> that item's text or JSON. In `instructions`, refer to
the current item as `item` (e.g. `item.title`); each question is rewritten per
item. Returns `results` keyed by your ids.

Rerank or filter: set `rank_by` to a noul or score question id to get a sorted
`ranking`; `min_value` drops items below a bar (if that would drop everything,
the top items come back unfiltered with a warning); `top_k` caps the list.
Check packed answers against a few single `decide` calls before trusting them
for anything important."""

READ_ONLY = {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": True}


@lifespan
async def warm_model(server):
    """Warm localhost models in the background so startup isn't blocked."""
    task = asyncio.create_task(asyncio.to_thread(prewarm))
    try:
        yield {}
    finally:
        task.cancel()


mcp = FastMCP(
    name="decide",
    instructions=(
        "Fast, calibrated judgments from a decision model. Call `decide` to classify, route, "
        "check yes/no or rate one input against options you can list; `decide_batch` for the "
        "same questions over many items or to rerank candidates. Batch questions per call. "
        "Read decide://guide before writing questions."
    ),
    lifespan=warm_model,
)


@mcp.tool(name="decide", description=DECIDE_DESCRIPTION, annotations={"title": "Ask a decision model", **READ_ONLY})
def decide(
    state: Annotated[Any, Field(description="Text or JSON the questions are about. Prefer named JSON fields when there are several parts.")],
    questions: Annotated[dict[str, dict[str, Any]], Field(description="Map of question id -> {type, instructions, criteria}. 1..64 questions.")],
    model: Annotated[str | None, Field(description="Override the default model (e.g. cloudflare.clef, typesafe.jev, clef, clef-flash).")] = None,
    image_paths: Annotated[list[str | None], Field(description="Optional local PNG/JPEG/WebP paths (max 4, <=4 MiB each). Clef only.")] | None = None,
    escalate: Annotated[bool, Field(description="If the server has an escalation model configured, re-ask unsure answers on it once. Set false to compare models.")] = True,
) -> dict[str, Any]:
    try:
        return run_decision(state, questions, model=model, image_paths=image_paths, escalate=escalate)
    except DecideError as e:
        raise ToolError(str(e)) from None


@mcp.tool(name="decide_batch", description=BATCH_DESCRIPTION, annotations={"title": "Ask a decision model about many items", **READ_ONLY})
def decide_batch(
    items: Annotated[dict[str, Any], Field(description="Map of your item id -> item text or JSON.")],
    questions: Annotated[dict[str, dict[str, Any]], Field(description="Questions asked of every item; refer to the item as `item` in instructions.")],
    model: Annotated[str | None, Field(description="Override the default model.")] = None,
    rank_by: Annotated[str | None, Field(description="noul or score question id to sort items by (highest first).")] = None,
    min_value: Annotated[float | None, Field(description="Drop items whose rank_by value is below this.")] = None,
    top_k: Annotated[int | None, Field(description="Keep at most this many ranked items.", ge=1)] = None,
) -> dict[str, Any]:
    try:
        return run_batch(items, questions, model=model, rank_by=rank_by, min_value=min_value, top_k=top_k)
    except DecideError as e:
        raise ToolError(str(e)) from None


@mcp.tool(name="decision_models", description="List decision models available on the configured backend and show the default.",
          annotations={"title": "List decision models", **READ_ONLY})
def decision_models() -> dict[str, Any]:
    try:
        return list_models()
    except DecideError as e:
        raise ToolError(str(e)) from None


@mcp.resource("decide://guide", name="decide_guide", description="Rules for writing decision-model questions.", mime_type="text/markdown")
def decide_guide() -> str:
    return GUIDE


@mcp.prompt(name="design_questions", description="Draft decide questions for a task, then run them.")
def design_questions(task: str) -> str:
    """Draft decide questions for a task.

    Args:
        task: What you want judged, e.g. "triage the open TODOs in src/ by type and urgency".
    """
    return (
        f"Task: {task}\n\n"
        "Design decision-model questions for this task, then run them with the decide tools.\n"
        "1. Say what code or you will do with each answer; drop questions nothing consumes.\n"
        "2. Gather the state (files, logs, text). Keep math, counts and dates out of the questions.\n"
        "3. Write the questions as JSON following the rules below, show them to me briefly, then call "
        "`decide` (one input) or `decide_batch` (many inputs).\n"
        "4. Report answers with probabilities, and list any warnings with a proposed rewrite.\n\n"
        + GUIDE
    )


if __name__ == "__main__":
    mcp.run()
