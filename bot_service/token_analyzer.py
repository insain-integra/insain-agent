"""Token usage analyzer for LLM providers (Gemini / YandexGPT).

Пример использования (внутри LLMProvider):

    from token_analyzer import TokenAnalyzer

    class LLMProvider:
        def __init__(...):
            ...
            self.analyzer = TokenAnalyzer()

        def chat(self, messages, tools=None):
            request_log = self.analyzer.log_request(
                messages=messages,
                tools=tools,
                metadata={"provider": "gemini", "model": self.model},
            )
            try:
                response = self._actual_chat(messages, tools)
                full_log = self.analyzer.log_response(response, request_log)
                self.analyzer.save_to_file(full_log)
                return response
            except Exception as e:
                request_log["error"] = str(e)
                self.analyzer.save_to_file(request_log)
                raise
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from rich.console import Console
from rich.table import Table


def _ensure_text(content: Any) -> str:
    """Привести контент сообщения к строке."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))
        return " ".join(parts)
    return str(content)


class TokenAnalyzer:
    """
    Анализ расхода токенов в запросах к LLM.

    Логирует:
    - длину каждого сообщения (в символах и оценка токенов)
    - количество и размер tools
    - общий размер запроса
    - размер ответа
    - breakdown по компонентам (system, history, user, tools)
    """

    # цена за 1M токенов (руб.)
    DEFAULT_PRICING_RUB_PER_1M = {
        "yandex": 400.0,
        "gemini": 0.0,
    }

    def __init__(
        self,
        log_path: Optional[Path] = None,
        pricing_rub_per_1m: Optional[Dict[str, float]] = None,
    ) -> None:
        root = Path(__file__).resolve().parent.parent  # проект
        self.log_path: Path = log_path or (root / "logs" / "token_usage.jsonl")
        self.pricing_rub_per_1m: Dict[str, float] = (
            pricing_rub_per_1m or self.DEFAULT_PRICING_RUB_PER_1M
        )

    # --- оценки токенов -------------------------------------------------

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Оценка токенов для русского текста.

        1 токен ≈ 4 символа (консервативная оценка).
        """
        if not text:
            return 0
        return max(1, len(text) // 4)

    def estimate_tokens_json(self, obj: Any) -> int:
        """Оценка токенов для JSON-объекта."""
        try:
            json_str = json.dumps(obj, ensure_ascii=False)
        except Exception:
            json_str = str(obj)
        return self.estimate_tokens(json_str)

    def _estimate_cost_rub(self, provider: str, tokens: int) -> float:
        """Оценить стоимость в рублях для заданного провайдера и числа токенов."""
        price_per_1m = self.pricing_rub_per_1m.get(provider.lower(), 0.0)
        if price_per_1m <= 0 or tokens <= 0:
            return 0.0
        return round(tokens * (price_per_1m / 1_000_000.0), 4)

    # --- логирование запросов / ответов ---------------------------------

    def log_request(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Анализ и логирование запроса к LLM.

        Возвращает детальный breakdown (без информации об ответе).
        """
        timestamp = datetime.utcnow().isoformat()
        metadata = dict(metadata or {})

        # system / user / history разбор
        system_texts: List[str] = []
        history_texts: List[str] = []
        user_text: str = ""

        user_indices: List[int] = [
            idx for idx, m in enumerate(messages) if (m.get("role") or "").lower() == "user"
        ]
        last_user_idx: Optional[int] = user_indices[-1] if user_indices else None

        for idx, m in enumerate(messages):
            role = (m.get("role") or "").lower()
            text = _ensure_text(m.get("content"))
            if role == "system":
                if text:
                    system_texts.append(text)
                continue
            if last_user_idx is not None and idx == last_user_idx:
                user_text = text
                continue
            # всё остальное (user/assistant/tool) считаем историей
            if text:
                history_texts.append(text)

        system_joined = "\n".join(system_texts)
        history_joined = "\n".join(history_texts)

        # оценки токенов по компонентам
        sys_chars = len(system_joined)
        sys_tokens = self.estimate_tokens(system_joined)

        hist_chars = len(history_joined)
        hist_tokens = self.estimate_tokens(history_joined)

        user_chars = len(user_text)
        user_tokens = self.estimate_tokens(user_text)

        # tools
        tools = tools or []
        tools_chars_total = 0
        tools_tokens_total = 0
        tools_list: List[Dict[str, Any]] = []
        for t in tools:
            func = t.get("function") or {}
            name = func.get("name") or t.get("name") or "unknown"
            tok = self.estimate_tokens_json(func)
            tools_tokens_total += tok
            tools_chars_total += len(json.dumps(func, ensure_ascii=False))
            tools_list.append(
                {
                    "name": name,
                    "tokens_estimate": tok,
                }
            )

        input_chars = sys_chars + hist_chars + user_chars + tools_chars_total
        input_tokens = sys_tokens + hist_tokens + user_tokens + tools_tokens_total

        provider = (metadata.get("provider") or "").lower()
        cost_estimate_rub = self._estimate_cost_rub(provider, input_tokens)

        breakdown = {
            "system_prompt": {
                "chars": sys_chars,
                "tokens_estimate": sys_tokens,
            },
            "history": {
                "messages_count": len(history_texts),
                "chars": hist_chars,
                "tokens_estimate": hist_tokens,
            },
            "user_message": {
                "chars": user_chars,
                "tokens_estimate": user_tokens,
            },
            "tools": {
                "count": len(tools),
                "chars": tools_chars_total,
                "tokens_estimate": tools_tokens_total,
                "tools_list": tools_list,
            },
        }

        total = {
            "input_chars": input_chars,
            "input_tokens_estimate": input_tokens,
            "output_tokens_estimate": 0,
            "total_tokens_estimate": input_tokens,
            "cost_estimate_rub": cost_estimate_rub,
        }

        # В лог по умолчанию кладём breakdown/total + метаданные.
        # Для отладки полезно также видеть сырые messages и tools,
        # поэтому добавляем их в поле "debug".
        return {
            "timestamp": timestamp,
            "metadata": metadata,
            "breakdown": breakdown,
            "total": total,
            "debug": {
                "messages": messages,
                "tools": tools,
            },
        }

    def log_response(
        self,
        response: Dict[str, Any],
        request_log: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Анализ ответа от LLM.

        Дополняет request_log полями по выходным токенам и обновлённой стоимостью.
        """
        content = response.get("content")
        tool_calls = response.get("tool_calls") or []

        content_text = _ensure_text(content)
        content_chars = len(content_text)
        content_tokens = self.estimate_tokens(content_text)

        tool_calls_tokens = self.estimate_tokens_json(tool_calls) if tool_calls else 0

        total_info = request_log.get("total", {})
        input_tokens = int(total_info.get("input_tokens_estimate", 0))

        output_tokens = content_tokens + tool_calls_tokens
        total_tokens = input_tokens + output_tokens

        metadata = request_log.get("metadata") or {}
        provider = (metadata.get("provider") or "").lower()
        cost_estimate_rub = self._estimate_cost_rub(provider, total_tokens)

        request_log["response"] = {
            "content_chars": content_chars,
            "content_tokens_estimate": content_tokens,
            "tool_calls_count": len(tool_calls),
            "tool_calls_tokens_estimate": tool_calls_tokens,
        }
        request_log["total"] = {
            "input_chars": int(total_info.get("input_chars", 0)),
            "input_tokens_estimate": input_tokens,
            "output_tokens_estimate": output_tokens,
            "total_tokens_estimate": total_tokens,
            "cost_estimate_rub": cost_estimate_rub,
        }
        return request_log

    def save_to_file(self, log_entry: Dict[str, Any], filepath: Optional[str] = None) -> None:
        """
        Сохранить запись в JSONL-файл (одна строка = один JSON).

        Формат:
        {"timestamp": "...", "breakdown": {...}, "total": {...}}
        """
        path = Path(filepath) if filepath is not None else self.log_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            json.dump(log_entry, f, ensure_ascii=False)
            f.write("\n")

        # Дополнительно: отдельный подробный лог-файл на каждый запрос.
        # Удобно для анализа конкретного диалога (видно все messages, tools и метаданные).
        ts = str(log_entry.get("timestamp") or datetime.utcnow().isoformat())
        safe_ts = ts.replace(":", "-").replace(".", "-")
        per_request_path = path.parent / f"llm_request_{safe_ts}.json"
        try:
            with per_request_path.open("w", encoding="utf-8") as f_req:
                json.dump(log_entry, f_req, ensure_ascii=False, indent=2)
        except Exception:
            # Логирование не должно ломать основной поток, поэтому ошибки здесь глотаем.
            pass


@dataclass
class _ComponentStats:
    tokens: int = 0
    percent: float = 0.0


class TokenUsageStats:
    """
    Агрегация статистики из логов.

    Методы:
    - load_from_file(filepath) — загрузить логи
    - get_total_stats() — общая статистика
    - get_breakdown_by_component() — разбивка по компонентам
    - get_top_expensive_requests(n=10) — самые дорогие запросы
    - get_tools_stats() — статистика по tools
    - print_report() — красивый отчёт в консоль
    """

    def __init__(self) -> None:
        self.entries: List[Dict[str, Any]] = []
        self.console = Console()

    def load_from_file(self, filepath: str) -> None:
        """Загрузить логи из JSONL-файла."""
        self.entries.clear()
        path = Path(filepath)
        if not path.is_file():
            return
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                self.entries.append(entry)

    # --- агрегаты --------------------------------------------------------

    def get_total_stats(self) -> Dict[str, Any]:
        """Общая статистика по токенам и стоимости."""
        if not self.entries:
            return {
                "requests": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "total_cost_rub": 0.0,
                "period": None,
            }

        input_tokens = 0
        output_tokens = 0
        total_cost = 0.0
        timestamps: List[datetime] = []

        for e in self.entries:
            total = e.get("total") or {}
            input_tokens += int(total.get("input_tokens_estimate", 0))
            output_tokens += int(total.get("output_tokens_estimate", 0))
            total_cost += float(total.get("cost_estimate_rub", 0.0))
            ts = e.get("timestamp")
            if ts:
                try:
                    timestamps.append(datetime.fromisoformat(ts))
                except ValueError:
                    continue

        total_tokens = input_tokens + output_tokens
        period: Optional[Tuple[Optional[datetime], Optional[datetime]]] = None
        if timestamps:
            period = (min(timestamps), max(timestamps))

        return {
            "requests": len(self.entries),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "total_cost_rub": round(total_cost, 4),
            "period": period,
        }

    def get_breakdown_by_component(self) -> Dict[str, _ComponentStats]:
        """Разбивка input-токенов по компонентам system/history/user/tools."""
        stats = {
            "system": _ComponentStats(),
            "history": _ComponentStats(),
            "user": _ComponentStats(),
            "tools": _ComponentStats(),
        }
        if not self.entries:
            return stats

        total_input = 0
        for e in self.entries:
            b = e.get("breakdown") or {}
            sys_t = int((b.get("system_prompt") or {}).get("tokens_estimate", 0))
            hist_t = int((b.get("history") or {}).get("tokens_estimate", 0))
            user_t = int((b.get("user_message") or {}).get("tokens_estimate", 0))
            tools_t = int((b.get("tools") or {}).get("tokens_estimate", 0))
            stats["system"].tokens += sys_t
            stats["history"].tokens += hist_t
            stats["user"].tokens += user_t
            stats["tools"].tokens += tools_t
            total_input += sys_t + hist_t + user_t + tools_t

        if total_input <= 0:
            return stats

        for comp in stats.values():
            comp.percent = round(100.0 * comp.tokens / total_input, 2)

        return stats

    def get_top_expensive_requests(self, n: int = 10) -> List[Dict[str, Any]]:
        """Вернуть N самых дорогих запросов по стоимости."""
        if not self.entries or n <= 0:
            return []
        sorted_entries = sorted(
            self.entries,
            key=lambda e: float((e.get("total") or {}).get("cost_estimate_rub", 0.0)),
            reverse=True,
        )
        return sorted_entries[:n]

    def get_tools_stats(self) -> Dict[str, Dict[str, Any]]:
        """Статистика по tools: суммарные токены и количество вызовов по имени инструмента."""
        tools_totals: Dict[str, Dict[str, Any]] = {}
        total_input_tokens = 0

        for e in self.entries:
            b = e.get("breakdown") or {}
            tools = (b.get("tools") or {}).get("tools_list") or []
            for t in tools:
                name = t.get("name") or "unknown"
                tok = int(t.get("tokens_estimate") or 0)
                info = tools_totals.setdefault(
                    name, {"tokens": 0, "count": 0}
                )
                info["tokens"] += tok
                info["count"] += 1
                total_input_tokens += tok

        # проценты
        for name, info in tools_totals.items():
            tokens = info["tokens"]
            percent = 0.0
            if total_input_tokens > 0:
                percent = round(100.0 * tokens / total_input_tokens, 2)
            info["percent"] = percent

        return tools_totals

    # --- вывод отчётов ---------------------------------------------------

    def print_report(self) -> None:
        """Красивый сводный отчёт по всем логам."""
        stats = self.get_total_stats()
        breakdown = self.get_breakdown_by_component()

        console = self.console
        console.print()
        console.print("📊 [bold]АНАЛИЗ РАСХОДА ТОКЕНОВ[/bold]")
        console.rule()

        period = stats["period"]
        if period:
            start, end = period
            console.print(
                f"📅 Период: {start} - {end}",
            )
        console.print(f"📨 Всего запросов: {stats['requests']}")
        console.print(f"💰 Общая стоимость: {stats['total_cost_rub']:.2f} ₽")
        console.print()

        table = Table(title="Разбивка по компонентам", show_header=True, header_style="bold")
        table.add_column("Компонент")
        table.add_column("Токены", justify="right")
        table.add_column("Доля", justify="right")

        for key, label in [
            ("system", "System prompt"),
            ("tools", "Tools (JSON Schema)"),
            ("history", "History"),
            ("user", "User messages"),
        ]:
            comp = breakdown[key]
            table.add_row(label, str(comp.tokens), f"{comp.percent:.2f}%")

        console.print(table)
        console.print()

        tools_stats = self.get_tools_stats()
        if tools_stats:
            tools_table = Table(title="ТОП-5 самых \"тяжёлых\" tools", show_header=True, header_style="bold")
            tools_table.add_column("Tool")
            tools_table.add_column("Токены", justify="right")
            tools_table.add_column("Доля", justify="right")

            for name, info in sorted(
                tools_stats.items(),
                key=lambda kv: kv[1]["tokens"],
                reverse=True,
            )[:5]:
                tools_table.add_row(
                    name,
                    str(info["tokens"]),
                    f"{info['percent']:.2f}%",
                )

            console.print(tools_table)

    def print_top_expensive(self, n: int = 10) -> None:
        """Вывести список N самых дорогих запросов."""
        console = self.console
        entries = self.get_top_expensive_requests(n)
        if not entries:
            console.print("Нет записей в логах.")
            return

        table = Table(title=f"Топ-{n} самых дорогих запросов", show_header=True, header_style="bold")
        table.add_column("Время")
        table.add_column("Токены", justify="right")
        table.add_column("Стоимость, ₽", justify="right")
        table.add_column("Провайдер")
        table.add_column("Модель")

        for e in entries:
            total = e.get("total") or {}
            meta = e.get("metadata") or {}
            table.add_row(
                e.get("timestamp", ""),
                str(total.get("total_tokens_estimate", "")),
                f"{float(total.get('cost_estimate_rub', 0.0)):.2f}",
                str(meta.get("provider", "")),
                str(meta.get("model", "")),
            )

        console.print(table)

    def print_component_breakdown(self, component: str) -> None:
        """Вывести подробную статистику по одному компоненту: system|history|user|tools."""
        component = component.lower()
        if component not in {"system", "history", "user", "tools"}:
            self.console.print(f"Неизвестный компонент: {component}")
            return

        breakdown = self.get_breakdown_by_component()
        comp = breakdown[component]
        self.console.print(
            f"[bold]{component}[/bold]: токенов={comp.tokens}, доля={comp.percent:.2f}%"
        )

