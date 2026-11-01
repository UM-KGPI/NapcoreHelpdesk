from __future__ import annotations

import io
import json
import threading
from http.server import HTTPServer
from unittest.mock import patch
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.test import SimpleTestCase, override_settings

from helpdesk import embedding_service
from helpdesk.services import embeddings
from helpdesk.services.embeddings import (
    EMBEDDING_DIMENSION,
    EmbeddingServiceError,
    build_text_embedding,
    build_text_embeddings_batch,
)


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _service_answer(texts_seen: list):
    """Stand-in for the embedding service: records requests, answers 384-value vectors."""

    def fake_urlopen(request, timeout):
        payload = json.loads(request.data)
        texts_seen.append((payload["kind"], payload["texts"]))
        vectors = [[float(i + 1)] + [0.0] * 383 for i, _ in enumerate(payload["texts"])]
        return _FakeResponse(json.dumps({"vectors": vectors}).encode())

    return fake_urlopen


class EmbeddingSwitchTests(SimpleTestCase):
    def test_hash_is_the_default_and_unchanged(self):
        with patch.object(embeddings, "urlopen") as urlopen_mock:
            vector = build_text_embedding("StopPlace with quays")
        urlopen_mock.assert_not_called()
        self.assertEqual(vector, embeddings._hash_embed("StopPlace with quays"))

    @override_settings(EMBEDDING_BACKEND="semantic", EMBEDDING_SERVICE_URL="http://embedder:8090")
    def test_semantic_vectors_come_from_the_service_padded_to_the_column(self):
        seen: list = []
        with patch.object(embeddings, "urlopen", side_effect=_service_answer(seen)):
            vector = build_text_embedding("How does SIRI use NeTEx?", kind="query")

        self.assertEqual(seen, [("query", ["How does SIRI use NeTEx?"])])
        self.assertEqual(len(vector), EMBEDDING_DIMENSION)
        self.assertEqual(vector[0], 1.0)
        self.assertEqual(vector[384:], [0.0] * (EMBEDDING_DIMENSION - 384))

    @override_settings(EMBEDDING_BACKEND="semantic")
    def test_semantic_batches_are_split_into_service_requests(self):
        seen: list = []
        with patch.object(embeddings, "urlopen", side_effect=_service_answer(seen)):
            vectors = build_text_embeddings_batch([f"chunk {i}" for i in range(70)])

        size = embeddings.SERVICE_BATCH_SIZE
        expected = [("passage", size)] * (70 // size) + ([("passage", 70 % size)] if 70 % size else [])
        self.assertEqual([(kind, len(texts)) for kind, texts in seen], expected)
        self.assertEqual(len(vectors), 70)

    @override_settings(EMBEDDING_BACKEND="semantic")
    def test_an_unreachable_service_raises_instead_of_falling_back_to_hash(self):
        with patch.object(embeddings, "urlopen", side_effect=URLError("connection refused")):
            with self.assertRaises(EmbeddingServiceError):
                build_text_embedding("anything")

    @override_settings(EMBEDDING_BACKEND="semantic")
    def test_a_short_answer_from_the_service_is_rejected(self):
        with patch.object(embeddings, "urlopen", return_value=_FakeResponse(b'{"vectors": []}')):
            with self.assertRaises(EmbeddingServiceError):
                build_text_embeddings_batch(["a", "b"])

    @override_settings(EMBEDDING_BACKEND="semantic")
    def test_semantic_inputs_are_the_plain_question_and_the_located_text(self):
        from helpdesk.services.index_builder import build_chunk_embedding_text
        from helpdesk.services.retrieval_gateway import _build_query_embedding_input

        self.assertEqual(
            _build_query_embedding_input(
                question="What is a StopPlace?", hinted_standards={"NeTEx"}, hinted_doc_types={"schema"}
            ),
            "What is a StopPlace?",
        )
        self.assertEqual(
            build_chunk_embedding_text(
                chunk_text="<StopPlace/>",
                doc_type="example",
                chunk_type="xml",
                heading="Stops",
                standards_scope=["NeTEx"],
                repository_url="https://github.com/TransmodelEcosystem/NeTEx",
                source_path="examples/stop.xml",
            ),
            "examples/stop.xml\nStops\n<StopPlace/>",
        )


class _FakeModel:
    def embed(self, texts, batch_size):
        for text in texts:
            yield [float(len(text))] + [0.0] * 383


class EmbeddingServiceTests(SimpleTestCase):
    def setUp(self):
        self.server = HTTPServer(("127.0.0.1", 0), embedding_service.make_handler(_FakeModel()))
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def _post(self, payload):
        request = Request(self.base + "/embed", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read())
        except Exception as exc:  # urllib raises HTTPError for 4xx
            return exc.code, json.loads(exc.read())

    def test_health(self):
        with urlopen(self.base + "/health", timeout=5) as response:
            self.assertEqual(json.loads(response.read())["dimension"], 384)

    def test_embed_applies_the_model_prefix_for_the_kind(self):
        status, body = self._post({"texts": ["abc"], "kind": "query"})

        self.assertEqual(status, 200)
        self.assertEqual(body["vectors"][0][0], float(len("query: abc")))

    def test_bad_requests_are_rejected(self):
        self.assertEqual(self._post({"texts": ["abc"], "kind": "document"})[0], 400)
        self.assertEqual(self._post({"texts": "abc", "kind": "query"})[0], 400)
        self.assertEqual(self._post({"texts": ["x"] * 257, "kind": "passage"})[0], 400)
