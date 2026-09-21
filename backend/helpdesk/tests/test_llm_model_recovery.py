from __future__ import annotations

import io
import json
from unittest.mock import patch
from urllib import error

from django.test import SimpleTestCase

from helpdesk.services import llm_model_recovery
from helpdesk.services.llm_model_recovery import (
    check_gateway_models,
    extract_authorized_model,
    get_all_corrections,
    get_cached_correction,
    remember_correction,
    resolve_effective_model,
)


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class LLMModelRecoveryTests(SimpleTestCase):
    def setUp(self):
        # The cache is a module-level dict shared across tests; reset it so
        # tests don't leak state into each other.
        llm_model_recovery._corrected_model_cache.clear()
        llm_model_recovery._verified_ok_cache.clear()

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

    def test_get_all_corrections_returns_snapshot(self):
        self.assertEqual(get_all_corrections(), {})

        remember_correction(
            api_base_url="https://litellm.lhrs.si/v1",
            configured_model="qwen36-35b-a3b",
            corrected_model="nvidia/Qwen3.6-35B-A3B-NVFP4",
            source="test",
        )

        snapshot = get_all_corrections()
        self.assertEqual(
            snapshot,
            {("https://litellm.lhrs.si/v1", "qwen36-35b-a3b"): "nvidia/Qwen3.6-35B-A3B-NVFP4"},
        )
        # Mutating the returned dict must not affect the module's cache.
        snapshot["injected"] = "value"
        self.assertNotIn("injected", get_all_corrections())


class CheckGatewayModelsTests(SimpleTestCase):
    @patch("helpdesk.services.llm_model_recovery.request.urlopen")
    def test_reports_reachable_with_model_ids_on_success(self, urlopen_mock):
        urlopen_mock.return_value = _FakeResponse(
            {"data": [{"id": "nvidia/Qwen3.6-35B-A3B-NVFP4"}, {"id": "gpt-4o-mini"}]}
        )

        result = check_gateway_models(
            api_base_url="https://litellm.lhrs.si/v1",
            api_key="sk-test",
            verify_ssl=True,
            ca_bundle="",
        )

        self.assertEqual(
            result,
            {
                "reachable": True,
                "modelIds": ["nvidia/Qwen3.6-35B-A3B-NVFP4", "gpt-4o-mini"],
                "error": None,
            },
        )
        called_request = urlopen_mock.call_args.args[0]
        self.assertEqual(called_request.full_url, "https://litellm.lhrs.si/v1/models")
        self.assertEqual(called_request.get_header("Authorization"), "Bearer sk-test")

    @patch("helpdesk.services.llm_model_recovery.request.urlopen")
    def test_reports_unreachable_on_http_error(self, urlopen_mock):
        urlopen_mock.side_effect = error.HTTPError(
            url="https://litellm.lhrs.si/v1/models",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=io.BytesIO(b'{"error":{"message":"invalid key"}}'),
        )

        result = check_gateway_models(
            api_base_url="https://litellm.lhrs.si/v1",
            api_key="sk-bad",
            verify_ssl=True,
            ca_bundle="",
        )

        self.assertFalse(result["reachable"])
        self.assertIsNone(result["modelIds"])
        self.assertIn("HTTP 401", result["error"])

    @patch("helpdesk.services.llm_model_recovery.request.urlopen")
    def test_reports_unreachable_on_network_error(self, urlopen_mock):
        urlopen_mock.side_effect = error.URLError("connection refused")

        result = check_gateway_models(
            api_base_url="https://litellm.lhrs.si/v1",
            api_key="sk-test",
            verify_ssl=True,
            ca_bundle="",
        )

        self.assertFalse(result["reachable"])
        self.assertIsNone(result["modelIds"])
        self.assertIn("connection refused", result["error"])


class ResolveEffectiveModelTests(SimpleTestCase):
    def setUp(self):
        llm_model_recovery._corrected_model_cache.clear()
        llm_model_recovery._verified_ok_cache.clear()

    @patch("helpdesk.services.llm_model_recovery.check_gateway_models")
    def test_returns_configured_model_and_caches_when_gateway_confirms_it(self, probe_mock):
        probe_mock.return_value = {
            "reachable": True,
            "modelIds": ["nvidia/Qwen3.6-35B-A3B-NVFP4"],
            "error": None,
        }

        model = resolve_effective_model(
            api_base_url="https://litellm.lhrs.si/v1",
            api_key="sk-test",
            configured_model="nvidia/Qwen3.6-35B-A3B-NVFP4",
            verify_ssl=True,
            ca_bundle="",
            source="answer_generation",
        )

        self.assertEqual(model, "nvidia/Qwen3.6-35B-A3B-NVFP4")
        self.assertIsNone(get_cached_correction("https://litellm.lhrs.si/v1", "nvidia/Qwen3.6-35B-A3B-NVFP4"))

        # A second call must not probe the gateway again -- confirmed models are cached too.
        probe_mock.reset_mock()
        resolve_effective_model(
            api_base_url="https://litellm.lhrs.si/v1",
            api_key="sk-test",
            configured_model="nvidia/Qwen3.6-35B-A3B-NVFP4",
            verify_ssl=True,
            ca_bundle="",
            source="answer_generation",
        )
        probe_mock.assert_not_called()

    @patch("helpdesk.services.llm_model_recovery.check_gateway_models")
    def test_preflight_corrects_a_single_drifted_model(self, probe_mock):
        probe_mock.return_value = {
            "reachable": True,
            "modelIds": ["nvidia/Qwen3.6-35B-A3B-NVFP4"],
            "error": None,
        }

        model = resolve_effective_model(
            api_base_url="https://litellm.lhrs.si/v1",
            api_key="sk-test",
            configured_model="qwen36-35b-a3b",
            verify_ssl=True,
            ca_bundle="",
            source="answer_generation",
        )

        self.assertEqual(model, "nvidia/Qwen3.6-35B-A3B-NVFP4")
        self.assertEqual(
            get_cached_correction("https://litellm.lhrs.si/v1", "qwen36-35b-a3b"),
            "nvidia/Qwen3.6-35B-A3B-NVFP4",
        )

    @patch("helpdesk.services.llm_model_recovery.check_gateway_models")
    def test_ambiguous_allowlist_falls_through_to_configured_model(self, probe_mock):
        probe_mock.return_value = {
            "reachable": True,
            "modelIds": ["model-a", "model-b"],
            "error": None,
        }

        model = resolve_effective_model(
            api_base_url="https://litellm.lhrs.si/v1",
            api_key="sk-test",
            configured_model="qwen36-35b-a3b",
            verify_ssl=True,
            ca_bundle="",
            source="answer_generation",
        )

        self.assertEqual(model, "qwen36-35b-a3b")
        self.assertIsNone(get_cached_correction("https://litellm.lhrs.si/v1", "qwen36-35b-a3b"))

    @patch("helpdesk.services.llm_model_recovery.check_gateway_models")
    def test_unreachable_gateway_falls_through_to_configured_model_without_caching(self, probe_mock):
        probe_mock.return_value = {"reachable": False, "modelIds": None, "error": "connection refused"}

        model = resolve_effective_model(
            api_base_url="https://litellm.lhrs.si/v1",
            api_key="sk-test",
            configured_model="qwen36-35b-a3b",
            verify_ssl=True,
            ca_bundle="",
            source="answer_generation",
        )

        self.assertEqual(model, "qwen36-35b-a3b")
        self.assertIsNone(get_cached_correction("https://litellm.lhrs.si/v1", "qwen36-35b-a3b"))

    def test_existing_cached_correction_skips_the_probe_entirely(self):
        remember_correction(
            api_base_url="https://litellm.lhrs.si/v1",
            configured_model="qwen36-35b-a3b",
            corrected_model="nvidia/Qwen3.6-35B-A3B-NVFP4",
            source="test",
        )

        with patch("helpdesk.services.llm_model_recovery.check_gateway_models") as probe_mock:
            model = resolve_effective_model(
                api_base_url="https://litellm.lhrs.si/v1",
                api_key="sk-test",
                configured_model="qwen36-35b-a3b",
                verify_ssl=True,
                ca_bundle="",
                source="answer_generation",
            )

        self.assertEqual(model, "nvidia/Qwen3.6-35B-A3B-NVFP4")
        probe_mock.assert_not_called()
