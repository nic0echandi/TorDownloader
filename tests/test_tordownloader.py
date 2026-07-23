"""Unit tests for tordownloader.py (no Tor connection required)."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Make sure the project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tordownloader

# Cross-platform temp directory for path-based tests that don't write files
_TMP = Path(tempfile.gettempdir()) / "tordownloader_tests"


class TestIsSameOrigin(unittest.TestCase):
    def test_same_origin(self):
        self.assertTrue(
            tordownloader.is_same_origin(
                "http://example.onion/foo/bar",
                "http://example.onion/",
            )
        )

    def test_different_host(self):
        self.assertFalse(
            tordownloader.is_same_origin(
                "http://other.onion/page",
                "http://example.onion/",
            )
        )

    def test_different_scheme(self):
        self.assertFalse(
            tordownloader.is_same_origin(
                "https://example.onion/page",
                "http://example.onion/",
            )
        )


class TestUrlToLocalPath(unittest.TestCase):
    def setUp(self):
        self.out = _TMP

    def test_file_url(self):
        path = tordownloader.url_to_local_path(
            "http://example.onion/docs/file.pdf",
            "http://example.onion/",
            self.out,
        )
        self.assertEqual(path, self.out / "example.onion" / "docs" / "file.pdf")

    def test_trailing_slash(self):
        path = tordownloader.url_to_local_path(
            "http://example.onion/section/",
            "http://example.onion/",
            self.out,
        )
        self.assertEqual(path, self.out / "example.onion" / "section" / "index.html")

    def test_no_extension(self):
        path = tordownloader.url_to_local_path(
            "http://example.onion/about",
            "http://example.onion/",
            self.out,
        )
        self.assertEqual(path, self.out / "example.onion" / "about" / "index.html")

    def test_root_path(self):
        path = tordownloader.url_to_local_path(
            "http://example.onion/",
            "http://example.onion/",
            self.out,
        )
        self.assertEqual(path, self.out / "example.onion" / "index.html")


class TestLooksLikeFile(unittest.TestCase):
    def test_pdf_extension(self):
        self.assertTrue(tordownloader.looks_like_file("http://x.onion/doc.pdf", None))

    def test_html_content_type(self):
        self.assertFalse(
            tordownloader.looks_like_file("http://x.onion/page", "text/html; charset=utf-8")
        )

    def test_binary_content_type(self):
        self.assertTrue(
            tordownloader.looks_like_file("http://x.onion/dl", "application/octet-stream")
        )

    def test_zip_extension(self):
        self.assertTrue(tordownloader.looks_like_file("http://x.onion/archive.zip", None))


class TestExtractLinks(unittest.TestCase):
    def test_absolute_links(self):
        html = '<a href="http://example.onion/page2">link</a>'
        links = tordownloader.extract_links(html, "http://example.onion/")
        self.assertIn("http://example.onion/page2", links)

    def test_relative_links(self):
        html = '<a href="/subdir/file.txt">link</a>'
        links = tordownloader.extract_links(html, "http://example.onion/")
        self.assertIn("http://example.onion/subdir/file.txt", links)

    def test_fragment_stripped(self):
        html = '<a href="/page#section">link</a>'
        links = tordownloader.extract_links(html, "http://example.onion/")
        self.assertIn("http://example.onion/page", links)
        self.assertNotIn("http://example.onion/page#section", links)

    def test_javascript_skipped(self):
        html = '<a href="javascript:void(0)">link</a>'
        links = tordownloader.extract_links(html, "http://example.onion/")
        self.assertEqual(links, [])

    def test_mailto_skipped(self):
        html = '<a href="mailto:test@example.com">email</a>'
        links = tordownloader.extract_links(html, "http://example.onion/")
        self.assertEqual(links, [])


class TestDownloadRecursive(unittest.TestCase):
    """Integration-level tests using mocked HTTP responses."""

    def _make_response(self, content: bytes, content_type: str = "text/html"):
        resp = MagicMock()
        resp.content = content
        resp.headers = {"Content-Type": content_type}
        resp.raise_for_status = MagicMock()
        return resp

    def test_saves_html_and_follows_links(self):
        html_root = b'<a href="/page2">go</a>'
        html_page2 = b'<p>no more links</p>'

        def fake_get(url, **kwargs):
            if url == "http://t.onion/":
                return self._make_response(html_root)
            if url == "http://t.onion/page2":
                return self._make_response(html_page2)
            raise AssertionError(f"Unexpected URL: {url}")

        session = MagicMock()
        session.get.side_effect = fake_get

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            tordownloader.download_recursive(
                start_url="http://t.onion/",
                output_dir=out,
                session=session,
                depth=-1,
                verbose=False,
                timeout=30,
            )
            root_file = out / "t.onion" / "index.html"
            page2_file = out / "t.onion" / "page2" / "index.html"
            self.assertTrue(root_file.exists())
            self.assertTrue(page2_file.exists())
            self.assertEqual(root_file.read_bytes(), html_root)
            self.assertEqual(page2_file.read_bytes(), html_page2)

    def test_does_not_follow_external_links(self):
        html = b'<a href="http://other.onion/secret">external</a>'

        session = MagicMock()
        session.get.return_value = self._make_response(html)

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            tordownloader.download_recursive(
                start_url="http://t.onion/",
                output_dir=out,
                session=session,
                depth=-1,
                verbose=False,
                timeout=30,
            )
            # Only the start URL should have been fetched
            self.assertEqual(session.get.call_count, 1)

    def test_depth_limit(self):
        """With depth=0 only the start page should be fetched."""
        html = b'<a href="/deep">go deeper</a>'

        session = MagicMock()
        session.get.return_value = self._make_response(html)

        with tempfile.TemporaryDirectory() as tmpdir:
            tordownloader.download_recursive(
                start_url="http://t.onion/",
                output_dir=Path(tmpdir),
                session=session,
                depth=0,
                verbose=False,
                timeout=30,
            )
            self.assertEqual(session.get.call_count, 1)

    def test_saves_binary_file(self):
        pdf_bytes = b"%PDF-1.4 binary content"

        session = MagicMock()
        session.get.return_value = self._make_response(pdf_bytes, "application/pdf")

        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir)
            tordownloader.download_recursive(
                start_url="http://t.onion/report.pdf",
                output_dir=out,
                session=session,
                depth=-1,
                verbose=False,
                timeout=30,
            )
            saved = out / "t.onion" / "report.pdf"
            self.assertTrue(saved.exists())
            self.assertEqual(saved.read_bytes(), pdf_bytes)

    def test_handles_request_error_gracefully(self):
        import requests as req_lib

        session = MagicMock()
        session.get.side_effect = req_lib.exceptions.ConnectionError("refused")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Should not raise; logs a warning instead
            tordownloader.download_recursive(
                start_url="http://t.onion/",
                output_dir=Path(tmpdir),
                session=session,
                depth=-1,
                verbose=False,
                timeout=30,
            )

    def test_visited_urls_not_refetched(self):
        """A URL that appears in multiple pages should only be fetched once."""
        html_root = b'<a href="/dup">A</a><a href="/dup">B</a>'
        html_dup = b'<p>done</p>'

        def fake_get(url, **kwargs):
            if url == "http://t.onion/":
                return self._make_response(html_root)
            if url == "http://t.onion/dup":
                return self._make_response(html_dup)
            raise AssertionError(f"Unexpected URL: {url}")

        session = MagicMock()
        session.get.side_effect = fake_get

        with tempfile.TemporaryDirectory() as tmpdir:
            tordownloader.download_recursive(
                start_url="http://t.onion/",
                output_dir=Path(tmpdir),
                session=session,
                depth=-1,
                verbose=False,
                timeout=30,
            )
            # /dup appears twice in the HTML but should only be fetched once
            calls = [c.args[0] for c in session.get.call_args_list]
            self.assertEqual(calls.count("http://t.onion/dup"), 1)


class TestBuildSession(unittest.TestCase):
    def test_proxy_configured(self):
        session = tordownloader.build_session("127.0.0.1", 9050, 30)
        self.assertIn("socks5h://", session.proxies.get("http", ""))


class TestMain(unittest.TestCase):
    def test_help_exits_zero(self):
        with self.assertRaises(SystemExit) as cm:
            tordownloader.main(["--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_missing_url_exits_nonzero(self):
        with self.assertRaises(SystemExit) as cm:
            tordownloader.main([])
        self.assertNotEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
