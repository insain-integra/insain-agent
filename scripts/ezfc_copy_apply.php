<?php
/**
 * Запись пакета scripts/ezfc_copy.py в копию формы ezFC (skill ezfc-form-to-api, шаги 10 и 15).
 *
 *   sudo -u www-data wp eval-file /tmp/ezfc_copy_apply.php /tmp/ezfc-copy.json [apply] --path=/var/www/insain.ru
 *
 * Без `apply` — только показ изменений. Отказ, если форма-цель — боевая: стоит на опубликованном
 * товаре, в шорткоде опубликованной записи или совпадает с `live`. Пишутся только ключи из $allowed
 * в поле data существующих элементов копии; структура формы (элементы, id, порядок) не меняется.
 * Перед записью строки сохраняются в /tmp/ezfc-copy-<copy>-<время>.json.
 */
if (!defined('ABSPATH')) {
    exit(1);
}

$allowed = array('custom_calculation', 'custom_calculation_function_read_file', 'GET', 'GET_check_option_value');

function ezfc_copy_stop($msg) {
    fwrite(STDERR, "стоп: {$msg}\n");
    exit(1);
}

global $wpdb;
$elements_table = $wpdb->prefix . 'ezfc_forms_elements';
$forms_table = $wpdb->prefix . 'ezfc_forms';

$file = isset($args[0]) ? $args[0] : '';
$apply = isset($args[1]) && $args[1] === 'apply';
if ($file === '' || !is_readable($file)) {
    ezfc_copy_stop('нет файла пакета');
}
$package = json_decode(file_get_contents($file), true);
if (!is_array($package) || empty($package['elements']) || !is_array($package['elements'])) {
    ezfc_copy_stop('пакет не JSON или без elements');
}
$live = (int) $package['live'];
$copy = (int) $package['copy'];
if ($live <= 0 || $copy <= 0 || $live === $copy) {
    ezfc_copy_stop("live={$live} copy={$copy}: копия должна отличаться от боевой формы");
}

$name = $wpdb->get_var($wpdb->prepare("SELECT name FROM {$forms_table} WHERE id = %d", $copy));
if ($name === null) {
    ezfc_copy_stop("формы {$copy} нет");
}

$published = $wpdb->get_col($wpdb->prepare(
    "SELECT p.ID FROM {$wpdb->postmeta} m JOIN {$wpdb->posts} p ON p.ID = m.post_id
     WHERE m.meta_key = 'ezfc_form_id' AND m.meta_value = %s AND p.post_status = 'publish'",
    (string) $copy
));
if ($published) {
    ezfc_copy_stop("форма {$copy} на опубликованных товарах " . implode(',', $published) . ' — это боевая форма');
}
$shortcode = $wpdb->get_col($wpdb->prepare(
    "SELECT ID FROM {$wpdb->posts} WHERE post_status = 'publish' AND post_content REGEXP %s",
    '\\[ezfc[^]]*id=["\']?' . $copy . '([^0-9]|$)'
));
if ($shortcode) {
    ezfc_copy_stop("форма {$copy} в шорткоде опубликованных записей " . implode(',', $shortcode));
}

$rows = array();
foreach ($package['elements'] as $el_id => $fields) {
    $el_id = (int) $el_id;
    if (!is_array($fields) || !$fields) {
        ezfc_copy_stop("элемент {$el_id}: пустой набор полей");
    }
    $extra = array_diff(array_keys($fields), $allowed);
    if ($extra) {
        ezfc_copy_stop("элемент {$el_id}: ключи вне белого списка: " . implode(',', $extra));
    }
    $row = $wpdb->get_row($wpdb->prepare(
        "SELECT id, f_id, data FROM {$elements_table} WHERE id = %d", $el_id
    ), ARRAY_A);
    if (!$row || (int) $row['f_id'] !== $copy) {
        ezfc_copy_stop("элемент {$el_id} не из формы {$copy}");
    }
    $data = json_decode($row['data'], true);
    if (!is_array($data)) {
        ezfc_copy_stop("элемент {$el_id}: data не JSON");
    }
    $rows[$el_id] = array('row' => $row, 'data' => $data, 'fields' => $fields);
}

echo "форма {$copy} «{$name}», боевая {$live}, " . ($apply ? 'запись' : 'показ, без записи') . "\n";
foreach ($rows as $el_id => $item) {
    $label = isset($item['data']['name']) ? $item['data']['name'] : '?';
    foreach ($item['fields'] as $key => $value) {
        $old = isset($item['data'][$key]) ? (string) $item['data'][$key] : '';
        $show = function ($v) use ($key) {
            return $key === 'custom_calculation' ? 'JS ' . strlen($v) . ' байт, calcApi=' . (strpos($v, 'insaincalc.calcApi(') !== false ? 1 : 0) : "'{$v}'";
        };
        $mark = $old === (string) $value ? '=' : '→';
        echo "{$el_id} {$label} {$key}: " . $show($old) . " {$mark} " . $show((string) $value) . "\n";
    }
}
if (!$apply) {
    exit(0);
}

$backup = '/tmp/ezfc-copy-' . $copy . '-' . gmdate('Ymd-His') . '.json';
$saved = array();
foreach ($rows as $item) {
    $saved[] = $item['row'];
}
if (file_put_contents($backup, wp_json_encode($saved, JSON_UNESCAPED_UNICODE)) === false) {
    ezfc_copy_stop("не записан бэкап {$backup}");
}
echo "бэкап: {$backup}\n";

foreach ($rows as $el_id => $item) {
    $data = array_merge($item['data'], $item['fields']);
    $ok = $wpdb->update(
        $elements_table,
        array('data' => wp_json_encode($data, JSON_UNESCAPED_UNICODE)),
        array('id' => $el_id, 'f_id' => $copy)
    );
    if ($ok === false) {
        ezfc_copy_stop("элемент {$el_id}: ошибка записи, откат — строки из {$backup}");
    }
    echo "{$el_id}: записано\n";
}
wp_cache_flush();
echo "готово; сбросить LiteSpeed: wp litespeed-purge all\n";
