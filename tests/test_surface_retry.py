"""Surface checks must tolerate transient connection failures.

A connection reset against GitHub Pages is common and is not evidence the
surface is down. Reporting a single failure as an outage is a false positive,
and a false positive in a status document teaches the reader to skip it.
"""

from __future__ import annotations

import httpx
import pytest

from auditor.state import SURFACE_ATTEMPTS, check_surface


class FakeResponse:
    def __init__(self, status_code: int, text: str) -> None:
        self.status_code = status_code
        self.text = text


class FlakyClient:
    """Fails the first `fail_times` calls, then succeeds."""

    def __init__(self, fail_times: int, body: str = "<html>ok</html>") -> None:
        self.fail_times = fail_times
        self.body = body
        self.calls = 0

    def get(self, url, headers=None):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise httpx.ConnectError("connection reset")
        return FakeResponse(200, self.body)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    """Retry backoff should not slow the test suite."""
    monkeypatch.setattr("time.sleep", lambda _: None)


def test_succeeds_on_first_attempt() -> None:
    client = FlakyClient(fail_times=0)
    result = check_surface("https://example.com/", client=client)
    assert result.healthy
    assert client.calls == 1


def test_recovers_after_one_failure() -> None:
    client = FlakyClient(fail_times=1)
    result = check_surface("https://example.com/", client=client)
    assert result.healthy
    assert client.calls == 2


def test_recovers_on_final_attempt() -> None:
    client = FlakyClient(fail_times=SURFACE_ATTEMPTS - 1)
    result = check_surface("https://example.com/", client=client)
    assert result.healthy


def test_reports_error_when_all_attempts_fail() -> None:
    client = FlakyClient(fail_times=SURFACE_ATTEMPTS)
    result = check_surface("https://example.com/", client=client)
    assert not result.healthy
    assert "attempts" in result.error
    assert client.calls == SURFACE_ATTEMPTS


def test_does_not_retry_a_successful_non_200() -> None:
    """An HTTP 404 is a real answer, not a transport failure."""

    class NotFound:
        calls = 0

        def get(self, url, headers=None):
            NotFound.calls += 1
            return FakeResponse(404, "missing")

    client = NotFound()
    result = check_surface("https://example.com/", client=client)
    assert result.status == 404
    assert not result.healthy
    assert NotFound.calls == 1


def test_counts_non_ascii_in_body() -> None:
    client = FlakyClient(fail_times=0, body="<html>caf\u00e9 \u00b7 test</html>")
    result = check_surface("https://example.com/", client=client)
    assert result.non_ascii == 2
    assert not result.healthy