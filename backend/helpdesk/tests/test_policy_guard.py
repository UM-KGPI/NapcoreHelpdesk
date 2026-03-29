from __future__ import annotations

from django.test import SimpleTestCase

from helpdesk.services.policy_guard import evaluate_policy


class PolicyGuardTests(SimpleTestCase):
    """Validate repository allow-list behavior for citation URLs."""

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