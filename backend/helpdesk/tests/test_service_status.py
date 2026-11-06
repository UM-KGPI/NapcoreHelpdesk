"""GET /api/v1/status: the "slower than usual" signal behind the frontend banner."""

import tempfile
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from helpdesk.services import service_status


def _fake_proc(root: Path, processes: dict[str, list[str]]) -> Path:
    for pid, argv in processes.items():
        (root / pid).mkdir()
        (root / pid / "cmdline").write_bytes(b"\0".join(arg.encode() for arg in argv) + b"\0")
    (root / "self").mkdir()  # non-numeric entries are skipped
    return root


class RunningIndexSourcesTests(SimpleTestCase):
    def test_finds_index_commands_started_through_manage_py(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = _fake_proc(
                Path(tmp),
                {
                    "101": ["python", "manage.py", "index_datex"],
                    "102": ["/usr/local/bin/python", "/app/manage.py", "index_inspire", "--verbosity", "2"],
                    "103": ["gunicorn", "config.wsgi"],
                    "104": ["sh", "-c", "python manage.py index_datex > /tmp/index_datex.log"],
                },
            )
            self.assertEqual(service_status.running_index_sources(proc), ["DATEX II", "INSPIRE"])

    def test_ignores_the_command_name_outside_manage_py(self):
        # The sh -c wrapper carries the whole command line as one argument; only the python child counts.
        with tempfile.TemporaryDirectory() as tmp:
            proc = _fake_proc(Path(tmp), {"104": ["sh", "-c", "python manage.py index_datex"]})
            self.assertEqual(service_status.running_index_sources(proc), [])

    def test_no_proc_means_no_indexing_signal(self):
        self.assertEqual(service_status.running_index_sources(Path("/nonexistent-proc")), [])


@override_settings(STATUS_BUSY_LOAD_PER_CPU=1.0)
class ServiceStatusEndpointTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def _get(self, *, sources, load):
        with mock.patch.object(service_status, "running_index_sources", return_value=sources), mock.patch.object(
            service_status, "load_per_cpu", return_value=load
        ):
            return self.client.get(reverse("service-status"))

    def test_ok_when_idle(self):
        response = self._get(sources=[], load=0.3)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"state": "ok", "reasons": []})
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_busy_while_indexing(self):
        response = self._get(sources=["DATEX II"], load=0.3)
        self.assertEqual(response.json(), {"state": "busy", "reasons": [{"code": "indexing", "sources": ["DATEX II"]}]})

    def test_busy_under_high_load(self):
        response = self._get(sources=[], load=1.0)
        self.assertEqual(response.json(), {"state": "busy", "reasons": [{"code": "high_load"}]})

    def test_unknown_load_is_not_busy(self):
        self.assertEqual(self._get(sources=[], load=None).json()["state"], "ok")

    def test_public_without_token_or_request_id(self):
        # Polled by every open page, including before the browser has a token.
        response = self._get(sources=[], load=0.0)
        self.assertEqual(response.status_code, 200)
