"""Bounded public-web retrieval with DNS pinning and redirect validation."""

import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import urllib3
from bs4 import BeautifulSoup
from ddgs import DDGS

HEADERS = {"User-Agent": "EREVNA/0.2 (research assistant)"}
MAX_BYTES = 1_000_000


def search_web(query: str, max_results: int = 5) -> list[dict]:
    try:
        with DDGS(timeout=10) as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception:
        # Never return provider exception strings as evidence or expose credentials.
        return [
            {
                "title": "Search unavailable",
                "href": "",
                "body": "Search service unavailable. Try again or provide sources.",
            }
        ]


def public_address(url: str) -> tuple[str, str, int, str]:
    parsed = urlsplit(url)
    if (
        parsed.scheme not in ("https", "http")
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError("Only public HTTP(S) URLs without credentials are allowed")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if port not in (80, 443):
        raise ValueError("Only standard web ports are allowed")
    addresses = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
    ips = [str(a[4][0]) for a in addresses]
    if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
        raise ValueError("Private, loopback and reserved addresses are blocked")
    return parsed.scheme, parsed.hostname, port, ips[0]


def scrape_page(url: str, max_chars: int = 24_000) -> str:
    if not url:
        return ""
    try:
        for _ in range(4):
            scheme, host, port, ip = public_address(url)
            parsed = urlsplit(url)
            target = (parsed.path or "/") + (("?" + parsed.query) if parsed.query else "")
            headers = {**HEADERS, "Host": host}
            # Connect to the validated IP, preserving TLS SNI/hostname validation.
            # No second DNS lookup and no environment proxy is involved.
            pool: urllib3.HTTPConnectionPool
            if scheme == "https":
                pool = urllib3.HTTPSConnectionPool(
                    ip, port, server_hostname=host, assert_hostname=host
                )
            else:
                pool = urllib3.HTTPConnectionPool(ip, port)
            response = None
            try:
                response = pool.urlopen(
                    "GET",
                    target,
                    headers=headers,
                    redirect=False,
                    retries=False,
                    preload_content=False,
                    timeout=urllib3.Timeout(connect=4, read=6),
                )
                if response.status in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location")
                    if not location:
                        return ""
                    url = urljoin(url, location)
                    continue
                if response.status != 200:
                    return ""
                content_type = response.headers.get("Content-Type", "").lower()
                if not any(
                    t in content_type for t in ("text/html", "text/plain", "application/xhtml")
                ):
                    return ""
                content = response.read(MAX_BYTES + 1)
                if len(content) > MAX_BYTES:
                    return ""
                soup = BeautifulSoup(content, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                    tag.decompose()
                return " ".join(soup.get_text(separator=" ").split())[:max_chars]
            finally:
                if response is not None:
                    response.close()
                pool.close()
    except (ValueError, OSError, urllib3.exceptions.HTTPError):
        return ""
    return ""
