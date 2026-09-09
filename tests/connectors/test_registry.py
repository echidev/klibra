from ingestion.connectors._registry import REGISTRY, get, discover_all, list_sources


def test_registry_has_five_sources():
    assert set(discover_all()) == {"worldbank", "fred", "ecb", "alphavantage", "coingecko"}


def test_get_worldbank():
    assert get("worldbank").source_id == "worldbank"


def test_duplicate_rejected():
    from ingestion.connectors._registry import ConnectorRegistration, REGISTRY as R

    from ingestion.connectors.worldbank import WorldBankConnector

    reg = ConnectorRegistration("worldbank", "dup", "A", WorldBankConnector, ())
    try:
        from ingestion.connectors._registry import register

        register(reg)
        assert False, "should have raised"
    except ValueError as e:
        assert "duplicate" in str(e).lower()


def test_list_sources_sorted():
    assert [r.source_id for r in list_sources()] == sorted(discover_all())


def test_dummy_registration_no_orchestration_edit(monkeypatch):
    from ingestion.connectors._registry import ConnectorRegistration, REGISTRY

    from ingestion.connectors.base import SourceConnectorBase

    class DummyConnector(SourceConnectorBase):
        connector_version = "0.0.1"

        def extract(self, **kwargs):
            from ingestion.connectors.base import ExtractionResult

            return ExtractionResult(payload=b"{}", source_url="dummy://", request_params={})

    dummy_id = "dummy_test"
    if dummy_id in REGISTRY:
        del REGISTRY[dummy_id]
    REGISTRY[dummy_id] = ConnectorRegistration(dummy_id, "Dummy", "A", DummyConnector, ())
    assert dummy_id in discover_all()
    assert get(dummy_id).connector_class is DummyConnector
    del REGISTRY[dummy_id]
