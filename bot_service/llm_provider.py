"""
Провайдер LLM с тремя режимами работы:

1) mixed        — основной Google Gemini (через OpenAI-совместимый API, с tools),
                   при любых проблемах с Gemini автоматический fallback на YandexGPT.
2) gemini       — только Gemini.
3) yandex       — только YandexGPT (нативный API Yandex Cloud, без tools).

Режим задаётся переменной окружения LLM_MODE в .env: mixed | gemini | yandex.
По умолчанию используется mixed.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

def _load_env() -> None:
    """Загрузить .env из корня проекта."""
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if not _env_path.is_file():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path)
    except ImportError:
        # Без python-dotenv: читаем .env вручную
        with open(_env_path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip().strip("'\"").strip()
                    if k and k not in os.environ:
                        os.environ[k] = v


_load_env()

from openai import OpenAI

logger = logging.getLogger(__name__)

# Конфиг из .env (поддержка обоих имён переменной)
GOOGLE_API_KEY = (
    os.getenv("GOOGLE_API_KEY", "").strip()
    or os.getenv("GEMINI_API_KEY", "").strip()
)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

# Режим работы LLM: mixed | gemini | yandex
LLM_MODE = os.getenv("LLM_MODE", "mixed").strip().lower() or "mixed"
if LLM_MODE not in ("mixed", "gemini", "yandex"):
    LLM_MODE = "mixed"

# Таймаут запроса к API, секунды
CHAT_TIMEOUT = 30

# YandexGPT fallback
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "").strip()
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID", "").strip()
YANDEX_MODEL_URI = f"gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest" if YANDEX_FOLDER_ID else ""
YANDEX_COMPLETION_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"


def _is_quota_error(exc: BaseException) -> bool:
    """Проверить, что ошибка — исчерпание квоты (429)."""
    msg = str(exc).lower()
    return "429" in str(exc) or "quota" in msg or "resource_exhausted" in msg


class YandexGPTProvider:
    """
    YandexGPT через нативный API Yandex Cloud.
    Поддерживает только текстовый ответ (tools не передаются в API).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        folder_id: Optional[str] = None,
        model_uri: Optional[str] = None,
        timeout: float = CHAT_TIMEOUT,
    ):
        self.api_key = (api_key or YANDEX_API_KEY).strip()
        self.folder_id = (folder_id or YANDEX_FOLDER_ID).strip()
        self.model_uri = model_uri or (f"gpt://{self.folder_id}/yandexgpt/latest" if self.folder_id else "")
        self.timeout = timeout

    def _is_available(self) -> bool:
        return bool(self.api_key and self.model_uri)

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Запрос к YandexGPT. tools игнорируются (API не поддерживает в том же формате).
        Возвращает {"content": str, "tool_calls": None}.
        """
        if not self._is_available():
            raise ValueError("YANDEX_API_KEY и YANDEX_FOLDER_ID не заданы для fallback.")

        # Конвертация формата: role + content -> role + text
        yandex_messages = []
        for m in messages:
            role = (m.get("role") or "user").lower()
            if role == "system":
                role = "user"
            text = m.get("content") or ""
            if isinstance(text, list):
                text = " ".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in text
                )
            if not text.strip():
                continue
            yandex_messages.append({"role": role, "text": text})

        if not yandex_messages:
            return {"content": None, "tool_calls": None}

        body = {
            "modelUri": self.model_uri,
            "messages": yandex_messages,
            "completionOptions": {
                "temperature": 0.6,
                "maxTokens": 2000,
            },
        }

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info("YandexGPT request: messages=%s", len(yandex_messages))

        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.post(YANDEX_COMPLETION_URL, json=body, headers=headers)
                r.raise_for_status()
                data = r.json()
        except httpx.HTTPStatusError as e:
            logger.warning("YandexGPT API error: %s", e)
            raise RuntimeError(f"YandexGPT: {e.response.text or str(e)}") from e
        except Exception as e:
            logger.exception("YandexGPT request error: %s", e)
            raise RuntimeError(f"YandexGPT: {e}") from e

        # result.alternatives[0].message.text
        result = data.get("result") or {}
        alternatives = result.get("alternatives") or []
        if not alternatives:
            return {"content": None, "tool_calls": None}
        text = (alternatives[0].get("message") or {}).get("text") or ""
        logger.info("YandexGPT response: content_len=%s", len(text))
        return {"content": text.strip() or None, "tool_calls": None}


class LLMProvider:
    """
    Обёртка над основными моделями:

    - Режим mixed  (по умолчанию): сначала Gemini, при любой ошибке — fallback на YandexGPT
      (если заданы YANDEX_API_KEY и YANDEX_FOLDER_ID).
    - Режим gemini: только Gemini, ошибки не перехватываются.
    - Режим yandex: только YandexGPT, Gemini не вызывается.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/",
        timeout: float = CHAT_TIMEOUT,
        fallback_provider: Optional[YandexGPTProvider] = None,
        mode: Optional[str] = None,
    ):
        self.api_key = (api_key or GOOGLE_API_KEY).strip()
        self.model = (model or GEMINI_MODEL).strip() or GEMINI_MODEL
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self._client: Optional[OpenAI] = None
        self._fallback = fallback_provider if fallback_provider is not None else YandexGPTProvider()
        mode_value = (mode or LLM_MODE).strip().lower()
        if mode_value not in ("mixed", "gemini", "yandex"):
            mode_value = "mixed"
        self.mode = mode_value

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            key = self.api_key or os.getenv("GOOGLE_API_KEY", "").strip() or os.getenv("GEMINI_API_KEY", "").strip()
            if not key:
                raise ValueError(
                    "GOOGLE_API_KEY не задан. Добавьте в .env в корне проекта: GOOGLE_API_KEY=ваш_ключ"
                )
            self._client = OpenAI(
                api_key=key,
                base_url=self.base_url,
            )
        return self._client

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Один вызов chat completions.

        :param messages: список {"role": "user"|"assistant"|"system", "content": "..."}
        :param tools: опционально список tool definitions для function calling
        :return: сообщение ответа: {"content": str|None, "tool_calls": list|None}
        """
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "timeout": self.timeout,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        # Режим "только Yandex" — сразу уходим в fallback
        if self.mode == "yandex":
            logger.info("LLM request: mode=yandex, messages=%s", len(messages))
            if not self._fallback._is_available():
                raise ValueError("YandexGPT недоступен: проверьте YANDEX_API_KEY и YANDEX_FOLDER_ID в .env")
            return self._fallback.chat(messages, tools=tools)

        logger.info("LLM request: mode=%s, model=%s, messages=%s", self.mode, self.model, len(messages))

        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            # В смешанном режиме при любой ошибке Gemini пробуем YandexGPT
            if self.mode == "mixed" and self._fallback._is_available():
                logger.warning("Gemini error (mode=mixed), переключаюсь на YandexGPT: %s", e)
                return self._fallback.chat(messages, tools=tools)

            logger.exception("LLM API error: %s", e)
            err_msg = str(e)
            if "timeout" in err_msg.lower() or "timed out" in err_msg.lower():
                raise ConnectionError("Таймаут запроса к модели. Попробуйте позже.") from e
            if "api_key" in err_msg.lower() or "401" in err_msg or "403" in err_msg:
                raise ValueError("Неверный или отсутствующий API-ключ Google.") from e
            raise RuntimeError(f"Ошибка API: {err_msg}") from e

        choice = (response.choices or [None])[0]
        if not choice:
            raise RuntimeError("Пустой ответ от модели")

        msg = choice.message
        out: Dict[str, Any] = {"content": None, "tool_calls": None}
        if getattr(msg, "content", None):
            out["content"] = msg.content
        if getattr(msg, "tool_calls", None) and len(msg.tool_calls) > 0:
            out["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": getattr(tc, "type", "function"),
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
        logger.info("LLM response: has_content=%s, tool_calls=%s", out["content"] is not None, len(out["tool_calls"] or []))
        return out

    def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
    ) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
        """
        Один раунд с поддержкой function calling.

        Отправляет messages и tools. Если модель вернула tool_calls —
        возвращает (None, tool_calls). Если вернула текстовый content —
        возвращает (content, None).

        :param messages: история сообщений
        :param tools: список инструментов (OpenAI tool format)
        :return: (content, None) или (None, tool_calls)
        """
        result = self.chat(messages, tools=tools)
        content = result.get("content")
        tool_calls = result.get("tool_calls")
        if tool_calls:
            return (None, tool_calls)
        return (content, None)
