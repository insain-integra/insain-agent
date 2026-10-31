/**
 * Мост ez Form Calculator → Python calc_service.
 *
 * Методы вешаются на уже существующий объект insaincalc
 * (его создаёт /icalc/calc/icdc_ls.js; если скрипт ещё не загружен — создаём пустой).
 *
 *   insaincalc.calcApi(slug, params)     — POST /api/v1/calc/{slug}, ответ в формате calcCost
 *   insaincalc.showResult(calcCost, qty, formId) — цена, вес, срок, материалы
 *   insaincalc.showError(err, formId)    — текст ошибки в блоке срока
 *   insaincalc.syncUrl(params)           — query-строка, имена = GET полей формы
 *
 * Сбор параметров формы остаётся в custom JS. Расчёт и вывод вызываются отдельно.
 */
(function () {
    'use strict';

    var calc = window.insaincalc || (window.insaincalc = {});
    var cfg = window.InsainCalcBridgeConfig || {};
    var API = String(cfg.apiBase || '/api/v1').replace(/\/+$/, '');
    var requestSeq = {};

    function formRoot(formId) {
        if (formId) {
            var root = document.getElementById('ezfc-form-' + formId);
            if (root) {
                return root;
            }
        }
        return document;
    }

    function setNamedAmount(formId, name, number) {
        if (typeof ezfc_functions === 'undefined' || !ezfc_functions.get_element_id_by_name) {
            return;
        }
        var id = ezfc_functions.get_element_id_by_name(formId || null, name);
        if (!id) {
            return;
        }
        var field = document.querySelector('#ezfc_element-' + id);
        if (!field) {
            return;
        }
        var caption = field.querySelector('.ezfc-text');
        if (caption) {
            caption.textContent = String(number);
        }
        var hiddenInput = field.querySelector('input.ezfc-element-subtotal');
        if (hiddenInput) {
            hiddenInput.value = number;
        }
    }

    function adaptLegacyResult(result) {
        result = result || {};

        var material = new Map();
        (result.materials || []).forEach(function (item) {
            var code = item.code || item.id;
            if (!code) {
                return;
            }
            material.set(code, [
                item.name || item.title || '',
                item.size_mm || item.size || null,
                item.quantity || item.quantity_approx || 0
            ]);
        });

        return {
            cost: result.cost || 0,
            price: result.price || 0,
            unit_price: result.unit_price || 0,
            time: result.time_hours || 0,
            timeReady: result.time_ready || 0,
            weight: result.weight_kg || 0,
            material: material,
            materials: result.materials || [],
            share_url: result.share_url || '',
            raw: result
        };
    }

    function postCalc(slug, params) {
        return fetch(API + '/calc/' + slug, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify(params || {})
        }).then(function (res) {
            return res.json().catch(function () {
                return null;
            }).then(function (data) {
                if (!res.ok) {
                    var message = data && (data.detail || data.error || data.message);
                    throw new Error(message || ('Ошибка API ' + res.status));
                }
                return data;
            });
        });
    }

    function calcApi(slug, params) {
        requestSeq[slug] = (requestSeq[slug] || 0) + 1;
        var reqId = requestSeq[slug];
        return postCalc(slug, params).then(function (data) {
            if (reqId !== requestSeq[slug]) {
                return null;
            }
            return adaptLegacyResult(data);
        }, function (err) {
            if (reqId !== requestSeq[slug]) {
                return null;
            }
            throw err;
        });
    }

    function syncUrl(params) {
        if (!window.history || !window.URL) {
            return;
        }
        var url = new URL(window.location.href);
        Object.keys(params || {}).forEach(function (key) {
            var value = params[key];
            if (value === undefined || value === null || value === '') {
                url.searchParams.delete(key);
            } else {
                url.searchParams.set(key, value);
            }
        });
        window.history.replaceState({}, '', url.toString());
    }

    function showError(err, formId) {
        var timeBlock = formRoot(formId).getElementsByClassName('htmTime')[0];
        if (timeBlock && timeBlock.getElementsByTagName('div')[0]) {
            timeBlock.getElementsByTagName('div')[0].innerHTML = 'Ошибка: ' + (err && err.message ? err.message : err);
        }
        console.error('InsainCalcBridge:', err);
    }

    function showResult(calcCost, qty, formId) {
        if (!calcCost) {
            return;
        }
        var n = Number(qty) || 1;
        var marginMin = (calc.common && calc.common.marginMin) || 0;
        var price = calc.round ? calc.round(calcCost.price, n) : Math.ceil(calcCost.price || 0);
        var discount = Math.ceil((calcCost.cost || 0) * (1 + marginMin));
        var cost = Math.ceil(calcCost.cost || 0);
        var weight = Math.round((calcCost.weight || 0) * 100) / 100;
        var unit = function (total) {
            return n ? Math.round(total / n * 100) / 100 : total;
        };

        window.PriceTotalManager = price;
        window.PriceTotalDiscount = discount;
        window.CostTotal = cost;
        window.WeightTotal = weight;

        setNamedAmount(formId, 'sbtPriceTotalManager', price);
        setNamedAmount(formId, 'sbtPriceManager', unit(price));
        setNamedAmount(formId, 'sbtPriceTotalDiscount', discount);
        setNamedAmount(formId, 'sbtPriceDiscount', unit(discount));
        setNamedAmount(formId, 'sbtCostTotal', cost);
        setNamedAmount(formId, 'sbtCost', unit(cost));
        setNamedAmount(formId, 'sbtWeightTotal', weight);

        var root = formRoot(formId);
        if (calc.timeToWords && calc.calcDateReady) {
            var timeReady = calc.timeToWords(calcCost.timeReady);
            var dateReady = calc.calcDateReady(calcCost.timeReady);
            var timeBlock = root.getElementsByClassName('htmTime')[0];
            if (timeBlock) {
                timeBlock.getElementsByTagName('div')[0].innerHTML = 'Срок ' + timeReady;
                var hint = timeBlock.getElementsByTagName('a')[0];
                if (hint) {
                    hint.setAttribute(
                        'data-bs-original-title',
                        'Готовность заказа: ' + dateReady[1] + ' При запуске заказа в работу до: ' + dateReady[0]
                    );
                }
            }
        }

        var materialsTable = root.getElementsByClassName('data-material-table')[0];
        if (materialsTable && calc.showMaterials && calcCost.material) {
            materialsTable.innerHTML = calc.showMaterials(calcCost.material);
        }
    }

    calc.calcApi = calcApi;
    calc.showResult = showResult;
    calc.showError = showError;
    calc.syncUrl = syncUrl;
}());
