from __future__ import annotations

from django.test import SimpleTestCase

from helpdesk.services import llm_model_recovery
from helpdesk.services.llm_model_recovery import (
    extract_authorized_model,
    get_cached_correction,
    remember_correction,
)


class LLMModelRecoveryTests(SimpleTestCase):
    def setUp(self):
        # The cache is a module-level dict shared across tests; reset it so
        # tests don't leak state into each other.
        llm_model_recovery._corrected_model_cache.clear()

    def test_extract_authorized_model_parses_litellm_error_body(self):
        error_body = (
            '{"error":{"message":"key not allowed to access model. This key can only '
            "access models=['nvidia/Qwen3.6-35B-A3B-NVFP4']. Tried to access "
            'qwen36-35b-a3b","type":"key_model_access_denied","param":"model","code":"403"}}'
        )

        self.assertEqual(
            extract_authorized_model(error_body),
            "nvidia/Qwen3.6-35B-A3B-NVFP4",
        )

    def test_extract_authorized_model_returns_none_for_unrelated_error(self):
        self.assertIsNone(extract_authorized_model('{"error":{"message":"rate limited"}}'))
        self.assertIsNone(extract_authorized_model(""))
        self.assertIsNone(extract_authorized_model(None))

    def test_cache_roundtrip(self):
        self.assertIsNone(get_cached_correction("https://litellm.lhrs.si/v1", "qwen36-35b-a3b"))

        remember_correction(
            api_base_url="https://litellm.lhrs.si/v1",
            configured_model="qwen36-35b-a3b",
            corrected_model="nvidia/Qwen3.6-35B-A3B-NVFP4",
            source="test",
        )

        self.assertEqual(
            get_cached_correction("https://litellm.lhrs.si/v1", "qwen36-35b-a3b"),
            "nvidia/Qwen3.6-35B-A3B-NVFP4",
        )
        # A different base URL or a different configured model must not hit the same entry.
        self.assertIsNone(get_cached_correction("https://other.example/v1", "qwen36-35b-a3b"))
        self.assertIsNone(get_cached_correction("https://litellm.lhrs.si/v1", "some-other-model"))
