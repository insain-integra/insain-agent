# Сборка: из корня репозитория — docker build -t insain-calc -f calc_service/Dockerfile calc_service/
# или из этой папки: docker build -t insain-calc .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Как в репозитории: calc_service/ внутри /app — чтобы Path(__file__).parents[2] в config.py был валиден
WORKDIR /app/calc_service

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

# JSON без пересборки: docker run -v ./calc_service/data:/app/calc_service/data ...
VOLUME ["/app/calc_service/data"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
