from calculators.laser import LaserCalculator

calc = LaserCalculator()
print(f"slug: {calc.slug}")
print(f"name: {calc.name}")

# Получить опции
options = calc.get_options()
print(f"\nМатериалы: {len(options.get('materials', []))} вариантов")
if options.get("materials"):
    print(f"  первый: {options['materials'][0]}")

# Получить schema
schema = calc.get_tool_schema()
print(f"\nSchema name: {schema['name']}")

# Тестовый расчёт — подставь реальный код материала
# Посмотри в options какие материалы доступны
for m in options.get("materials", [])[:1]:
    code = m["code"]
    print(f"\n--- Расчёт для {code} ---")
    params = {
        "quantity": 10,
        "width_mm": 200,
        "height_mm": 150,
        "material_code": code,
        "mode": 1,
    }
    try:
        result = calc.execute(params)
        print(f"  cost: {result['cost']:.2f}")
        print(f"  price: {result['price']:.2f}")
        print(f"  unit_price: {result['unit_price']:.2f}")
        print(f"  time_hours: {result['time_hours']:.4f}")
        print(f"  time_ready: {result['time_ready']:.2f}")
        print(f"  weight_kg: {result['weight_kg']:.3f}")
        print(f"  materials: {result['materials']}")
        print(f"  share_url: {result['share_url'][:80]}...")
    except Exception as e:
        print(f"  ОШИБКА: {e}")