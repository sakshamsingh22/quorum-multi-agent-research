import pytest

from security import validate_public_http_url
from pipeline import run_research_pipeline


@pytest.mark.parametrize("url", [
    "http://127.0.0.1/admin",
    "http://localhost/",
    "http://10.0.0.1/",
    "http://192.168.1.10/",
    "file:///etc/passwd",
    "ftp://example.com/file",
    "http://user:pass@example.com/",
    "",
])
def test_rejects_unsafe_or_invalid_urls(url):
    with pytest.raises(ValueError):
        validate_public_http_url(url)


def test_accepts_public_ip_url_without_dns_lookup():
    assert validate_public_http_url("https://8.8.8.8/dns-query") == "https://8.8.8.8/dns-query"


def test_rejects_empty_topic_before_creating_agents(monkeypatch):
    def unexpected():
        raise AssertionError("Agents should not be created for invalid input.")

    monkeypatch.setattr("pipeline.build_search_agent", unexpected)
    with pytest.raises(ValueError, match="must not be empty"):
        run_research_pipeline("   ")


def test_rejects_overlong_topic_before_creating_agents(monkeypatch):
    monkeypatch.setattr(
        "pipeline.build_search_agent",
        lambda: (_ for _ in ()).throw(AssertionError("Unexpected agent creation")),
    )
    with pytest.raises(ValueError, match="500 characters"):
        run_research_pipeline("x" * 501)
