"""
Semantic embedding service.

One process loads the multilingual embedding model once and answers HTTP requests from the
backend and the worker, so the model (about 0.8 GB in memory) is not loaded in every process.
It runs only when semantic embeddings are switched on (EMBEDDING_BACKEND=semantic); see
docs/production-deployment.md, "Semantic embeddings".

    GET  /health  -> {"status": "ok", "model": ..., "dimension": 384}
    POST /embed   {"texts": [...], "kind": "query" | "passage"} -> {"vectors": [[...], ...]}

Run with: python -m helpdesk.embedding_service  (no Django needed). Its settings are
EMBEDDER_* variables; the older EMBEDDING_MODEL in existing env files belongs to a removed
provider and is ignored.

Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
Crafted by: AI coding agents
Created: 2026-10-26  |  Modified: 2026-11-09
"""

from __future__ import annotations

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

MODEL_NAME = os.environ.get("EMBEDDER_MODEL", "intfloat/multilingual-e5-small")
MODEL_FILE = os.environ.get("EMBEDDER_MODEL_FILE", "onnx/model.onnx")
MODEL_DIMENSION = 384
# The trial measured the first 256 tokens of a chunk to be as good as 512 and twice as fast.
MAX_TOKENS = int(os.environ.get("EMBEDDER_MAX_TOKENS", "256"))
# Larger batches multiply the attention memory; 32 chunks of 512 tokens exceeded 3 GiB.
BATCH_SIZE = int(os.environ.get("EMBEDDER_BATCH_SIZE", "16"))
MAX_TEXTS_PER_REQUEST = 256
# The model requires these prefixes: questions are queries, indexed chunks are passages.
PREFIXES = {"query": "query: ", "passage": "passage: "}

logger = logging.getLogger("embedding_service")


def cpu_threads() -> int | None:
    """Threads for the model: EMBEDDER_THREADS, else the container's CPU limit (cgroup cpu.max), else None
    (the runtime's default, one per host core).

    The runtime's default counts the host's cores, not the container's limit: on prod (cpus 2 on a larger
    host) every request was throttled, 1.1-1.3 s for a short question (12 ms on the dev stack). Under a
    1-CPU limit on a 4-core machine, a definition passage took 576 ms with the default and 200 ms with one
    thread (2026-11-09)."""
    configured = os.environ.get("EMBEDDER_THREADS", "").strip()
    if configured:
        return max(1, int(configured))
    try:
        quota, period = open("/sys/fs/cgroup/cpu.max").read().split()[:2]
    except (OSError, ValueError):
        return None
    if quota == "max":
        return None
    import math

    return max(1, math.ceil(int(quota) / int(period)))


def load_model():
    """Load the model from the cache directory, downloading it once if absent."""
    from fastembed import TextEmbedding
    from fastembed.common.model_description import ModelSource, PoolingType

    try:
        TextEmbedding.add_custom_model(
            model=MODEL_NAME,
            pooling=PoolingType.MEAN,
            normalization=True,
            sources=ModelSource(hf=MODEL_NAME),
            dim=MODEL_DIMENSION,
            model_file=MODEL_FILE,
        )
    except ValueError:
        pass  # already registered in this process
    threads = cpu_threads()
    logger.info("embedding model threads: %s", threads or "runtime default")
    model = TextEmbedding(MODEL_NAME, cache_dir=os.environ.get("EMBEDDER_MODEL_DIR", "/models"), threads=threads)
    model.model.tokenizer.enable_truncation(max_length=MAX_TOKENS)
    return model


def embed_texts(model, texts: list[str], kind: str) -> list[list[float]]:
    prefix = PREFIXES[kind]
    return [[float(x) for x in vector] for vector in model.embed([prefix + text for text in texts], batch_size=BATCH_SIZE)]


def make_handler(model):
    class Handler(BaseHTTPRequestHandler):
        def _reply(self, status: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            if self.path == "/health":
                self._reply(200, {"status": "ok", "model": MODEL_NAME, "dimension": MODEL_DIMENSION})
            else:
                self._reply(404, {"error": "not found"})

        def do_POST(self):  # noqa: N802
            if self.path != "/embed":
                self._reply(404, {"error": "not found"})
                return
            try:
                request = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                texts, kind = request.get("texts"), request.get("kind")
                if kind not in PREFIXES or not isinstance(texts, list) or not all(isinstance(t, str) for t in texts):
                    raise ValueError('expected {"texts": [str, ...], "kind": "query" | "passage"}')
                if len(texts) > MAX_TEXTS_PER_REQUEST:
                    raise ValueError(f"at most {MAX_TEXTS_PER_REQUEST} texts per request")
            except (ValueError, json.JSONDecodeError) as exc:
                self._reply(400, {"error": str(exc)})
                return
            self._reply(200, {"vectors": embed_texts(model, texts, kind)})

        def log_message(self, fmt, *args):
            logger.info("%s %s", self.address_string(), fmt % args)

    return Handler


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    port = int(os.environ.get("EMBEDDER_PORT", "8090"))
    model = load_model()
    logger.info("model %s loaded; listening on port %s", MODEL_NAME, port)
    # One request at a time: the model already uses every CPU it is given, and parallel
    # requests would only multiply its memory.
    HTTPServer(("0.0.0.0", port), make_handler(model)).serve_forever()


if __name__ == "__main__":
    main()
