from __future__ import annotations

from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from helpdesk.management.commands.reembed_chunks import swap_vectors, vector_kind
from helpdesk.models import SourceChunk
from helpdesk.services import embeddings
from helpdesk.tests.test_embedding_service import _service_answer


def _chunk(index: int) -> SourceChunk:
    text = f"<StopPlace id='{index}'/> with quays"
    return SourceChunk.objects.create(
        chunk_id=f"src-{index}",
        repository_url="https://github.com/TransmodelEcosystem/NeTEx",
        commit_sha="abc",
        source_path=f"examples/stop{index}.xml",
        heading="Stops",
        text=text,
        standards_scope=["NeTEx"],
        embedding_vector=embeddings._hash_embed(text),
    )


@override_settings(EMBEDDING_BACKEND="hash", EMBEDDING_SERVICE_URL="http://embedder:8090")
class ReembedChunksTests(TestCase):
    def setUp(self):
        self.chunks = [_chunk(i) for i in range(3)]
        self.hash_vectors = {c.pk: list(c.embedding_vector) for c in self.chunks}

    def _fill(self, *args):
        seen: list = []
        with patch.object(embeddings, "urlopen", side_effect=_service_answer(seen)):
            call_command("reembed_chunks", *args, stdout=StringIO())
        return seen

    def test_fill_embeds_the_other_backend_and_keeps_the_vectors_in_use(self):
        seen = self._fill()

        self.assertEqual([kind for kind, _ in seen], ["passage"])
        self.assertIn("examples/stop0.xml\nStops\n<StopPlace id='0'/> with quays", seen[0][1])
        for chunk in SourceChunk.objects.all():
            self.assertEqual(vector_kind(chunk.alternate_vector), "semantic")
            self.assertEqual(list(chunk.embedding_vector), self.hash_vectors[chunk.pk])

    def test_a_rerun_embeds_only_chunks_without_an_alternate_vector(self):
        self._fill()
        SourceChunk.objects.filter(pk=self.chunks[1].pk).update(alternate_vector=None)

        seen = self._fill()

        self.assertEqual([len(texts) for _, texts in seen], [1])

    def test_swap_switches_the_columns_and_swapping_again_restores_them(self):
        self._fill("--swap")
        for chunk in SourceChunk.objects.all():
            self.assertEqual(vector_kind(chunk.embedding_vector), "semantic")
            self.assertEqual(list(chunk.alternate_vector), self.hash_vectors[chunk.pk])

        swap_vectors()
        for chunk in SourceChunk.objects.all():
            self.assertEqual(list(chunk.embedding_vector), self.hash_vectors[chunk.pk])
            self.assertEqual(vector_kind(chunk.alternate_vector), "semantic")

    def test_swap_refuses_while_a_chunk_has_no_alternate_vector(self):
        self._fill()
        _chunk(9)

        with self.assertRaises(CommandError):
            swap_vectors()
        self.assertEqual(list(SourceChunk.objects.get(pk=self.chunks[0].pk).embedding_vector), self.hash_vectors[self.chunks[0].pk])

    def test_status_reports_the_counts(self):
        out = StringIO()
        call_command("reembed_chunks", "--status", stdout=out)

        self.assertIn("3 chunks, 0 with an alternate vector, 3 without", out.getvalue())
