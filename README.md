# TorDownloader

Recursively download files from a Tor (`.onion`) site through the Tor SOCKS5 proxy.

## Requirements

* Python 3.10+
* A running [Tor](https://www.torproject.org/) process (default: `127.0.0.1:9050`)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```
python tordownloader.py [OPTIONS] URL
```

### Positional arguments

| Argument | Description |
|----------|-------------|
| `URL`    | Starting URL to crawl (e.g. `http://example.onion/`) |

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-o`, `--output DIR` | `downloads` | Local directory where files are saved |
| `--proxy-host HOST` | `127.0.0.1` | Tor SOCKS5 proxy hostname |
| `--proxy-port PORT` | `9050` | Tor SOCKS5 proxy port |
| `--depth N` | `-1` | Maximum crawl depth (`-1` = unlimited) |
| `--timeout N` | `60` | HTTP request timeout in seconds |
| `-v`, `--verbose` | — | Enable verbose (DEBUG) logging |

### Examples

Download everything from an onion site (unlimited depth):
```bash
python tordownloader.py http://example.onion/
```

Download up to 2 levels deep and save to `~/tor-files`:
```bash
python tordownloader.py --depth 2 -o ~/tor-files http://example.onion/
```

Use a custom Tor proxy port:
```bash
python tordownloader.py --proxy-port 9150 http://example.onion/
```

## How it works

1. All HTTP/HTTPS requests are routed through the local Tor SOCKS5 proxy
   (`socks5h://` is used so DNS resolution also happens inside Tor).
2. Starting from the given URL, the crawler performs a **breadth-first** traversal,
   staying within the same origin (scheme + host).
3. HTML pages are parsed with BeautifulSoup; every `<a href>` and `<link href>` is
   enqueued if it has not been visited yet.
4. Every resource is saved locally under `<output>/<host>/<path>`, mirroring the
   remote directory structure.

## Notes

* The script will not follow links to external domains.
* Interrupted downloads can be resumed; already-saved files will be overwritten
  if the URL is visited again in a new run.
* Use `--depth` to limit scope and avoid downloading the entire internet over Tor.
