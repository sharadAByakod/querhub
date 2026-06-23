from types import SimpleNamespace

from queryhub.database.elasticsearch import elastic


def test_connect_elasticsearch_skips_tls_options_for_http(monkeypatch):
    captured: dict = {}

    def fake_elasticsearch(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(elastic, "Elasticsearch", fake_elasticsearch)
    monkeypatch.setattr(
        elastic,
        "settings",
        SimpleNamespace(
            es_host="http://localhost:9200",
            es_user="elastic",
            es_pass="changeme",
            es_ca_path="ca.crt",
            es_client_cert="client.crt",
            es_client_key="client.key",
        ),
    )

    elastic.connect_elasticsearch()

    assert captured == {
        "hosts": ["http://localhost:9200"],
        "basic_auth": ("elastic", "changeme"),
        "request_timeout": 10,
    }


def test_connect_elasticsearch_includes_tls_options_for_https(monkeypatch):
    captured: dict = {}

    def fake_elasticsearch(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(elastic, "Elasticsearch", fake_elasticsearch)
    monkeypatch.setattr(
        elastic,
        "settings",
        SimpleNamespace(
            es_host="https://localhost:9200",
            es_user="elastic",
            es_pass="changeme",
            es_ca_path="ca.crt",
            es_client_cert="client.crt",
            es_client_key="client.key",
        ),
    )

    elastic.connect_elasticsearch()

    assert captured["ca_certs"] == "ca.crt"
    assert captured["verify_certs"] is True
    assert captured["client_cert"] == "client.crt"
    assert captured["client_key"] == "client.key"
