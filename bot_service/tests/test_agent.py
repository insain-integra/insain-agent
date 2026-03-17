"""Тесты для agent.py — базовые unit-тесты без реального API."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestInsainAgentFormatResult:
    """Тесты форматирования результата _format_calc_result."""

    def _make_agent(self):
        with patch("agent.httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__enter__ = MagicMock(return_value=mock_instance)
            mock_client.return_value.__exit__ = MagicMock(return_value=False)
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_response.raise_for_status = MagicMock()
            mock_instance.get.return_value = mock_response

            from agent import InsainAgent
            agent = InsainAgent.__new__(InsainAgent)
            agent.calc_api_url = "http://test:8001"
            agent.llm = MagicMock()
            agent._calculators = [{"slug": "laser", "name": "Лазерная резка"}]
            agent._tools = []
            agent._param_schemas = {}
            agent._options_by_slug = {}
            agent.calculator_materials = {}

            from knowledge_base import KnowledgeBase
            from wiki_parser import YandexWikiParser
            import tempfile
            tmp = tempfile.mkdtemp()
            agent.kb = KnowledgeBase(
                wiki_parser=YandexWikiParser(token="", org_id=""),
                local_dir=tmp,
                cache_file=Path(tmp) / "cache.json",
            )
            return agent

    def test_format_basic_result(self):
        agent = self._make_agent()
        result = agent._format_calc_result(
            "calc_laser",
            {"quantity": 10, "width": 100, "height": 50, "mode": 1},
            {
                "cost": 500.0,
                "price": 800.0,
                "unit_price": 80.0,
                "time_hours": 0.5,
                "time_ready": 8.5,
                "weight_kg": 0.3,
                "materials": [{"code": "PVC3", "title": "ПВХ 3мм", "quantity": 10, "unit": "шт"}],
            },
        )
        assert "800.00" in result
        assert "Лазерная резка" in result
        assert "ПВХ 3мм" in result

    def test_format_error_result(self):
        agent = self._make_agent()
        result = agent._format_calc_result("calc_laser", {}, {"error": "Bad params"})
        assert "Не удалось" in result
        assert "Bad params" in result

    def test_format_zero_price_warning(self):
        agent = self._make_agent()
        result = agent._format_calc_result(
            "calc_laser",
            {"quantity": 1},
            {"cost": 0, "price": 0, "unit_price": 0, "time_hours": 0, "time_ready": 0, "weight_kg": 0, "materials": []},
        )
        assert "ВНИМАНИЕ" in result


class TestInsainAgentExecuteTool:
    """Тесты execute_tool."""

    def _make_agent(self):
        from agent import InsainAgent
        import tempfile
        from knowledge_base import KnowledgeBase
        from wiki_parser import WikiArticle, YandexWikiParser

        agent = InsainAgent.__new__(InsainAgent)
        agent.calc_api_url = "http://test:8001"
        agent.llm = MagicMock()
        agent._calculators = []
        agent._tools = []
        agent._param_schemas = {}
        agent._options_by_slug = {}
        agent.calculator_materials = {}

        tmp = tempfile.mkdtemp()
        parser = YandexWikiParser(token="", org_id="")
        kb = KnowledgeBase(wiki_parser=parser, local_dir=tmp, cache_file=Path(tmp) / "c.json")
        kb._articles = [
            WikiArticle(slug="about", title="О компании", content="Инсайн — рекламная компания в Москве."),
        ]
        agent.kb = kb
        return agent

    def test_search_knowledge_found(self):
        agent = self._make_agent()
        result = agent.execute_tool("search_knowledge", {"query": "компания"})
        assert "results" in result
        assert len(result["results"]) > 0
        assert result["results"][0]["slug"] == "about"

    def test_search_knowledge_empty_query(self):
        agent = self._make_agent()
        result = agent.execute_tool("search_knowledge", {"query": ""})
        assert "error" in result

    def test_search_knowledge_no_results(self):
        agent = self._make_agent()
        result = agent.execute_tool("search_knowledge", {"query": "xyznonexistent"})
        assert "results" in result


class TestInsainAgentModeLabel:
    def test_modes(self):
        from agent import InsainAgent
        assert InsainAgent._mode_label(0) == "эконом"
        assert InsainAgent._mode_label(1) == "стандарт"
        assert InsainAgent._mode_label(2) == "экспресс"
        assert InsainAgent._mode_label("invalid") == "стандарт"
