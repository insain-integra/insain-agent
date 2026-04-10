# Сборка: docker build -t insain-bot -f bot_service/Dockerfile bot_service/
#
# Код ожидает структуру как в репозитории: родитель каталога bot_service — корень проекта
# (PROJECT_ROOT в knowledge_base, token_analyzer; calc_service/data/common.json у agent).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/insain

COPY requirements.txt ./bot_service/
RUN pip install --no-cache-dir -r bot_service/requirements.txt

COPY . ./bot_service/

WORKDIR /opt/insain/bot_service

# Логи токенов: docker run -v ./logs:/opt/insain/logs ...
VOLUME ["/opt/insain/logs"]

CMD ["python", "bot.py"]
