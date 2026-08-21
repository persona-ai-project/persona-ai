"""
SSRF-safe URL validation.
Blocks requests to private/internal IPs, localhost, and link-local addresses.
"""
import ipaddress
import socket
from urllib.parse import urlparse
from fastapi import HTTPException


BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # loopback
    ipaddress.ip_network("10.0.0.0/8"),        # private Class A
    ipaddress.ip_network("172.16.0.0/12"),     # private Class B
    ipaddress.ip_network("192.168.0.0/16"),    # private Class C
    ipaddress.ip_network("169.254.0.0/16"),    # link-local
    ipaddress.ip_network("::1/128"),            # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),           # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),          # IPv6 link-local
    ipaddress.ip_network("0.0.0.0/8"),         # "this" network
]


def validate_url_safe(url: str) -> str:
    """
    Validate URL format AND block SSRF to private/internal networks.
    Raises HTTPException 400 if URL is invalid or points to a blocked network.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Only http/https URLs are allowed")
    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="URL must have a hostname")

    hostname = parsed.hostname

    # Block localhost variations
    if hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        raise HTTPException(status_code=400, detail="Requests to localhost are not allowed")

    # Try to resolve hostname to IP
    try:
        resolved = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise HTTPException(status_code=400, detail=f"Could not resolve hostname: {hostname}")

    # Check each resolved IP against blocked networks
    for _, _, _, _, sockaddr in resolved:
        ip = ipaddress.ip_address(sockaddr[0])
        for network in BLOCKED_NETWORKS:
            if ip in network:
                raise HTTPException(
                    status_code=400,
                    detail=f"Requests to private/internal networks are not allowed (resolved {hostname} to {ip})"
                )

    return url
