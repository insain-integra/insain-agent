import json5
import os

# Проверяем путь относительно корня проекта
path = "calc_service/data/materials/hardsheet.json"

if os.path.exists(path):
    print(f"Файл найден: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json5.load(f)
        print("✅ УСПЕХ! JSON5 прочитан корректно.")
        print("Ключи верхнего уровня:", list(data.keys()))
    except Exception as e:
        print(f"❌ ОШИБКА чтение JSON: {e}")
else:
    print(f"❌ ОШИБКА: Файл не найден по пути {path}")
    print("Текущая директория:", os.getcwd())