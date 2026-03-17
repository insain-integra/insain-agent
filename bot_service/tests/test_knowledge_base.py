"""Тесты для knowledge_base.py."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from knowledge_base import KnowledgeBase, _tokenize, _snippet
from wiki_parser import WikiArticle, YandexWikiParser


class TestTokenize:
    def test_basic(self):
        tokens = _tokenize("Лазерная резка акрила")
        assert "лазерная" in tokens
        assert "резка" in tokens
        assert "акрила" in tokens

    def test_short_words_filtered(self):
        tokens = _tokenize("я и к")
        assert len(tokens) == 0

    def test_numbers(self):
        tokens = _tokenize("размер 300x400")
        assert "300x400" in tokens or "300" in tokens

    def test_empty(self):
        assert _tokenize("") == []


class TestSnippet:
    def test_short_text(self):
        text = "short text"
        result = _snippet(text, ["short"])
        assert "short" in result

    def test_long_text_with_match(self):
        text = "A" * 500 + " TARGET " + "B" * 500
        result = _snippet(text, ["target"], max_len=200)
        assert "target" in result.lower()
        assert len(result) <= 210  # some tolerance for ellipsis

    def test_no_match(self):
        text = "hello world"
        result = _snippet(text, ["xyz"], max_len=100)
        assert "hello" in result


class TestKnowledgeBase:
    def _make_kb(self, articles=None, local_dir=None):
        parser = YandexWikiParser(token="", org_id="")
        tmp = tempfile.mkdtemp()
        cache = Path(tmp) / "cache.json"
        kb = KnowledgeBase(
            wiki_parser=parser,
            local_dir=local_dir or tmp,
            cache_file=cache,
        )
        if articles:
            kb._articles = articles
            kb._save_cache()
        return kb

    def test_empty_kb(self):
        kb = self._make_kb()
        assert kb.article_count == 0
        assert kb.search("test") == []

    def test_search_by_title(self):
        articles = [
            WikiArticle(slug="laser", title="Лазерная резка", content="Резка акрила лазером."),
            WikiArticle(slug="print", title="Печать на бумаге", content="Листовая печать."),
        ]
        kb = self._make_kb(articles=articles)
        results = kb.search("лазерная резка")
        assert len(results) > 0
        assert results[0]["slug"] == "laser"

    def test_search_by_content(self):
        articles = [
            WikiArticle(slug="a1", title="Статья 1", content="Широкоформатная печать баннер материал."),
            WikiArticle(slug="a2", title="Статья 2", content="Резка фанеры."),
        ]
        kb = self._make_kb(articles=articles)
        results = kb.search("баннер")
        assert len(results) > 0
        assert results[0]["slug"] == "a1"

    def test_search_returns_snippet(self):
        articles = [
            WikiArticle(slug="s", title="Title", content="This is a long text about laminators and lamination process."),
        ]
        kb = self._make_kb(articles=articles)
        results = kb.search("lamination")
        assert len(results) > 0
        assert "snippet" in results[0]

    def test_get_context(self):
        articles = [
            WikiArticle(slug="info", title="О компании", content="Компания Инсайн занимается рекламным производством."),
        ]
        kb = self._make_kb(articles=articles)
        context = kb.get_context("компания")
        assert "О компании" in context
        assert "Инсайн" in context

    def test_get_context_empty(self):
        kb = self._make_kb()
        assert kb.get_context("anything") == ""

    def test_get_all_titles(self):
        articles = [
            WikiArticle(slug="a", title="AAA", content="x"),
            WikiArticle(slug="b", title="BBB", content="y"),
        ]
        kb = self._make_kb(articles=articles)
        titles = kb.get_all_titles()
        assert len(titles) == 2
        assert titles[0]["slug"] == "a"

    def test_load_local_files(self):
        tmp = tempfile.mkdtemp()
        md_file = Path(tmp) / "test_article.md"
        md_file.write_text("# Тестовая статья\n\nСодержимое статьи о компании.", encoding="utf-8")
        kb = self._make_kb(local_dir=tmp)
        articles = kb._load_local_files()
        assert len(articles) == 1
        assert articles[0].title == "Тестовая статья"
        assert "Содержимое" in articles[0].content

    def test_cache_round_trip(self):
        articles = [
            WikiArticle(slug="cached", title="Cached Article", content="Content here."),
        ]
        kb1 = self._make_kb(articles=articles)
        cache_file = kb1._cache_file
        kb2 = KnowledgeBase(
            wiki_parser=YandexWikiParser(token="", org_id=""),
            local_dir=str(kb1._local_dir),
            cache_file=cache_file,
        )
        assert kb2.article_count == 1
        assert kb2._articles[0].slug == "cached"
