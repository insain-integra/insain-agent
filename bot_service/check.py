import sys
sys.path.insert(0, "../calc_service")

try:
    from llm_provider import LLMProvider
except ModuleNotFoundError as e:
    if "openai" in str(e):
        print("Установите зависимости бота: pip install -r bot_service/requirements.txt")
        print("или: pip install openai")
    raise SystemExit(1) from e

llm = LLMProvider()
messages = [{"role": "user", "content": "Скажи привет одним предложением"}]
response = llm.chat(messages)
print(f"Ответ: {response}")
