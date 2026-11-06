"""GET /api/v1/status: the "slower than usual" signal behind the frontend banner."""

import os
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
    def _sources(self, processes: dict[str, list[str]], markers: tuple[str, ...] = ()) -> list[str]:
        with tempfile.TemporaryDirectory() as proc_tmp, tempfile.TemporaryDirectory() as marker_tmp:
            for pid in markers:
                (Path(marker_tmp) / f"{service_status.MARKER_PREFIX}{pid}").write_text("")
            return service_status.running_index_sources(_fake_proc(Path(proc_tmp), processes), Path(marker_tmp))

    def test_reports_index_commands_that_are_embedding(self):
        sources = self._sources(
            {
                "101": ["python", "manage.py", "index_datex"],
                "102": ["/usr/local/bin/python", "/app/manage.py", "index_inspire", "--verbosity", "2"],
                "103": ["gunicorn", "config.wsgi"],
            },
            markers=("101", "102"),
        )
        self.assertEqual(sources, ["DATEX II", "INSPIRE"])

    def test_deploy_index_commands_that_only_compare_hashes_are_not_reported(self):
        # deploy.sh runs them on every deploy; with nothing changed they never embed.
        processes = {
            "101": ["python", "manage.py", "index_datex"],
            "102": ["python", "manage.py", "index_regulations"],
            "103": ["python", "manage.py", "index_napcore_site"],
        }
        self.assertEqual(self._sources(processes), [])
        self.assertEqual(self._sources(processes, markers=("103",)), ["napcore.eu"])

    def test_a_marker_of_another_process_does_not_count(self):
        self.assertEqual(self._sources({"101": ["python", "manage.py", "index_datex"]}, markers=("999",)), [])

    def test_commands_that_always_embed_need_no_marker(self):
        self.assertEqual(self._sources({"104": ["python", "manage.py", "reembed_chunks", "--fill"]}), ["search index"])

    def test_ignores_the_command_name_outside_manage_py(self):
        # The sh -c wrapper carries the whole command line as one argument; only the python child counts.
        self.assertEqual(self._sources({"105": ["sh", "-c", "python manage.py index_datex"]}, markers=("105",)), [])

    def test_no_proc_means_no_indexing_signal(self):
        self.assertEqual(service_status.running_index_sources(Path("/nonexistent-proc")), [])


class MarkEmbeddingTests(SimpleTestCase):
    def test_writes_one_marker_for_this_process_and_removes_it_at_exit(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(service_status, "MARKER_DIR", Path(tmp)), \
                mock.patch.object(service_status.atexit, "register") as register:
            service_status.mark_embedding()
            service_status.mark_embedding()
            marker = Path(tmp) / f"{service_status.MARKER_PREFIX}{os.getpid()}"
            self.assertTrue(marker.exists())
            register.assert_called_once()
            (cleanup,), kwargs = register.call_args
            self.assertEqual((cleanup.__self__, cleanup.__name__, kwargs), (marker, "unlink", {"missing_ok": True}))

    def test_an_unwritable_marker_never_fails_the_index_run(self):
        with mock.patch.object(service_status, "MARKER_DIR", Path("/nonexistent-dir")):
            service_status.mark_embedding()  # no exception


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
