# Локальная разработка: calc_service (uvicorn) и Telegram-бот.
# Требуется: GNU make + Python 3.10+ в PATH (лучше venv).
#
# Если команды `make` нет (часто в Git Bash / cmd без отдельной установки):
#   python scripts/dev.py start all
#   bash scripts/dev.sh start all
# Установка make (Windows): winget install GnuWin32.Make  или  choco install make
#
# Примеры:
#   make up          — API + бот
#   make down        — остановить оба
#   make status
#   make calc-up | calc-down | bot-up | bot-down

PYTHON ?= python
DEV = $(PYTHON) scripts/dev.py

.PHONY: help up down restart status calc-up calc-down bot-up bot-down

help:
	@echo "make up | down | restart | status"
	@echo "make calc-up | calc-down | bot-up | bot-down"

up:
	$(DEV) start all

down:
	$(DEV) stop all

restart:
	$(DEV) restart all

status:
	$(DEV) status

calc-up:
	$(DEV) start calc

calc-down:
	$(DEV) stop calc

bot-up:
	$(DEV) start bot

bot-down:
	$(DEV) stop bot
