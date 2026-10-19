from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from helpdesk.services.ontology_evidence import TRANSMODEL_SOURCE_URL
from helpdesk.services.policy_guard import evaluate_policy


class PolicyGuardTests(SimpleTestCase):
    """Validate repository allow-list behavior for citation URLs."""

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/NeTEx"})
    def test_allows_github_blob_url_from_approved_repository(self):
        result = evaluate_policy(
            answer_text="Grounded answer.",
            citations=[
                {
                    "repositoryUrl": (
                        "https://github.com/TransmodelEcosystem/NeTEx/"
                        "blob/de021e8/examples/functions/stopPlace/sample.xml"
                    )
                }
            ],
        )

        self.assertTrue(result["allowed"])
        self.assertIsNone(result["reason"])

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/OpRa-CEN/OpRa"})
    def test_allows_github_blob_url_from_configured_opra_repository(self):
        result = evaluate_policy(
            answer_text="Grounded answer.",
            citations=[
                {
                    "repositoryUrl": (
                        "https://github.com/OpRa-CEN/OpRa/"
                        "blob/abc123/docs/lj-number-of-late-journeys-model-summary.md"
                    )
                }
            ],
        )

        self.assertTrue(result["allowed"])
        self.assertIsNone(result["reason"])

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/SIRI-CEN/SIRI"})
    def test_allows_siri_citation_whichever_spelling_the_allow_list_uses(self):
        for repository_url in ("https://github.com/TransmodelEcosystem/SIRI", "https://github.com/SIRI-CEN/SIRI"):
            result = evaluate_policy(
                answer_text="Grounded answer.",
                citations=[{"repositoryUrl": f"{repository_url}/blob/abc123/xsd/siri.xsd"}],
            )
            self.assertTrue(result["allowed"], repository_url)

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/NeTEx"})
    def test_blocks_unapproved_repository(self):
        result = evaluate_policy(
            answer_text="Grounded answer.",
            citations=[
                {
                    "repositoryUrl": (
                        "https://github.com/SIRI-CEN/SIRI/"
                        "blob/abc123/docs/example.md"
                    )
                }
            ],
        )

        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "POLICY_BLOCK")

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/NeTEx"})
    def test_allows_generated_transmodel_ontology_citation(self):
        result = evaluate_policy(
            answer_text="Grounded answer.",
            citations=[
                {"repositoryUrl": TRANSMODEL_SOURCE_URL},
                {"repositoryUrl": TRANSMODEL_SOURCE_URL + "#STOP_PLACE"},
                {"repositoryUrl": "https://github.com/TransmodelEcosystem/NeTEx/blob/v2.0/xsd/a.xsd"},
            ],
        )

        self.assertTrue(result["allowed"])

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/TransmodelEcosystem/NeTEx"})
    def test_still_blocks_other_files_from_the_project_repository(self):
        result = evaluate_policy(
            answer_text="Grounded answer.",
            citations=[
                {"repositoryUrl": "https://github.com/UM-KGPI/NapcoreHelpdesk/blob/main/docs/ontology/standards/netex.ttl"}
            ],
        )

        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "POLICY_BLOCK")
