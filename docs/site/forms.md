# Реестр форм ezFC

Снято 2026-10-25, только чтение. WordPress не менялся.

Источник строки: товар WooCommerce с непустым meta `ezfc_form_id` (permalink). Формы без товара — строка с пустой страницей. Custom JS — `wp_insain_ezfc_forms_elements.data`. Список slug — `GET https://insain.ru/api/v1/calculators` (38 публичных).

Статус по вызову в custom JS, не по имени формы:

- есть `insaincalc.calcApi('slug', …)` — API, в колонке slug тот аргумент;
- нет `calcApi`, но есть `insaincalc.calc…` (служебный `insaincalc.calcDateReady` не считается) — старый JS, имя функции из кода;
- такого вызова нет — не калькулятор.

Slug из имени функции (`calcLaser` → `laser`) не подставлялся: в JS этих форм строкового slug нет.

| Страница (URL) | Форма ezFC | slug API | Статус |
|---|---|---|---|
| https://insain.ru/catalog/listovki-pod-zakaz/ (Листовки под заказ) | 6 CalcPrint | — | старый JS `insaincalc.calcPrintSheet` |
| — | 10 _ExternalTest | — | старый JS `insaincalc.calc_fun1`, `insaincalc.calc_fun2`, `insaincalc.calc_fun3` |
| https://insain.ru/catalog/znachki-zakatnye-kruglye/ (Значки закатные круглые) | 12 CalcButtonPins | — | старый JS `insaincalc.calcButtonPins` |
| https://insain.ru/catalog/vizitki/ (Визитки) | 19 CalcCards | — | старый JS `insaincalc.calcPrintSheet` |
| https://insain.ru/catalog/plotternaya-rezka/ (Плоттерная резка) | 22 CalcSticker | — | старый JS `insaincalc.calcSticker` |
| https://insain.ru/catalog/shirokoformatnaya-pechat-na-zakaz/ (Широкоформатная печать на заказ) | 23 CalcPrintWide | — | старый JS `insaincalc.calcPrintRoll` |
| https://insain.ru/catalog/uf-pechat-na-suveniry/ (УФ-печать на сувениры) | 26 CalcUVPrint | — | старый JS `insaincalc.calcUVPrint` |
| https://insain.ru/catalog/lazernaya-gravirovka-i-rezka/ (Лазерная гравировка и резка) | 28 CalcLaser | — | старый JS `insaincalc.calcLaser` |
| https://insain.ru/catalog/stikerpak/ (Стикерпак) | 29 CalcStickerPack | — | старый JS `insaincalc.calcSticker` |
| https://insain.ru/catalog/naklejki-s-polimernoj-zalivkoj/ (Наклейки с полимерной заливкой) | 30 CalcPolySticker | — | старый JS `insaincalc.calcPolySticker` |
| https://insain.ru/catalog/bejdzhi-s-polimernoj-zalivkoj/ (Бейджи с полимерной заливкой) | 31 CalcPolyBadge | — | старый JS `insaincalc.calcBadge` |
| https://insain.ru/catalog/znachki-metallicheskie-s-emalyami/ (Значки металлические с эмалями) | 34 CalcMetalPins | — | старый JS `insaincalc.calcMetalPins` |
| https://insain.ru/catalog/frezerovka-listovyh-materialov/ (Фрезеровка листовых материалов) | 35 CalcMilling | — | старый JS `insaincalc.calcMilling` |
| https://insain.ru/catalog/tablichki-s-uf-pechatyu/ (Калькулятор табличек) | 36 CalcTabs | — | старый JS `insaincalc.calcTablets` |
| https://insain.ru/catalog/tampopechat/ (Тампопечать) | 38 CalcPadPrint | — | старый JS `insaincalc.calcPadPrint` |
| https://insain.ru/catalog/kalkulyator-naneseniya-na-odezhdu/ (Калькулятор нанесения на одежду) | 40 CalcHeatPress | — | старый JS `insaincalc.calcHeatPress` |
| https://insain.ru/catalog/kalkulyator-sublimaczionnoj-pechati-na-kruzhki/ (Калькулятор сублимационной печати на кружки) | 41 CalcMug | — | старый JS `insaincalc.calcMug` |
| https://insain.ru/catalog/kalkulyator-bloknotov/ (Калькулятор блокнотов) | 45 CalcNotebook | — | старый JS `insaincalc.calcNotebook` |
| https://insain.ru/catalog/kalkulyator-pressvolov/ (Калькулятор прессволов) | 46 CalcPresswall | — | старый JS `insaincalc.calcPresswall` |
| https://insain.ru/catalog/kalkulyator-stendov/ (Калькулятор стендов) | 48 CalcStands | — | старый JS `insaincalc.calcTablets` |
| https://insain.ru/catalog/kalkulyator-rollapov/ (Калькулятор роллапов) | 49 CalcRollup | — | старый JS `insaincalc.calcRollup` |
| https://insain.ru/catalog/kalkulyator-kvartalnyh-kalendarej/ (Калькулятор квартальных календарей) | 50 CalcCalendarQuarterly | — | старый JS `insaincalc.calcCalendarQuarterly` |
| https://insain.ru/catalog/kalkulyator-heshtegov/ (Калькулятор хештегов) | 51 CalcHashtags | — | старый JS `insaincalc.calcTablets` |
| https://insain.ru/catalog/kalkulyator-perekidnyh-kalendarej/ (Калькулятор перекидных календарей) | 52 CalcCalendarFlip | — | старый JS `insaincalc.calcCalendarFlip` |
| https://insain.ru/catalog/kulkulyator-magnitov-vinilovyh/ (Калькулятор магнитов виниловых) | 54 CalcMagnetLamination | — | старый JS `insaincalc.calcMagnetLamination` |
| https://insain.ru/catalog/kalkulyator-flazhkov-bumazhnyh/ (Калькулятор флажков бумажных) | 55 CalcFlagPaper | — | старый JS `insaincalc.calcFlagPaper` |
| https://insain.ru/catalog/kalkulyator-plastikovyh-kart/ (Калькулятор пластиковых карт) | 56 CalcPlasticCards | — | старый JS `insaincalc.calcPlasticCards` |
| https://insain.ru/catalog/magnity-polimernye/ (Магниты полимерные) | 57 CalcMagnetPoly | — | старый JS `insaincalc.calcMagnetLamination` |
| https://insain.ru/catalog/znachki-polimernye/ (Значки полимерные) | 60 CalcPolyPin | — | старый JS `insaincalc.calcBadge` |
| https://insain.ru/catalog/znachki-plastikovye-s-gravirovkoj/ (Значки пластиковые с гравировкой) | 61 CalcPins | — | старый JS `insaincalc.calcBadge` |
| https://insain.ru/catalog/znachki-plastikovye-s-uf-pechatyu/ (Значки пластиковые с УФ-печатью) | 61 CalcPins | — | старый JS `insaincalc.calcBadge` |
| https://insain.ru/catalog/znachki-derevyannye/ (Значки деревянные) | 61 CalcPins | — | старый JS `insaincalc.calcBadge` |
| https://insain.ru/catalog/bejdzhi-s-uf-pechatyu/ (Бейджи с УФ-печатью) | 64 CalcBadge | — | старый JS `insaincalc.calcBadge` |
| https://insain.ru/catalog/bejdzhi-s-lazernoj-gravirovkoj/ (Бейджи с лазерной гравировкой) | 64 CalcBadge | — | старый JS `insaincalc.calcBadge` |
| https://insain.ru/catalog/kalkulyator-nastolnyh-perekidnyh-kalendarej/ (Калькулятор настольных перекидных календарей) | 66 CalcCalendarTable | — | старый JS `insaincalc.calcCalendarTableFlip` |
| https://insain.ru/catalog/kalkulyator-shildov/ (Калькулятор шильдов) | 68 CalcShild | — | старый JS `insaincalc.calcTablets` |
| https://insain.ru/catalog/kalkulyator-nagradnyh-plaketok/ (Калькулятор наградных плакеток) | 69 CalcPlaque | — | старый JS `insaincalc.calcPlaque` |
| https://insain.ru/catalog/stikerpaki-s-polimernoj-zalivkoj/ (Стикерпаки с полимерной заливкой) | 70 CalcPolyStickerPack | — | старый JS `insaincalc.calcPolyStickerPack` |
| — | 71 setStickers | — | не калькулятор |
| — | 72 setPockets | — | не калькулятор |
| https://insain.ru/catalog/kalkulyator-vympelov-bumazhnyh/ (Калькулятор вымпелов бумажных) | 73 CalcPennantPaper | — | старый JS `insaincalc.calcPennantPaper` |
| https://insain.ru/catalog/kalkulyator-akrilovyh-brelokov/ (Калькулятор акриловых брелоков) | 74 CalcАcrylicKeychains | — | старый JS `insaincalc.calcAcrylicKeychain` |
| https://insain.ru/catalog/akrilovye-magnity/ (Акриловые магниты) | 75 CalcАcrylicMagnets | — | старый JS `insaincalc.calcAcrylicMagnets` |
| https://insain.ru/catalog/transparanty-bessmertnyj-polk/ (Транспаранты Бессмертный полк) | 76 CalcTabs9May | — | старый JS `insaincalc.calcTablets` |
| — | 77 setLayers | — | не калькулятор |
| https://insain.ru/catalog/kalkulyator-akrilovyh-prizov/ (Калькулятор акриловых призов) | 78 CalcAcrilycPrizes | — | старый JS `insaincalc.calcAcrilycPrizes` |
| https://insain.ru/catalog/kalkulyator-pazlov/ (Калькулятор пазлов) | 79 CalcPuzzle | puzzle | API через `insaincalc.calcApi` |
| https://insain.ru/catalog/canvas/ (Печать на холсте) | 80 CalcCanvas | — | старый JS `insaincalc.calcCanvas` |
| https://insain.ru/catalog/listovki-po-akczii/ (Листовки по акции) | 82 CalcPrintPromo | — | старый JS `insaincalc.calcPrintOffsetPromo` |
| https://insain.ru/catalog/vizitki-po-akczii/ (Визитки по акции) | 83 CalcCardPromo | — | старый JS `insaincalc.calcPrintOffsetPromo` |
| https://insain.ru/catalog/bejdzhi-laminirovannye/ (Бейджи ламинированные) | 84 CalcBadgeLamination | — | старый JS `insaincalc.calcBadge` |
| https://insain.ru/catalog/kalkulyator-tisneniya/ (Калькулятор тиснения) | 85 CalcEmbossing | — | старый JS `insaincalc.calcEmbossing` |

В названиях форм 74 и 75 буква «А» кириллическая (`U+0410`): `CalcАcrylicKeychains`, `CalcАcrylicMagnets`.

Форма 79 считает через `insaincalc.calcApi('puzzle', …)` (элемент 3108). В скрытом HTML-элементе 3101 остаются теги `/icalc/calc/icdc_ls.js` и `/icalc/calc/common.js`. На странице пазлов вызов `calcApi('puzzle'` есть. У форм старого JS в элементах есть `insaincalc.loadData(…/icalc/…)`. У 10, 71, 72, 77 подстроки `icalc` нет.

## Итог

Форм ezFC: 49. Опубликованных товаров с формой: 48 (форма 61 на трёх товарах, форма 64 на двух).

| Статус | Форм | Опубликованных страниц |
|---|---:|---:|
| API через `insaincalc.calcApi` | 1 | 1 |
| старый JS `insaincalc.calc…` | 45 | 47 |
| не калькулятор | 3 | 0 |

Непереведённых форм: **45** (вызова `calcApi` нет). 44 из них на опубликованных товарах. Ещё одна — `_ExternalTest` (id 10), страницы нет. Не калькуляторы без страницы: `setStickers` (71), `setPockets` (72), `setLayers` (77).

К форме через `calcApi` привязан один slug: `puzzle`.

Не привязаны ни к одной форме (37 из 38): `laser`, `cut_plotter`, `cut_roller`, `milling`, `lamination`, `print_sheet`, `print_wide`, `print_inkjet`, `print_roll`, `print_offset`, `sticker`, `poly_sticker`, `poly_sticker_pack`, `uv_print`, `uv_badge`, `cards`, `mug`, `keychain`, `flag`, `pennant`, `rollup`, `design`, `presswall`, `notebook`, `metal_pins`, `acrylic_prizes`, `embossing`, `pad_print`, `magnet_acrylic`, `magnet_laminated`, `badge`, `calendar`, `heat_press`, `canvas`, `tablets`, `shild`, `plaque`.

Вне таблицы, форм нет. Черновик товара 4893 «Шаблон товара» ссылается на `ezfc_form_id` 44, такой формы нет. Страница https://insain.ru/sample-page/ содержит шорткод `[ezfc id='13' /]`, формы 13 нет. У 9 опубликованных товаров meta `ezfc_form_id` пустое: магниты деревянные, шесть шоколадов с логотипом (5/12/15/20/50/100 г), баннеры, фотообои.
