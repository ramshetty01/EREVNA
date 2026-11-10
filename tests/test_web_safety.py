import socket
from unittest.mock import MagicMock

import pytest

from tools.web_search import public_address, scrape_page


@pytest.mark.parametrize(
    "url", ["file:///etc/passwd", "http://user:pass@example.com", "http://example.com:8080"]
)
def test_unsafe_urls_rejected(url):
    with pytest.raises(ValueError):
        public_address(url)


@pytest.mark.parametrize("ip", ["127.0.0.1", "10.0.0.5", "169.254.169.254", "::1", "192.168.1.1"])
def test_private_resolution_rejected(monkeypatch, ip):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", (ip, 80))])
    with pytest.raises(ValueError, match="blocked"):
        public_address("https://example.com")


def test_public_connection_pins_ip_and_preserves_tls_hostname(monkeypatch):
    monkeypatch.setattr(
        socket, "getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("93.184.215.14", 443))]
    )
    factory = MagicMock()
    response = factory.return_value.urlopen.return_value
    response.status = 200
    response.headers = {"Content-Type": "text/html"}
    response.read.return_value = (
        b"<html><script>ignore me</script><p>Useful research text</p></html>"
    )
    monkeypatch.setattr("tools.web_search.urllib3.HTTPSConnectionPool", factory)
    assert scrape_page("https://example.com/docs") == "Useful research text"
    factory.assert_called_once_with(
        "93.184.215.14", 443, server_hostname="example.com", assert_hostname="example.com"
    )
    assert factory.return_value.urlopen.call_args.kwargs["redirect"] is False


def test_private_redirect_is_rejected(monkeypatch):
    def dns(host, *a, **k):
        return [(2, 1, 6, "", ("127.0.0.1" if host == "localhost" else "93.184.215.14", 443))]

    monkeypatch.setattr(socket, "getaddrinfo", dns)
    factory = MagicMock()
    response = factory.return_value.urlopen.return_value
    response.status = 302
    response.headers = {"Location": "http://localhost/private"}
    monkeypatch.setattr("tools.web_search.urllib3.HTTPSConnectionPool", factory)
    assert scrape_page("https://example.com") == ""
    assert factory.call_count == 1
