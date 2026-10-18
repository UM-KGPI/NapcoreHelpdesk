from __future__ import annotations

from django.test import SimpleTestCase

from helpdesk.services.repository_urls import canonical_repository_url

SIRI = "https://github.com/TransmodelEcosystem/SIRI"


class CanonicalRepositoryUrlTests(SimpleTestCase):
    def test_siri_aliases_map_to_the_main_source(self):
        for spelling in (
            SIRI,
            "https://github.com/SIRI-CEN/SIRI",
            "https://github.com/siri-cen/siri/",
            "https://github.com/transmodelecosystem/siri",
        ):
            self.assertEqual(canonical_repository_url(spelling), SIRI, spelling)

    def test_netex_aliases_map_to_transmodel_ecosystem(self):
        self.assertEqual(
            canonical_repository_url("https://github.com/NeTEx-CEN/NeTEx"),
            "https://github.com/TransmodelEcosystem/NeTEx",
        )

    def test_file_urls_reduce_to_the_repository_root(self):
        self.assertEqual(
            canonical_repository_url("https://github.com/SIRI-CEN/SIRI/blob/abc123/xsd/siri.xsd"),
            SIRI,
        )

    def test_unknown_repositories_keep_their_own_spelling(self):
        self.assertEqual(
            canonical_repository_url("https://github.com/OpRa-CEN/OpRa/"), "https://github.com/OpRa-CEN/OpRa"
        )
        self.assertEqual(canonical_repository_url("https://example.org/repo/"), "https://example.org/repo")
        self.assertEqual(canonical_repository_url("not a url/"), "not a url")
