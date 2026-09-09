from orchestration.health import DependencyCheck, check_health, check_ready


def test_health_ok():
    assert check_health() == {"status": "ok"}


def test_ready_ok():
    assert check_ready([])["status"] == "ok"
    assert check_ready([DependencyCheck(name="db", ok=True)])["status"] == "ok"


def test_ready_degraded():
    r = check_ready([DependencyCheck(name="db", ok=False, details="down")])
    assert r["status"] == "degraded"
    assert r["dependencies"][0]["name"] == "db"


def test_ready_no_secret_leak():
    r = check_ready([DependencyCheck(name="api", ok=False, details="fail")])
    assert "key" not in str(r).lower() or "api_key" not in str(r)
