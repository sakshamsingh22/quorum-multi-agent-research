"""Input safety helpers for outbound URL fetching."""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit


def validate_public_http_url(url: str) -> str:
    """Return a normalized public HTTP(S) URL or raise ValueError.

    DNS is resolved before a request so obvious private, loopback, link-local,
    multicast, and reserved destinations are rejected.
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string.")

    parsed = urlsplit(url.strip())
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("Only HTTP and HTTPS URLs are allowed.")
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("URL must include a host and must not contain credentials.")
    if parsed.port is not None and not (1 <= parsed.port <= 65535):
        raise ValueError("URL port is invalid.")

    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise ValueError("Local network hosts are not allowed.")

    try:
        addresses = {ipaddress.ip_address(host)}
    except ValueError:
        try:
            records = socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise ValueError("URL host could not be resolved.") from exc
        addresses = {ipaddress.ip_address(record[4][0]) for record in records}

    if not addresses or any(
        not address.is_global for address in addresses
    ):
        raise ValueError("URL must resolve exclusively to public IP addresses.")

    return url.strip()
