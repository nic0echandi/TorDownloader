#!/usr/bin/env python3
"""
TorDownloader - Recursively download files from a Tor (.onion) site.

Requires a running Tor process listening on localhost:9050 (SOCKS5).
"""

import argparse
import logging
import mimetypes
import os
import sys
import urllib.parse
from collections import deque
from pathlib import Path

import requests
import socks  # noqa: F401 – imported so requests[socks] SOCKS5 transport is available
from bs4 import BeautifulSoup

logger = logging.getLogger("tordownloader")

# Extensions treated as downloadable files rather than crawlable HTML pages
DEFAULT_FILE_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".mp3", ".mp4", ".avi", ".mkv", ".mov", ".flac", ".ogg",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
    ".exe", ".bin", ".iso", ".dmg",
    ".txt", ".csv", ".json", ".xml", ".yaml", ".yml",
    ".sh", ".py", ".js", ".css",
}


def build_session(proxy_host: str, proxy_port: int, timeout: int) -> requests.Session:
    """Return a requests Session routed through the Tor SOCKS5 proxy."""
    session = requests.Session()
    proxy_url = f"socks5h://{proxy_host}:{proxy_port}"
    session.proxies = {"http": proxy_url, "https": proxy_url}
    session.headers.update({"User-Agent": "TorDownloader/1.0"})
    session.timeout = timeout
    return session


def is_same_origin(url: str, base: str) -> bool:
    """Return True if *url* shares the same scheme+netloc as *base*."""
    parsed_url = urllib.parse.urlparse(url)
    parsed_base = urllib.parse.urlparse(base)
    return (parsed_url.scheme == parsed_base.scheme and
            parsed_url.netloc == parsed_base.netloc)


def url_to_local_path(url: str, base_url: str, output_dir: Path) -> Path:
    """Map a remote URL to a local file path under *output_dir*."""
    parsed = urllib.parse.urlparse(url)
    # Strip leading slash and decode percent-encoding
    rel = urllib.parse.unquote(parsed.path.lstrip("/"))
    # If path ends with '/' or has no extension, treat as an index.html
    if not rel or rel.endswith("/"):
        rel = (rel.rstrip("/") + "/index.html").lstrip("/")
    elif not Path(rel).suffix:
        rel = rel + "/index.html"
    return output_dir / parsed.netloc / rel


def looks_like_file(url: str, content_type: str | None) -> bool:
    """Heuristic: decide whether a URL points to a downloadable file."""
    path = urllib.parse.urlparse(url).path
    ext = Path(path).suffix.lower()
    if ext in DEFAULT_FILE_EXTENSIONS:
        return True
    if content_type:
        mime = content_type.split(";")[0].strip().lower()
        if mime and not mime.startswith("text/html"):
            return True
    return False


def save_content(local_path: Path, content: bytes) -> None:
    """Write *content* to *local_path*, creating parent directories as needed."""
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(content)
    logger.info("Saved %s (%d bytes)", local_path, len(content))


def extract_links(html: str, page_url: str) -> list[str]:
    """Return absolute URLs found in <a href=…> and <link href=…> tags."""
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for tag in soup.find_all(["a", "link"], href=True):
        href = tag["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:")):
            continue
        abs_url = urllib.parse.urljoin(page_url, href)
        # Normalise – drop fragment
        abs_url = urllib.parse.urldefrag(abs_url)[0]
        links.append(abs_url)
    return links


def download_recursive(
    start_url: str,
    output_dir: Path,
    session: requests.Session,
    depth: int,
    verbose: bool,
) -> None:
    """BFS crawl from *start_url*, saving every reachable resource."""
    visited: set[str] = set()
    # Each item: (url, current_depth)
    queue: deque[tuple[str, int]] = deque([(start_url, 0)])

    while queue:
        url, current_depth = queue.popleft()

        if url in visited:
            continue
        visited.add(url)

        if not is_same_origin(url, start_url):
            logger.debug("Skipping external URL: %s", url)
            continue

        logger.info("Fetching [depth=%d]: %s", current_depth, url)

        try:
            response = session.get(url, stream=True, timeout=session.timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            logger.warning("Failed to fetch %s: %s", url, exc)
            continue

        content_type = response.headers.get("Content-Type", "")
        content = response.content

        local_path = url_to_local_path(url, start_url, output_dir)

        if looks_like_file(url, content_type):
            save_content(local_path, content)
        else:
            # Treat as an HTML page: save it and enqueue its links
            save_content(local_path, content)
            if depth < 0 or current_depth < depth:
                try:
                    html = content.decode("utf-8", errors="replace")
                except Exception:
                    continue
                for link in extract_links(html, url):
                    if link not in visited:
                        queue.append((link, current_depth + 1))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Recursively download files from a Tor (.onion) site.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("url", help="Starting URL (e.g. http://example.onion/)")
    parser.add_argument(
        "-o", "--output",
        default="downloads",
        help="Local directory to save downloaded files",
    )
    parser.add_argument(
        "--proxy-host",
        default="127.0.0.1",
        help="Tor SOCKS5 proxy hostname",
    )
    parser.add_argument(
        "--proxy-port",
        type=int,
        default=9050,
        help="Tor SOCKS5 proxy port",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=-1,
        help="Maximum crawl depth (-1 for unlimited)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP request timeout in seconds",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    output_dir = Path(args.output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    session = build_session(args.proxy_host, args.proxy_port, args.timeout)

    try:
        download_recursive(
            start_url=args.url,
            output_dir=output_dir,
            session=session,
            depth=args.depth,
            verbose=args.verbose,
        )
    except KeyboardInterrupt:
        logger.info("Interrupted by user.")
        return 1

    logger.info("Done. Files saved to: %s", output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
