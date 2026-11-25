"""Baseline-compatible checks distilled from the round-six regression replay."""
from types import SimpleNamespace
import unittest

from cedar.client import Client
from cedar.transport import Transport


class Adapter:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        status, headers = next(self.responses)
        return SimpleNamespace(status=status, location=None, headers=headers)


class UnchangedContract(unittest.TestCase):
    def test_successful_post_uses_one_attempt_and_does_not_wait(self):
        adapter = Adapter([(200, {"Retry-After": "1"})])
        waits = []
        client = Client(Transport(adapter, sleeper=waits.append))
        self.assertEqual(client.submit("https://one.fixture.invalid").status, 200)
        self.assertEqual(len(adapter.calls), 1)
        self.assertEqual(waits, [])

    def test_invalid_429_retry_after_is_ignored_without_disabling_get_retry(self):
        for supplied in ("9", "bad", "-1", ""):
            with self.subTest(header=supplied):
                adapter = Adapter([(429, {"Retry-After": supplied}), (200, {})])
                waits = []
                client = Client(Transport(adapter, sleeper=waits.append))
                self.assertEqual(client.fetch("https://one.fixture.invalid").status, 200)
                self.assertEqual(len(adapter.calls), 2)
                self.assertEqual(waits, [])
