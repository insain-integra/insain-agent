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


class TestRouterParsing:
    """Роутер: разбор intent + calculator_slug."""

    def test_parse_calculator_with_slug(self):
        from agent import InsainAgent
        out = {
            "content": None,
            "tool_calls": [
                {
                    "id": "1",
                    "type": "function",
                    "function": {
                        "name": "route_request",
                        "arguments": '{"intent": "calculator", "reason": "пересчёт", "calculator_slug": "print_sheet"}',
                    },
                }
            ],
        }
        intent, slug = InsainAgent._parse_router_result(out)
        assert intent == "calculator"
        assert slug == "print_sheet"

    def test_parse_knowledge_clears_slug(self):
        from agent import InsainAgent
        out = {
            "tool_calls": [
                {
                    "function": {
                        "name": "route_request",
                        "arguments": '{"intent": "knowledge", "reason": "справка", "calculator_slug": ""}',
                    }
                }
            ]
        }
        intent, slug = InsainAgent._parse_router_result(out)
        assert intent == "knowledge"
        assert slug is None

    def test_parse_fallback_calculator_none_slug(self):
        from agent import InsainAgent
        intent, slug = InsainAgent._parse_router_result({"content": "", "tool_calls": []})
        assert intent == "calculator"
        assert slug is None

    def test_parse_json_in_content(self):
        from agent import InsainAgent
        out = {
            "content": 'Ответ: {"intent": "knowledge", "reason": "вопрос", "calculator_slug": ""}',
            "tool_calls": None,
        }
        intent, slug = InsainAgent._parse_router_result(out)
        assert intent == "knowledge"
        assert slug is None

    def test_parse_calculator_empty_slug(self):
        from agent import InsainAgent
        out = {
            "tool_calls": [
                {
                    "function": {
                        "name": "route_request",
                        "arguments": '{"intent": "calculator", "reason": "не ясно", "calculator_slug": ""}',
                    }
                }
            ]
        }
        intent, slug = InsainAgent._parse_router_result(out)
        assert intent == "calculator"
        assert slug is None


class TestToolsForIntent:
    def test_knowledge_returns_only_search_knowledge(self):
        from agent import SEARCH_KNOWLEDGE_TOOL, SEARCH_MATERIALS_TOOL, InsainAgent
        agent = InsainAgent.__new__(InsainAgent)
        calc_ps = {"type": "function", "function": {"name": "calc_print_sheet"}}
        agent._calc_tool_by_slug = {"print_sheet": calc_ps}
        full = [SEARCH_KNOWLEDGE_TOOL, SEARCH_MATERIALS_TOOL, calc_ps]
        result = agent._tools_for_intent("knowledge", None, full)
        assert len(result) == 1
        assert result[0] == SEARCH_KNOWLEDGE_TOOL

    def test_calculator_with_slug_returns_narrow_set(self):
        from agent import SEARCH_KNOWLEDGE_TOOL, SEARCH_MATERIALS_TOOL, InsainAgent
        agent = InsainAgent.__new__(InsainAgent)
        calc_ps = {"type": "function", "function": {"name": "calc_print_sheet"}}
        agent._calc_tool_by_slug = {"print_sheet": calc_ps}
        full = [SEARCH_KNOWLEDGE_TOOL, SEARCH_MATERIALS_TOOL, calc_ps]
        narrow = agent._tools_for_intent("calculator", "print_sheet", full)
        assert len(narrow) == 2
        assert narrow[0] == SEARCH_MATERIALS_TOOL
        assert narrow[1] == calc_ps

    def test_calculator_without_slug_returns_minimal(self):
        from agent import SEARCH_KNOWLEDGE_TOOL, SEARCH_MATERIALS_TOOL, InsainAgent
        agent = InsainAgent.__new__(InsainAgent)
        calc_ps = {"type": "function", "function": {"name": "calc_print_sheet"}}
        agent._calc_tool_by_slug = {"print_sheet": calc_ps}
        full = [SEARCH_KNOWLEDGE_TOOL, SEARCH_MATERIALS_TOOL, calc_ps]
        result = agent._tools_for_intent("calculator", None, full)
        assert len(result) == 2
        assert result[0] == SEARCH_KNOWLEDGE_TOOL
        assert result[1] == SEARCH_MATERIALS_TOOL


class TestSystemPromptForIntent:
    def test_knowledge_prompt(self):
        from agent import InsainAgent
        agent = InsainAgent.__new__(InsainAgent)
        agent._user_calc_context = {}
        agent._calc_tool_by_slug = {}
        agent._calculators = []
        agent._calc_llm_prompts = {}
        agent._calculator_index = ""
        prompt = agent._system_prompt_for_intent("knowledge", None)
        assert "Wiki" in prompt or "база знаний" in prompt

    def test_calculator_with_slug_prompt(self):
        from agent import InsainAgent
        agent = InsainAgent.__new__(InsainAgent)
        agent._user_calc_context = {}
        agent._calc_tool_by_slug = {
            "laser": {"type": "function", "function": {"name": "calc_laser"}}
        }
        agent._calculators = [{"slug": "laser", "name": "Лазерная резка", "description": "Лазер"}]
        agent._calc_llm_prompts = {"laser": "Алгоритм лазера."}
        agent._calculator_index = ""
        prompt = agent._system_prompt_for_intent("calculator", "laser")
        assert "laser" in prompt
        assert "calc_laser" in prompt
        assert "Алгоритм лазера" in prompt

    def test_calculator_without_slug_uses_short_fallback(self):
        from agent import InsainAgent
        agent = InsainAgent.__new__(InsainAgent)
        agent._calc_tool_by_slug = {}
        agent._calculators = [{"slug": "laser", "name": "Лазерная резка"}]
        agent._calc_llm_prompts = {}
        agent._user_calc_context = {}
        prompt = agent._system_prompt_for_intent("calculator", None)
        assert "Калькулятор для текущего запроса" in prompt or "не выбран" in prompt
        assert "Лазерная" in prompt or "laser" in prompt


class TestRecalcHeuristics:
    """Эвристики пересчёта без LLM (логи: tool_calls_count=0 при «500 шт»)."""

    def test_user_message_suggests_recalc(self):
        from agent import InsainAgent

        assert InsainAgent._user_message_suggests_recalc("посчитай 500шт")
        assert InsainAgent._user_message_suggests_recalc("посчитай 4+4")
        assert not InsainAgent._user_message_suggests_recalc("посчитай 130гр")
        assert not InsainAgent._user_message_suggests_recalc("посчитай матовую бумагу 130гр")
        assert not InsainAgent._user_message_suggests_recalc("привет")
        assert not InsainAgent._user_message_suggests_recalc("что такое ламинация")

    def test_router_continuation_includes_material_change(self):
        from agent import InsainAgent

        assert InsainAgent._router_context_continuation_message("посчитай 130гр")
        assert InsainAgent._router_context_continuation_message("посчитай 500шт")

    def test_router_override_knowledge_to_calculator(self):
        from agent import InsainAgent

        agent = InsainAgent.__new__(InsainAgent)
        agent._calc_tool_by_slug = {"print_sheet": {}}
        agent._user_calc_context = {
            1: {"slug": "print_sheet", "tool_name": "calc_print_sheet", "params": {"quantity": 100}},
        }
        intent, slug = agent._router_apply_context_override("knowledge", None, "посчитай 4+4", 1)
        assert intent == "calculator"
        assert slug == "print_sheet"

    def test_router_override_knowledge_material_density(self):
        from agent import InsainAgent

        agent = InsainAgent.__new__(InsainAgent)
        agent._calc_tool_by_slug = {"print_sheet": {}}
        agent._user_calc_context = {
            1: {"slug": "print_sheet", "tool_name": "calc_print_sheet", "params": {"quantity": 100}},
        }
        intent, slug = agent._router_apply_context_override("knowledge", None, "посчитай 130гр", 1)
        assert intent == "calculator"
        assert slug == "print_sheet"

    def test_heuristic_magnet_slug_acrylic(self):
        from agent import InsainAgent

        agent = InsainAgent.__new__(InsainAgent)
        agent._calc_tool_by_slug = {"magnet_acrylic": {}, "magnet_laminated": {}}
        assert agent._heuristic_magnet_slug("посчитай магниты акриловые") == "magnet_acrylic"
        assert agent._heuristic_magnet_slug("ламинированные магниты 100 шт") == "magnet_laminated"

    def test_router_magnet_thread_override_blanks(self):
        from agent import InsainAgent

        agent = InsainAgent.__new__(InsainAgent)
        agent._calc_tool_by_slug = {"magnet_acrylic": {}}
        agent._user_calc_context = {}
        history = [
            {"role": "user", "content": "посчитай акриловые магниты"},
            {
                "role": "assistant",
                "content": "Нужен тираж. Какой размер магнита?",
            },
        ]
        intent, slug = agent._router_apply_context_override(
            "knowledge", None, "какие есть заготовки", 0, history
        )
        assert intent == "calculator"
        assert slug == "magnet_acrylic"

    def test_merge_params_prefers_url_and_user_quantity(self):
        from agent import InsainAgent

        agent = InsainAgent.__new__(InsainAgent)
        ctx = {
            "quantity": 100,
            "width": 100.0,
            "height": 100.0,
            "material_id": "PaperCoated115M",
            "color": "4+0",
        }
        history = [
            {
                "role": "assistant",
                "content": (
                    "Печать листовая\n\nТираж\t200\n"
                    "🔗 Ссылка для клиента:\n"
                    "https://insain.ru/calculator/print_sheet/?height=100&material_id=PaperCoated115M"
                    "&quantity=200&width=100&color_type=4+4"
                ),
            }
        ]
        merged = agent._merge_params_for_recalc("print_sheet", ctx, "посчитай 500шт", history)
        assert merged["quantity"] == 500
        assert merged["material_id"] == "PaperCoated115M"
        assert merged.get("color") == "4+4"


class TestMaterialSearchFallback:
    """Fallback поиска материалов и подстановка id (логи: пустой search → выдуманный paper_coated_115)."""

    def test_fallback_queries_includes_melovka_short(self):
        from agent import InsainAgent

        q = InsainAgent._fallback_queries_print_sheet_material("Мелованная бумага 115 г/м²")
        assert "меловка 115" in q
        assert q[0] == "Мелованная бумага 115 г/м²"

    def test_material_id_suspicious(self):
        from agent import InsainAgent

        assert InsainAgent._material_id_looks_suspicious("paper_coated_115")
        assert InsainAgent._material_id_looks_suspicious("")
        assert not InsainAgent._material_id_looks_suspicious("PaperCoated115M")
        assert not InsainAgent._material_id_looks_suspicious("PVC3")


class TestBuildRecalcContext:
    def test_build_recalc_context(self):
        from prompts import build_recalc_context

        s = build_recalc_context({"quantity": 100, "width": 50}, "print_sheet")
        assert "print_sheet" in s
        assert "quantity" in s
        assert "100" in s


class TestSanitizeLlmReplyForDisplay:
    def test_ctrl_tokens_become_colons(self):
        from agent import InsainAgent

        raw = "title:<ctrl46>Уточните материал:<ctrl46>\n1. Меловка матовая"
        out = InsainAgent.sanitize_llm_reply_for_display(raw)
        assert "<ctrl" not in out
        assert "Уточните материал:" in out or "Уточните материал" in out

    def test_strips_id_parentheses(self):
        from agent import InsainAgent

        s = "1. Мат (id: PaperCoated115M)"
        out = InsainAgent.sanitize_llm_reply_for_display(s)
        assert "PaperCoated115M" not in out
        assert "(id:" not in out.lower()


class TestParseNumberedChoiceLines:
    def test_two_variants(self):
        from agent import InsainAgent

        text = (
            "Выберите:\n"
            "1. Меловка матовая 115г/м²\n"
            "2. Меловка глянцевая 115г/м²"
        )
        titles = InsainAgent._parse_numbered_choice_lines(text)
        assert len(titles) == 2
        assert "матовая" in titles[0]
        assert "глянцевая" in titles[1]


class TestEnrichToolPropsFromParamSchemaInlineChoices:
    def test_adds_enum_and_description_from_inline(self):
        from agent import InsainAgent

        props = {
            "magnet_id": {"type": "string", "description": "Код заготовки"},
        }
        param_schema = {
            "params": [
                {
                    "name": "magnet_id",
                    "choices": {
                        "inline": [
                            {"id": "MagnetAcrylic6565", "title": "Квадрат 65×65"},
                            {"id": "MagnetAcrylic5277", "title": "Прямоугольник 52×77"},
                        ]
                    },
                }
            ]
        }
        InsainAgent._enrich_tool_props_from_param_schema_inline_choices(props, param_schema)
        assert props["magnet_id"]["enum"] == ["MagnetAcrylic6565", "MagnetAcrylic5277"]
        assert "MagnetAcrylic6565" in props["magnet_id"]["description"]
        assert "Квадрат 65×65" in props["magnet_id"]["description"]

    def test_skips_when_enum_already_set(self):
        from agent import InsainAgent

        props = {
            "color": {"type": "string", "enum": ["4+0", "4+4"], "description": "fixed"},
        }
        param_schema = {
            "params": [
                {
                    "name": "color",
                    "choices": {"inline": [{"id": "1+0", "title": "x"}]},
                }
            ]
        }
        InsainAgent._enrich_tool_props_from_param_schema_inline_choices(props, param_schema)
        assert props["color"]["enum"] == ["4+0", "4+4"]


class TestNormalizeChoicesParam:
    def test_lamination_slug_maps_lamination_to_material(self):
        from agent import InsainAgent
        assert InsainAgent._normalize_choices_param("lamination", "lamination") == "material"
        assert InsainAgent._normalize_choices_param("lamination", "material") == "material"

    def test_other_slugs_unchanged(self):
        from agent import InsainAgent
        assert InsainAgent._normalize_choices_param("print_sheet", "lamination") == "lamination"
        assert InsainAgent._normalize_choices_param("print_sheet", "material") == "material"
