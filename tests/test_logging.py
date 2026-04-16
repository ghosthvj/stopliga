from __future__ import annotations

import logging
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from stopliga.logging_utils import KeyValueFormatter  # noqa: E402


class LoggingFormatterTests(unittest.TestCase):
    def test_info_logs_are_human_readable_and_hide_noisy_fields(self) -> None:
        formatter = KeyValueFormatter()
        record = logging.LogRecord(
            name="stopliga.feed",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="feed_loaded",
            args=(),
            exc_info=None,
        )
        record.event = "feed_loaded"
        record.fields = {
            "sync_id": "abc123",
            "is_blocked": True,
            "valid_destinations": 1626,
            "invalid_destinations": 0,
            "feed_hash": "secret-hash",
        }

        output = formatter.format(record)

        self.assertIn("INFO Feed loaded: blocking active", output)
        self.assertIn("valid_destinations=1626", output)
        self.assertNotIn("sync_id=", output)
        self.assertNotIn("feed_hash=", output)
        self.assertNotIn("logger=", output)

    def test_debug_logs_keep_event_and_logger_context(self) -> None:
        formatter = KeyValueFormatter()
        record = logging.LogRecord(
            name="stopliga.feed",
            level=logging.DEBUG,
            pathname=__file__,
            lineno=1,
            msg="feed_loaded",
            args=(),
            exc_info=None,
        )
        record.event = "feed_loaded"
        record.fields = {
            "sync_id": "abc123",
            "is_blocked": True,
        }

        output = formatter.format(record)

        self.assertIn("DEBUG Feed loaded: blocking active", output)
        self.assertIn('logger="stopliga.feed"', output)
        self.assertIn('event="feed_loaded"', output)
        self.assertIn('sync_id="abc123"', output)
