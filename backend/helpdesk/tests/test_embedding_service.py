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


def _word_tokenizer(cut: int):
    """A small real tokenizer shaped like the model's: words, special tokens around the text, a cut and padding."""
    from tokenizers import Tokenizer, models, pre_tokenizers, processors

    vocab = {"<pad>": 0, "<s>": 1, "</s>": 2, "<unk>": 3, "passage:": 4, "query:": 5, "a": 6, "b": 7}
    tokenizer = Tokenizer(models.WordLevel(vocab, unk_token="<unk>"))
    tokenizer.pre_tokenizer = pre_tokenizers.WhitespaceSplit()
    tokenizer.post_processor = processors.TemplateProcessing(single="<s> $A </s>", special_tokens=[("<s>", 1), ("</s>", 2)])
    tokenizer.enable_truncation(max_length=cut)
    tokenizer.enable_padding(pad_id=0, pad_token="<pad>")
    return tokenizer


class _FakeTokenizedModel(_FakeModel):
    """A stand-in with the attribute path of fastembed's TextEmbedding to its tokenizer."""

    def __init__(self, tokenizer):
        self.model = type("Inner", (), {"tokenizer": tokenizer})()


class _StubCounter:
    """Counts characters, so a test sees exactly which text was counted."""

    def encode_batch(self, texts):
        return [type("Encoding", (), {"ids": list(text)})() for text in texts]


class TokenCountServiceTests(SimpleTestCase):
    def _serve(self, model, counter=None):
        server = HTTPServer(("127.0.0.1", 0), embedding_service.make_handler(model, counter))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return f"http://127.0.0.1:{server.server_port}"

    def _post(self, base, payload):
        request = Request(base + "/count", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read())
        except Exception as exc:  # urllib raises HTTPError for 4xx
            return exc.code, json.loads(exc.read())

    def test_count_is_of_the_text_with_the_prefix_of_its_kind(self):
        base = self._serve(_FakeModel(), _StubCounter())

        self.assertEqual(
            self._post(base, {"texts": ["abc", ""], "kind": "passage"}),
            (200, {"counts": [len("passage: abc"), len("passage: ")], "maxTokens": embedding_service.MAX_TOKENS}),
        )
        self.assertEqual(self._post(base, {"texts": ["abc"], "kind": "query"})[1]["counts"], [len("query: abc")])

    def test_count_rejects_what_embed_rejects(self):
        base = self._serve(_FakeModel(), _StubCounter())

        self.assertEqual(self._post(base, {"texts": ["abc"], "kind": "document"})[0], 400)
        self.assertEqual(self._post(base, {"texts": ["x"] * 257, "kind": "passage"})[0], 400)

    def test_without_a_tokenizer_there_is_no_count(self):
        self.assertEqual(self._post(self._serve(_FakeModel()), {"texts": ["a"], "kind": "passage"})[0], 404)

    def test_the_count_includes_special_tokens_and_is_not_cut(self):
        try:
            tokenizer = _word_tokenizer(cut=4)
        except ImportError:
            self.skipTest("tokenizers is not installed (it comes with fastembed)")
        base = self._serve(_FakeTokenizedModel(tokenizer))

        # <s> passage: a b a b a </s>: 8 tokens, above the cut of 4; <s> passage: </s>: 3.
        self.assertEqual(self._post(base, {"texts": ["a b a b a", ""], "kind": "passage"})[1]["counts"], [8, 3])
        # The model's own tokenizer still cuts and pads: what it embeds is unchanged.
        encodings = tokenizer.encode_batch(["passage: a b a b a", "passage: "])
        self.assertEqual([len(e.ids) for e in encodings], [4, 4])
        self.assertEqual([sum(e.attention_mask) for e in encodings], [4, 3])


class TokenCountClientTests(SimpleTestCase):
    def _answer(self, seen, max_tokens=256, drop=0):
        def fake_urlopen(request, timeout):
            payload = json.loads(request.data)
            seen.append((request.full_url, payload["kind"], payload["texts"]))
            counts = [len(text) for text in payload["texts"]][drop:]
            return _FakeResponse(json.dumps({"counts": counts, "maxTokens": max_tokens}).encode())

        return fake_urlopen

    @override_settings(EMBEDDING_SERVICE_URL="http://embedder:8090/")
    def test_passages_are_counted_as_the_indexer_embeds_them(self):
        seen = []
        with patch.object(embeddings, "urlopen", self._answer(seen)):
            counts, cut = embeddings.count_passage_tokens([("examples/stop.xml", "Stops", "<StopPlace/>"), ("README.md", "", "x")])

        text = embeddings.passage_text("examples/stop.xml", "Stops", "<StopPlace/>")
        self.assertEqual(seen, [("http://embedder:8090/count", "passage", [text, "README.md\n\nx"])])
        self.assertEqual((counts, cut), ([len(text), len("README.md\n\nx")], 256))

    def test_counts_are_asked_in_batches_the_service_accepts(self):
        seen = []
        with patch.object(embeddings, "urlopen", self._answer(seen)):
            counts, _ = embeddings.count_embedded_tokens(["a"] * 600, "passage")

        self.assertEqual([len(texts) for _, _, texts in seen], [256, 256, 88])
        self.assertEqual(len(counts), 600)

    def test_a_service_that_cannot_count_raises(self):
        with patch.object(embeddings, "urlopen", side_effect=URLError("404 not found")):
            with self.assertRaises(EmbeddingServiceError):
                embeddings.count_embedded_tokens(["a"])
        with patch.object(embeddings, "urlopen", self._answer([], drop=1)):
            with self.assertRaises(EmbeddingServiceError):
                embeddings.count_embedded_tokens(["a", "b"])
