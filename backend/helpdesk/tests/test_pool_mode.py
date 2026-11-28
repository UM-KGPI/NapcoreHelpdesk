"""RETRIEVAL_POOL_MODE: which passages a search covers (the measurement switch of the single-pool plan)."""

from django.test import TestCase, override_settings

from helpdesk.models import SourceChunk
from helpdesk.services import retrieval_gateway as rg
from helpdesk.services.embeddings import build_text_embedding


@override_settings(EMBEDDING_BACKEND="hash")
class PoolModeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for scope in (["NeTEx"], ["SIRI"], ["DATEX II"], ["EU legislation"], ["DATEX II", "SIRI"]):
            SourceChunk.objects.create(
                repository_url="https://example.org/r", commit_sha="x", source_path="a/" + "-".join(scope) + ".md",
                chunk_id="c-" + "-".join(scope), label="a", text="a", standards_scope=scope, quality_score=0.5,
                embedding_vector=build_text_embedding("a"),
            )

    def ids(self, scope):
        return set(SourceChunk.objects.filter(rg._scope_query_filter(scope)).values_list("chunk_id", flat=True))

    def test_default_is_the_scope_of_the_question(self):
        self.assertEqual(rg.pool_mode(), "scoped")
        self.assertEqual(self.ids(None), {"c-NeTEx", "c-SIRI", "c-DATEX II-SIRI"})
        self.assertEqual(self.ids(["NeTEx"]), {"c-NeTEx"})
        self.assertFalse(rg._scope_matches(["DATEX II"], None))
        self.assertFalse(rg._scope_matches(["SIRI"], ["NeTEx"]))

    @override_settings(RETRIEVAL_POOL_MODE="unnamed")
    def test_unnamed_searches_everything_only_without_a_scope(self):
        self.assertEqual(len(self.ids(None)), 5)
        self.assertEqual(self.ids(["NeTEx"]), {"c-NeTEx"})
        self.assertTrue(rg._scope_matches(["DATEX II"], None))
        self.assertFalse(rg._scope_matches(["SIRI"], ["NeTEx"]))

    @override_settings(RETRIEVAL_POOL_MODE="all")
    def test_all_searches_everything_but_a_pass_for_one_source_keeps_its_scope(self):
        self.assertEqual(len(self.ids(None)), 5)
        self.assertEqual(len(self.ids(["NeTEx"])), 5)
        self.assertTrue(rg._scope_matches(["SIRI"], ["NeTEx"]))
        with rg._exact_scope_passes():
            self.assertEqual(self.ids(["NeTEx"]), {"c-NeTEx"})
            self.assertFalse(rg._scope_matches(["SIRI"], ["NeTEx"]))
        self.assertEqual(len(self.ids(["NeTEx"])), 5)

    @override_settings(RETRIEVAL_POOL_MODE="nonsense")
    def test_an_unknown_mode_is_the_default(self):
        self.assertEqual(rg.pool_mode(), "scoped")
        self.assertEqual(self.ids(["NeTEx"]), {"c-NeTEx"})
