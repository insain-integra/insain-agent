(function () {
    'use strict';

    const DEFAULT_CONFIG = {
        apiBase: '/api/v1',
        autoInit: true,
        debounceMs: 350,
        products: {
            puzzle: {
                productSlug: 'puzzle',
                calcSlug: 'puzzle',
                pagePathIncludes: 'kalkulyator-pazlov',
                inputSelectors: {
                    quantity: [
                        '#ezfc_element-3103',
                        '#ezfc_element_3103',
                        '[name="numn"]',
                        '[name$="[numn]"]',
                        '[data-element-name="numn"]',
                        '[data-ezfc-id="3103"]',
                    ],
                    puzzle_id: [
                        '#ezfc_element-3104',
                        '#ezfc_element_3104',
                        '[name="dpdformat"]',
                        '[name$="[dpdformat]"]',
                        '[data-element-name="dpdformat"]',
                        '[data-ezfc-id="3104"]',
                    ],
                },
                selectCodeMap: {
                    puzzle_id: {
                        0: 'Puzzle300420',
                        1: 'Puzzle208298',
                        2: 'Puzzle159215',
                    },
                },
                resultSelectors: {},
            },
        },
    };

    const globalConfig = window.InsainCalcBridgeConfig || {};
    const config = mergeConfig(DEFAULT_CONFIG, globalConfig);
    const productCache = new Map();
    const lastRequestByProduct = new Map();

    function mergeConfig(base, override) {
        const out = Array.isArray(base) ? base.slice() : Object.assign({}, base);
        Object.keys(override || {}).forEach((key) => {
            const baseValue = out[key];
            const overrideValue = override[key];
            if (isPlainObject(baseValue) && isPlainObject(overrideValue)) {
                out[key] = mergeConfig(baseValue, overrideValue);
            } else {
                out[key] = overrideValue;
            }
        });
        return out;
    }

    function isPlainObject(value) {
        return Object.prototype.toString.call(value) === '[object Object]';
    }

    function joinUrl(base, path) {
        return String(base || '').replace(/\/+$/, '') + '/' + String(path || '').replace(/^\/+/, '');
    }

    function selectFirst(selectors, root) {
        const scope = root || document;
        const list = Array.isArray(selectors) ? selectors : [selectors];

        for (const selector of list) {
            if (!selector) {
                continue;
            }
            try {
                const element = scope.querySelector(selector);
                if (element) {
                    return element;
                }
            } catch (err) {
                console.warn('InsainCalcBridge: некорректный selector', selector, err);
            }
        }

        return null;
    }

    function getFieldValue(element) {
        if (!element) {
            return '';
        }

        if (element.type === 'checkbox') {
            return element.checked ? (element.value || '1') : '';
        }

        if (element.tagName === 'SELECT') {
            const option = element.options[element.selectedIndex];
            return option ? option.value : element.value;
        }

        return element.value || element.textContent || '';
    }

    function setFieldValue(element, value) {
        if (!element) {
            return;
        }

        if ('value' in element) {
            element.value = value == null ? '' : String(value);
            element.dispatchEvent(new Event('input', { bubbles: true }));
            element.dispatchEvent(new Event('change', { bubbles: true }));
            return;
        }

        element.textContent = value == null ? '' : String(value);
    }

    function normalizeInteger(value, fallback) {
        const parsed = parseInt(String(value || '').replace(',', '.'), 10);
        return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
    }

    function normalizeSelectValue(paramName, value, productConfig) {
        const raw = String(value || '').trim();
        const codeMap = (productConfig.selectCodeMap || {})[paramName] || {};
        return codeMap[raw] || raw;
    }

    function readParams(productKey, root) {
        const productConfig = getProductConfig(productKey);
        const fields = productConfig.inputSelectors || {};
        const quantityValue = getFieldValue(selectFirst(fields.quantity, root));
        const puzzleValue = getFieldValue(selectFirst(fields.puzzle_id, root));

        return {
            quantity: normalizeInteger(quantityValue, undefined),
            puzzle_id: normalizeSelectValue('puzzle_id', puzzleValue, productConfig),
            mode: 1,
        };
    }

    function applyDefaults(params, productInfo) {
        const defaults = Object.assign({}, productInfo && productInfo.defaults ? productInfo.defaults : {});
        const out = Object.assign({}, defaults, params || {});

        Object.keys(out).forEach((key) => {
            if (out[key] === undefined || out[key] === null || out[key] === '') {
                out[key] = defaults[key];
            }
        });

        if (!out.mode && out.mode !== 0) {
            out.mode = 1;
        }

        return out;
    }

    async function fetchJson(url, options) {
        const response = await fetch(url, Object.assign({ credentials: 'same-origin' }, options || {}));
        let payload = null;

        try {
            payload = await response.json();
        } catch (err) {
            payload = null;
        }

        if (!response.ok) {
            const message = payload && (payload.detail || payload.error || payload.message);
            throw new Error(message || `Ошибка API ${response.status}`);
        }

        return payload;
    }

    async function loadProduct(productKey) {
        const productConfig = getProductConfig(productKey);
        const productSlug = productConfig.productSlug || productKey;

        if (!productCache.has(productSlug)) {
            const promise = fetchJson(joinUrl(config.apiBase, `product/${productSlug}`));
            productCache.set(productSlug, promise);
        }

        return productCache.get(productSlug);
    }

    async function insainCalc(slug, params) {
        const body = Object.assign({}, params || {});
        return fetchJson(joinUrl(config.apiBase, `calc/${slug}`), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });
    }

    async function insainCalcLegacy(productKey, params, options) {
        const productConfig = getProductConfig(productKey);
        const product = await loadProduct(productKey);
        const calcSlug = (options && options.calcSlug) || productConfig.calcSlug || product.base_calc_slug || productKey;
        const requestParams = applyDefaults(params || {}, product);
        const result = await insainCalc(calcSlug, requestParams);
        const legacyResult = adaptLegacyResult(result);

        if (!options || options.updateUrl !== false) {
            updateUrlParams(requestParams);
        }

        return legacyResult;
    }

    function adaptLegacyResult(result) {
        const materialsMap = new Map();
        (result.materials || []).forEach((material) => {
            const code = material.code || material.id || '';
            if (!code) {
                return;
            }
            materialsMap.set(code, [
                material.name || material.title || code,
                material.size_mm || material.size || null,
                material.quantity || material.quantity_approx || 0,
            ]);
        });

        return {
            cost: result.cost || 0,
            price: result.price || 0,
            unit_price: result.unit_price || 0,
            time: result.time_hours || 0,
            timeReady: result.time_ready || 0,
            weight: result.weight_kg || 0,
            material: materialsMap,
            materials: result.materials || [],
            share_url: result.share_url || '',
            raw: result,
        };
    }

    function formatMoney(value) {
        const number = Number(value || 0);
        return Number.isFinite(number) ? Math.ceil(number).toString() : '';
    }

    function formatNumber(value, digits) {
        const number = Number(value || 0);
        return Number.isFinite(number) ? number.toFixed(digits).replace(/\.?0+$/, '') : '';
    }

    function formatResultValue(key, value) {
        if (key === 'cost' || key === 'price' || key === 'unit_price') {
            return formatMoney(value);
        }
        if (key === 'time' || key === 'time_hours' || key === 'timeReady' || key === 'time_ready') {
            return formatNumber(value, 2);
        }
        if (key === 'weight' || key === 'weight_kg') {
            return formatNumber(value, 2);
        }
        return value == null ? '' : value;
    }

    function displayResult(productKey, legacyResult, root) {
        const productConfig = getProductConfig(productKey);
        const resultSelectors = productConfig.resultSelectors || {};
        const values = {
            cost: legacyResult.cost,
            price: legacyResult.price,
            unit_price: legacyResult.unit_price,
            time: legacyResult.time,
            time_hours: legacyResult.time,
            timeReady: legacyResult.timeReady,
            time_ready: legacyResult.timeReady,
            weight: legacyResult.weight,
            weight_kg: legacyResult.weight,
            share_url: legacyResult.share_url,
        };

        Object.keys(resultSelectors).forEach((key) => {
            const element = selectFirst(resultSelectors[key], root);
            if (element) {
                setFieldValue(element, formatResultValue(key, values[key]));
            }
        });

        document.dispatchEvent(new CustomEvent('insaincalc:result', {
            detail: {
                product: productKey,
                result: legacyResult,
            },
        }));
    }

    function displayError(productKey, error) {
        console.error('InsainCalcBridge:', error);
        document.dispatchEvent(new CustomEvent('insaincalc:error', {
            detail: {
                product: productKey,
                error,
            },
        }));
    }

    function updateUrlParams(params) {
        if (!window.history || !window.URLSearchParams) {
            return;
        }

        const url = new URL(window.location.href);
        Object.keys(params || {}).forEach((key) => {
            const value = params[key];
            if (value === undefined || value === null || value === '') {
                url.searchParams.delete(key);
            } else {
                url.searchParams.set(key, value);
            }
        });
        window.history.replaceState({}, '', url.toString());
    }

    function readUrlParams() {
        const params = {};
        const search = new URLSearchParams(window.location.search);
        search.forEach((value, key) => {
            params[key] = value;
        });
        return params;
    }

    function prefillForm(productKey, root) {
        const productConfig = getProductConfig(productKey);
        const fields = productConfig.inputSelectors || {};
        const params = readUrlParams();

        if (params.quantity) {
            setFieldValue(selectFirst(fields.quantity, root), params.quantity);
        }

        if (params.puzzle_id) {
            const puzzleField = selectFirst(fields.puzzle_id, root);
            const reverseMap = reverseCodeMap((productConfig.selectCodeMap || {}).puzzle_id || {});
            setFieldValue(puzzleField, reverseMap[params.puzzle_id] || params.puzzle_id);
        }
    }

    function reverseCodeMap(map) {
        return Object.keys(map || {}).reduce((acc, key) => {
            acc[map[key]] = key;
            return acc;
        }, {});
    }

    async function recalculate(productKey, explicitParams, root) {
        const productConfig = getProductConfig(productKey);
        const product = await loadProduct(productKey);
        const calcSlug = productConfig.calcSlug || product.base_calc_slug || productKey;
        const formParams = explicitParams || readParams(productKey, root);
        const params = applyDefaults(formParams, product);

        const requestId = Date.now();
        lastRequestByProduct.set(productKey, requestId);

        const result = await insainCalc(calcSlug, params);
        if (lastRequestByProduct.get(productKey) !== requestId) {
            return null;
        }

        const legacyResult = adaptLegacyResult(result);
        displayResult(productKey, legacyResult, root);
        updateUrlParams({
            quantity: params.quantity,
            puzzle_id: params.puzzle_id,
            mode: params.mode,
        });
        return legacyResult;
    }

    function bindProduct(productKey, root) {
        const productConfig = getProductConfig(productKey);
        const fields = productConfig.inputSelectors || {};
        const inputs = [
            selectFirst(fields.quantity, root),
            selectFirst(fields.puzzle_id, root),
        ].filter(Boolean);

        if (!inputs.length) {
            return false;
        }

        const debounced = debounce(() => {
            recalculate(productKey, undefined, root).catch((error) => displayError(productKey, error));
        }, Number(config.debounceMs || 350));

        inputs.forEach((input) => {
            input.addEventListener('input', debounced);
            input.addEventListener('change', debounced);
        });

        prefillForm(productKey, root);
        debounced();
        return true;
    }

    function debounce(fn, wait) {
        let timeoutId = null;
        return function debounced() {
            window.clearTimeout(timeoutId);
            timeoutId = window.setTimeout(fn, wait);
        };
    }

    function getProductConfig(productKey) {
        return (config.products || {})[productKey] || {};
    }

    function shouldAutoBind(productKey) {
        const productConfig = getProductConfig(productKey);
        if (!productConfig.pagePathIncludes) {
            return true;
        }
        return window.location.pathname.indexOf(productConfig.pagePathIncludes) !== -1;
    }

    function init(root) {
        Object.keys(config.products || {}).forEach((productKey) => {
            if (shouldAutoBind(productKey)) {
                bindProduct(productKey, root || document);
            }
        });
    }

    window.insainCalc = insainCalc;
    window.insainCalcLegacy = insainCalcLegacy;
    window.InsainCalcBridge = {
        init,
        bindProduct,
        recalculate,
        calcLegacy: insainCalcLegacy,
        readParams,
        adaptLegacyResult,
        updateUrlParams,
        readUrlParams,
    };

    window.insaincalc = window.insaincalc || {};
    window.insaincalc.calcPuzzleAsync = function calcPuzzleAsync(n, puzzleID, options, modeProduction) {
        return insainCalcLegacy('puzzle', {
            quantity: normalizeInteger(n, 1),
            puzzle_id: puzzleID,
            mode: modeProduction == null ? 1 : Number(modeProduction),
        }).then((result) => result || adaptLegacyResult({}));
    };

    if (config.autoInit !== false) {
        document.addEventListener('DOMContentLoaded', () => init(document));
    }
}());
