from __future__ import annotations

from celery.schedules import crontab
from django.test import SimpleTestCase

from config.beat_schedule import build_beat_schedule


class BeatScheduleTests(SimpleTestCase):
    def test_nothing_is_scheduled_unless_the_refresh_is_enabled(self):
        self.assertEqual(build_beat_schedule(refresh_enabled=False, hour=3, minute=30), {})

    def test_enabled_refresh_runs_daily_at_the_configured_time(self):
        entry = build_beat_schedule(refresh_enabled=True, hour=4, minute=5)["helpdesk-refresh-source-indexes-daily"]
        self.assertEqual(entry["task"], "helpdesk.refresh_source_indexes")
        self.assertEqual(entry["schedule"], crontab(hour=4, minute=5))

    def test_out_of_range_time_is_rejected(self):
        with self.assertRaises(ValueError):
            build_beat_schedule(refresh_enabled=True, hour=24, minute=0)
        with self.assertRaises(ValueError):
            build_beat_schedule(refresh_enabled=False, hour=3, minute=60)
