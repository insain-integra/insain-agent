# Интеграция с WordPress

## Текущее состояние

На сайте insain.ru установлен плагин **ez Form Calculator for WordPress**.
Формы калькуляторов уже созданы через этот плагин.

Текущий процесс:
Пользователь заполняет форму
→ ez Form Calculator вызывает JS-функцию (calcLaser.js)
→ JS считает результат локально
→ Результат отображается в полях формы

Ограничения:
- Нет share URL (ссылки с заполненными параметрами)
- Менеджер не может отправить клиенту ссылку на готовый расчёт

## Целевое состояние
Пользователь заполняет форму
→ JS-обёртка делает fetch к Python API
→ POST https://calc.insain.ru/api/v1/calc/{slug}
→ Результат отображается в форме
→ URL обновляется GET-параметрами

Менеджер копирует URL → отправляет клиенту

Клиент открывает ссылку:
→ JS читает GET-параметры
→ Форма заполняется автоматически
→ Расчёт запускается
→ Клиент видит результат, может менять параметры

## Что нужно сделать

### 1. Установить мини-плагин

`wp-plugin/insain-calc-bridge.php` → загрузить в WordPress.
Подключает JS-скрипт на страницах с калькуляторами.

### 2. Заменить вызовы JS-калькуляторов

В настройках ez Form Calculator для каждой формы:
- Было: вызов `calcLaser(params)`
- Стало: вызов `insainCalc("laser", params)`

### 3. Функции JS-обёртки

insainCalc(slug, params) — fetch POST к API, вернуть результат
updateURLParams(params) — URL ← параметры формы (history.replaceState)
readURLParams() — URL → параметры
prefillForm(slug, params) — параметры → поля формы
displayResult(result) — результат → поля формы
DOMContentLoaded — при загрузке: если есть GET-параметры →
заполнить форму → запустить расчёт
## Файлы
wp-plugin/
├── insain-calc-bridge.php — мини-плагин WordPress
├── js/insain-calc-bridge.js — fetch + URL параметры + pre-fill
└── css/insain-calc-bridge.css — стили (опционально)

## Как работает share_url

### Через сайт
Менеджер заполняет форму → URL обновляется:
.../calculator/laser/?material=PVC3&width=300&quantity=100
Менеджер копирует URL → отправляет клиенту
Клиент открывает → форма заполнена → расчёт выполнен
### Через Telegram бота
Менеджер: "Посчитай лазерную резку ПВХ 3мм, 300×200, 100 штук"
Бот → API → результат:
— Цена: 15 000 ₽
— Время: 2.5 ч, готовность: 10.5 ч
— Ссылка: https://insain.ru/calculator/laser/?material=PVC3&...
Менеджер пересылает ссылку клиенту

## Маппинг полей

Для каждого калькулятора нужен маппинг:
имя GET-параметра ↔ ID поля в ez Form Calculator.

Через data-атрибуты в HTML:
```html
<div data-calc-slug="laser"
     data-calc-field-map='{"material":"#field-123","width":"#field-124"}'>
CORS
Python

# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://insain.ru", "https://www.insain.ru"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```