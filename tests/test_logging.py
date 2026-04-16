from __future__ import annotations

import io
import logging
import unittest
from pathlib import Path
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from stopliga.logging_utils import KeyValueFormatter, configure_logging  # noqa: E402


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

    def test_missing_vpn_client_network_log_includes_docs_url(self) -> None:
        formatter = KeyValueFormatter()
        record = logging.LogRecord(
            name="stopliga.service",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="vpn_client_network_missing",
            args=(),
            exc_info=None,
        )
        record.event = "vpn_client_network_missing"
        record.fields = {
            "docs_url": "https://github.com/jcastro/stopliga/blob/main/README.md#vpn-client-network-required",
        }

        output = formatter.format(record)

        self.assertIn("ERROR No UniFi VPN client network found", output)
        self.assertIn(
            'docs_url="https://github.com/jcastro/stopliga/blob/main/README.md#vpn-client-network-required"',
            output,
        )


class LoggingConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        root = logging.getLogger()
        self._original_handlers = list(root.handlers)
        self._original_level = root.level

    def tearDown(self) -> None:
        root = logging.getLogger()
        root.handlers.clear()
        root.handlers.extend(self._original_handlers)
        root.setLevel(self._original_level)

    def test_logs_are_split_between_stdout_and_stderr_by_severity(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with patch("sys.stdout", stdout), patch("sys.stderr", stderr):
            configure_logging("DEBUG")
            logger = logging.getLogger("stopliga.test")
            logger.info("info_message")
            logger.warning("warning_message")
            logger.error("error_message")

        stdout_output = stdout.getvalue()
        stderr_output = stderr.getvalue()

        self.assertIn("INFO info_message", stdout_output)
        self.assertIn("WARNING warning_message", stdout_output)
        self.assertNotIn("ERROR error_message", stdout_output)

        self.assertIn("ERROR error_message", stderr_output)
        self.assertNotIn("INFO info_message", stderr_output)
        self.assertNotIn("WARNING warning_message", stderr_output)
