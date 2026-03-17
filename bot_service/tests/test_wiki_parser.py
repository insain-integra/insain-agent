"""Тесты для wiki_parser.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wiki_parser import WikiArticle, YandexWikiParser, _strip_html, _strip_wiki_markup


class TestStripHtml:
    def test_basic_tags(self):
        assert _strip_html("<p>Hello</p>") == "Hello"

    def test_br_to_newline(self):
        assert "first" in _strip_html("first<br>second")
        assert "second" in _strip_html("first<br>second")

    def test_entities(self):
        assert _strip_html("&amp; &lt; &gt;") == "& < >"

    def test_nested_tags(self):
        result = _strip_html("<div><p>text <b>bold</b></p></div>")
        assert "text bold" in result

    def test_empty(self):
        assert _strip_html("") == ""


class TestStripWikiMarkup:
    def test_links_with_label(self):
        assert _strip_wiki_markup("see [[page|label]]") == "see label"

    def test_links_without_label(self):
        assert _strip_wiki_markup("see [[page]]") == "see page"

    def test_cut_blocks(self):
        result = _strip_wiki_markup("{{cut title=x}}hidden{{/cut}}")
        assert "hidden" in result or result.strip() == "hidden"

    def test_empty(self):
        assert _strip_wiki_markup("") == ""


class TestWikiArticle:
    def test_to_dict(self):
        a = WikiArticle(slug="test", title="Test", content="body", tags=["tag1"])
        d = a.to_dict()
        assert d["slug"] == "test"
        assert d["title"] == "Test"
        assert d["content"] == "body"
        assert d["tags"] == ["tag1"]
        assert d["updated_at"] is None

    def test_to_dict_with_datetime(self):
        from datetime import datetime
        dt = datetime(2025, 1, 15, 10, 30)
        a = WikiArticle(slug="s", title="T", content="c", updated_at=dt)
        d = a.to_dict()
        assert "2025-01-15" in d["updated_at"]


class TestYandexWikiParser:
    def test_not_available_without_credentials(self):
        parser = YandexWikiParser(token="NONE", org_id="NONE")
        parser.token = ""
        parser.org_id = ""
        assert not parser.is_available()

    def test_available_with_credentials(self):
        parser = YandexWikiParser(token="test-token", org_id="12345")
        assert parser.is_available()

    def test_fetch_pages_returns_empty_when_no_slugs(self):
        parser = YandexWikiParser(token="test-token", org_id="12345", slugs=[])
        result = parser.fetch_pages()
        assert result == []
