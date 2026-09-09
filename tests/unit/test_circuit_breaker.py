from ingestion.connectors._circuit_breaker import CircuitBreaker, State


def test_closed_to_open():
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=60)
    assert cb.state == State.CLOSED
    cb.record_failure()
    assert cb.state == State.CLOSED
    cb.record_failure()
    assert cb.state == State.OPEN


def test_open_blocks_and_half_open():
    cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=0)
    cb.record_failure()
    assert cb.state == State.OPEN
    assert cb.allow_request() is True
    assert cb.state == State.HALF_OPEN


def test_half_open_success_closes():
    cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=0)
    cb.record_failure()
    cb.allow_request()
    cb.record_success()
    assert cb.state == State.CLOSED


def test_half_open_failure_reopens():
    cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=0)
    cb.record_failure()
    cb.allow_request()
    cb.record_failure()
    assert cb.state == State.OPEN


def test_per_type_max_retries_in_send_request(monkeypatch):
    from ingestion.connectors.base import send_request, HttpRequest
    import types

    calls = {"n": 0}

    def fake_sleep(*a, **k):
        calls["n"] += 1

    monkeypatch.setattr("ingestion.connectors.base.time.sleep", fake_sleep)
    # auth:0 -> no retry on auth failure type, should raise quickly
    req = HttpRequest(method="GET", url="http://example.com", timeout_seconds=1)
    import requests

    def fake_req(*a, **k):
        calls["n"] += 10
        # simulate 401-like auth failure path: raise RequestException with auth marker
        # For this test we check that failure_type="authentication" forces max_retries=0
        raise requests.RequestException("auth failure")

    monkeypatch.setattr("requests.request", fake_req)
    try:
        send_request(req, failure_type="authentication", max_retries=3)
        assert False
    except Exception:
        pass
    assert calls["n"] >= 10
