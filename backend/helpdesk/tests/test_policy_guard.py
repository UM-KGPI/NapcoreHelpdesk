from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from helpdesk.services.policy_guard import evaluate_policy


class PolicyGuardTests(SimpleTestCase):
    """Validate repository allow-list behavior for citation URLs."""

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/NeTEx-CEN/NeTEx"})
    def test_allows_github_blob_url_from_approved_repository(self):
        result = evaluate_policy(
            answer_text="Grounded answer.",
            citations=[
                {
                    "repositoryUrl": (
                        "https://github.com/NeTEx-CEN/NeTEx/"
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

    @override_settings(ALLOWED_SOURCE_REPOSITORIES={"https://github.com/NeTEx-CEN/NeTEx"})
    def test_blocks_unapproved_repository(self):
        result = evaluate_policy(
            answer_text="Grounded answer.",
            citations=[
                {
                    "repositoryUrl": (
                        "https://github.com/NeTEx-CEN/test-Profile-Documentation/"
                        "blob/abc123/docs/example.md"
                    )
                }
            ],
        )

        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "POLICY_BLOCK")