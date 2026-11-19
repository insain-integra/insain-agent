<?php
/**
 * Применение пакета scripts/ezfc_build_form.py к таблицам ezFC на сайте.
 *
 *   sudo -u www-data wp eval-file /tmp/ezfc_build_apply.php /tmp/ezfc-build-pkg.json [apply|update-options|allow-published] --path=/var/www/insain.ru
 *   sudo -u www-data wp eval-file /tmp/ezfc_build_apply.php restore /tmp/ezfc-build-99-....json [dry-run|allow-published] --path=/var/www/insain.ru
 *
 * Режимы:
 *   - без флага `apply` (или `dry-run`) — только показ создаваемой формы/элементов или diff опций, ничего не пишет;
 *   - `apply` — создаёт новую форму (action=build) или обновляет options элементов (action=update-options),
 *     сохраняя манифест/бэкап в /tmp/ezfc-build-*.json;
 *   - `update-options` — без `apply` показывает diff опций, с `apply` обновляет только массив `options`;
 *   - `restore <файл>` — удаляет созданную форму из манифеста build или возвращает `data` элементов из бэкапа.
 */
if (!defined('ABSPATH')) {
    exit(1);
}

function ezfc_build_stop($msg) {
    fwrite(STDERR, "стоп: {$msg}\n");
    exit(1);
}

function ezfc_build_encode_json($value) {
    $json = wp_json_encode($value, JSON_UNESCAPED_UNICODE);
    if ($json === false) {
        ezfc_build_stop('ошибка wp_json_encode');
    }
    return $json;
}

function ezfc_build_published_refs($wpdb, $form_id) {
    $published = $wpdb->get_col($wpdb->prepare(
        "SELECT p.ID FROM {$wpdb->postmeta} m JOIN {$wpdb->posts} p ON p.ID = m.post_id
         WHERE m.meta_key = 'ezfc_form_id' AND m.meta_value = %s AND p.post_status = 'publish'",
        (string) $form_id
    ));
    $shortcode = $wpdb->get_col($wpdb->prepare(
        "SELECT ID FROM {$wpdb->posts} WHERE post_status = 'publish' AND post_content REGEXP %s",
        '\\[ezfc[^]]*id=["\']?' . (int) $form_id . '([^0-9]|$)'
    ));
    return array_values(array_unique(array_merge($published ?: array(), $shortcode ?: array())));
}

function ezfc_build_assert_safe_form($wpdb, $form_id, $allow_published) {
    if ($allow_published) {
        return;
    }
    $refs = ezfc_build_published_refs($wpdb, $form_id);
    if ($refs) {
        ezfc_build_stop(
            "форма {$form_id} используется на опубликованных записях " . implode(',', $refs) .
            ' — для записи нужен явный флаг allow-published'
        );
    }
}

function ezfc_build_set_nested(&$target, $path, $value) {
    $ref = &$target;
    foreach ($path as $segment) {
        if (!is_array($ref) || !array_key_exists($segment, $ref)) {
            ezfc_build_stop('некорректный path ссылки: ' . implode('.', $path));
        }
        $ref = &$ref[$segment];
    }
    $ref = $value;
}

function ezfc_build_merge_options($old_options, $new_options) {
    $old_by_value = array();
    $max_id = 0;
    $has_old = is_array($old_options) && count($old_options) > 0;
    if ($has_old) {
        foreach ($old_options as $opt) {
            if (!is_array($opt)) {
                continue;
            }
            $val = isset($opt['value']) ? (string) $opt['value'] : '';
            $oid = isset($opt['id']) ? (string) $opt['id'] : '';
            if ($val !== '' && !isset($old_by_value[$val]) && $oid !== '') {
                $old_by_value[$val] = $oid;
            }
            if (ctype_digit($oid) && (int) $oid > $max_id) {
                $max_id = (int) $oid;
            }
        }
    }

    $used_ids = array();
    $merged = array();
    foreach ($new_options as $opt) {
        $val = isset($opt['value']) ? (string) $opt['value'] : '';
        $candidate_id = isset($old_by_value[$val]) ? $old_by_value[$val] : '';
        if ($candidate_id !== '' && !isset($used_ids[$candidate_id])) {
            $opt['id'] = $candidate_id;
        } elseif (!$has_old) {
            $fallback = isset($opt['id']) ? (string) $opt['id'] : '';
            if ($fallback !== '' && !isset($used_ids[$fallback])) {
                $opt['id'] = $fallback;
            } else {
                $max_id += 1;
                $opt['id'] = (string) $max_id;
            }
        } else {
            $max_id += 1;
            $opt['id'] = (string) $max_id;
        }
        $used_ids[$opt['id']] = true;
        $merged[] = $opt;
    }
    return $merged;
}

function ezfc_build_diff_options($old_options, $new_options) {
    $old_map = array();
    if (is_array($old_options)) {
        foreach ($old_options as $o) {
            if (is_array($o) && isset($o['value'])) {
                $old_map[(string) $o['value']] = isset($o['text']) ? (string) $o['text'] : '';
            }
        }
    }
    $new_map = array();
    foreach ($new_options as $o) {
        $new_map[(string) $o['value']] = isset($o['text']) ? (string) $o['text'] : '';
    }
    $added = array();
    $removed = array();
    $changed = array();
    $same = 0;
    foreach ($new_map as $v => $t) {
        if (!array_key_exists($v, $old_map)) {
            $added[] = "+ {$v}: {$t}";
        } elseif ($old_map[$v] !== $t) {
            $changed[] = "~ {$v}: '{$old_map[$v]}' → '{$t}'";
        } else {
            $same += 1;
        }
    }
    foreach ($old_map as $v => $t) {
        if (!array_key_exists($v, $new_map)) {
            $removed[] = "- {$v}: {$t}";
        }
    }
    return array('added' => $added, 'removed' => $removed, 'changed' => $changed, 'same' => $same);
}

function ezfc_build_cleanup_partial($wpdb, $form_id) {
    $wpdb->delete($wpdb->prefix . 'ezfc_forms_elements', array('f_id' => $form_id), array('%d'));
    $wpdb->delete($wpdb->prefix . 'ezfc_forms_options', array('f_id' => $form_id), array('%d'));
    $wpdb->delete($wpdb->prefix . 'ezfc_forms', array('id' => $form_id), array('%d'));
}

function ezfc_build_run_restore($wpdb, $file, $dry_run, $allow_published) {
    if ($file === '' || !is_readable($file)) {
        ezfc_build_stop("нечитаемый файл отката: {$file}");
    }
    $manifest = json_decode(file_get_contents($file), true);
    if (!is_array($manifest) || empty($manifest['action']) || empty($manifest['form_id'])) {
        ezfc_build_stop('файл отката не содержит action и form_id');
    }
    $form_id = (int) $manifest['form_id'];
    $forms_table = $wpdb->prefix . 'ezfc_forms';
    $elements_table = $wpdb->prefix . 'ezfc_forms_elements';
    $options_table = $wpdb->prefix . 'ezfc_forms_options';

    ezfc_build_assert_safe_form($wpdb, $form_id, $allow_published);

    if ($manifest['action'] === 'build') {
        $el_cnt = (int) $wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM {$elements_table} WHERE f_id = %d", $form_id));
        $opt_cnt = (int) $wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM {$options_table} WHERE f_id = %d", $form_id));
        $frm_cnt = (int) $wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM {$forms_table} WHERE id = %d", $form_id));
        echo "restore build форма {$form_id}: forms={$frm_cnt}, options={$opt_cnt}, elements={$el_cnt}" . ($dry_run ? " (dry-run)\n" : "\n");
        if ($dry_run) {
            return;
        }
        $wpdb->delete($elements_table, array('f_id' => $form_id), array('%d'));
        $wpdb->delete($options_table, array('f_id' => $form_id), array('%d'));
        $wpdb->delete($forms_table, array('id' => $form_id), array('%d'));
        wp_cache_flush();
        echo "удалена форма {$form_id} (elements={$el_cnt}, options={$opt_cnt}, forms={$frm_cnt}); сбросить LiteSpeed: wp litespeed-purge all\n";
        return;
    }

    if ($manifest['action'] === 'update-options') {
        if (empty($manifest['elements']) || !is_array($manifest['elements'])) {
            ezfc_build_stop('в бэкапе update-options нет elements');
        }
        echo "restore update-options форма {$form_id}: элементов " . count($manifest['elements']) . ($dry_run ? " (dry-run)\n" : "\n");
        if ($dry_run) {
            return;
        }
        foreach ($manifest['elements'] as $row) {
            $ok = $wpdb->update(
                $elements_table,
                array('data' => $row['data']),
                array('id' => (int) $row['id'], 'f_id' => $form_id)
            );
            if ($ok === false) {
                ezfc_build_stop("ошибка восстановления элемента {$row['id']}");
            }
            echo "{$row['id']}: восстановлено\n";
        }
        wp_cache_flush();
        echo "готово; сбросить LiteSpeed: wp litespeed-purge all\n";
        return;
    }

    ezfc_build_stop("неизвестный action в файле отката: {$manifest['action']}");
}

global $wpdb;
$forms_table = $wpdb->prefix . 'ezfc_forms';
$elements_table = $wpdb->prefix . 'ezfc_forms_elements';
$options_table = $wpdb->prefix . 'ezfc_forms_options';

$first = isset($args[0]) ? $args[0] : '';
if ($first === '') {
    ezfc_build_stop('нужен путь к пакету JSON или команда restore <файл>');
}

if ($first === 'restore') {
    $restore_file = isset($args[1]) ? $args[1] : '';
    $rest_flags = array_slice($args, 2);
    $dry_run = in_array('dry-run', $rest_flags, true);
    $allow_published = in_array('allow-published', $rest_flags, true);
    ezfc_build_run_restore($wpdb, $restore_file, $dry_run, $allow_published);
    exit(0);
}

$file = $first;
if (!is_readable($file)) {
    ezfc_build_stop("нет файла пакета: {$file}");
}
$package = json_decode(file_get_contents($file), true);
if (!is_array($package) || empty($package['action'])) {
    ezfc_build_stop('пакет не JSON или без action');
}

$flags = array_slice($args, 1);
$apply = in_array('apply', $flags, true);
$allow_published = in_array('allow-published', $flags, true);
if (in_array('update-options', $flags, true) && $package['action'] !== 'update-options') {
    ezfc_build_stop("режим update-options требует пакет с action=update-options (получено {$package['action']})");
}

if ($package['action'] === 'build') {
    if (empty($package['form']['name']) || empty($package['elements']) || !is_array($package['elements'])) {
        ezfc_build_stop('неполный пакет build');
    }
    $form_name = (string) $package['form']['name'];
    $form_options = isset($package['form_options']) && is_array($package['form_options']) ? $package['form_options'] : array();
    $elements = $package['elements'];

    echo "build «{$form_name}» (" . (isset($package['slug']) ? $package['slug'] : '?') . "), "
        . ($apply ? 'запись в БД' : 'dry-run, без записи') . "\n";
    echo "опций формы: " . count($form_options) . ", элементов: " . count($elements) . "\n";

    if (!$apply) {
        foreach ($elements as $el) {
            $opts_cnt = isset($el['data']['options']) && is_array($el['data']['options']) ? count($el['data']['options']) : 0;
            $hid = isset($el['data']['hidden']) ? $el['data']['hidden'] : '0';
            echo sprintf(
                "  pos=%2d e_id=%2d %-24s group=%-16s hidden=%s%s\n",
                (int) $el['position'],
                (int) $el['e_id'],
                $el['name'],
                $el['group_name'],
                $hid,
                $opts_cnt ? " options={$opts_cnt}" : ''
            );
        }
        exit(0);
    }

    $ok_form = $wpdb->insert(
        $forms_table,
        array(
            'name' => $form_name,
            'data' => ezfc_build_encode_json($package['form']['data']),
        ),
        array('%s', '%s')
    );
    if ($ok_form === false) {
        ezfc_build_stop('ошибка вставки в ezfc_forms: ' . $wpdb->last_error);
    }
    $form_id = (int) $wpdb->insert_id;

    foreach ($form_options as $opt) {
        $ok_opt = $wpdb->insert(
            $options_table,
            array(
                'f_id' => $form_id,
                'o_id' => (int) $opt['o_id'],
                'value' => (string) $opt['value'],
            ),
            array('%d', '%d', '%s')
        );
        if ($ok_opt === false) {
            ezfc_build_cleanup_partial($wpdb, $form_id);
            ezfc_build_stop("ошибка вставки опции o_id={$opt['o_id']}: " . $wpdb->last_error);
        }
    }

    $name_to_id = array();
    $inserted_with_refs = array();
    foreach ($elements as $el) {
        $data = $el['data'];
        $gname = isset($el['group_name']) ? (string) $el['group_name'] : '0';
        if ($gname === '0') {
            $data['group_id'] = '0';
        } else {
            if (!isset($name_to_id[$gname])) {
                ezfc_build_cleanup_partial($wpdb, $form_id);
                ezfc_build_stop("родительская группа '{$gname}' не вставлена до '{$el['name']}'");
            }
            $data['group_id'] = (string) $name_to_id[$gname];
        }

        $ok_el = $wpdb->insert(
            $elements_table,
            array(
                'f_id' => $form_id,
                'e_id' => (int) $el['e_id'],
                'data' => ezfc_build_encode_json($data),
                'position' => (int) $el['position'],
            ),
            array('%d', '%d', '%s', '%d')
        );
        if ($ok_el === false) {
            ezfc_build_cleanup_partial($wpdb, $form_id);
            ezfc_build_stop("ошибка вставки элемента {$el['name']}: " . $wpdb->last_error);
        }
        $new_id = (int) $wpdb->insert_id;
        $name_to_id[$el['name']] = $new_id;
        if (!empty($el['refs']) && is_array($el['refs'])) {
            $inserted_with_refs[] = array('id' => $new_id, 'name' => $el['name'], 'data' => $data, 'refs' => $el['refs']);
        }
    }

    foreach ($inserted_with_refs as $item) {
        $data = $item['data'];
        foreach ($item['refs'] as $ref) {
            $tname = (string) $ref['target_name'];
            if (!isset($name_to_id[$tname])) {
                ezfc_build_cleanup_partial($wpdb, $form_id);
                ezfc_build_stop("не найден целевой элемент '{$tname}' для ссылки из '{$item['name']}'");
            }
            ezfc_build_set_nested($data, $ref['path'], (string) $name_to_id[$tname]);
        }
        $ok_upd = $wpdb->update(
            $elements_table,
            array('data' => ezfc_build_encode_json($data)),
            array('id' => $item['id'], 'f_id' => $form_id)
        );
        if ($ok_upd === false) {
            ezfc_build_cleanup_partial($wpdb, $form_id);
            ezfc_build_stop("ошибка обновления ссылок элемента {$item['name']}: " . $wpdb->last_error);
        }
    }

    $manifest_path = '/tmp/ezfc-build-' . $form_id . '-' . gmdate('Ymd-His') . '.json';
    $manifest = array(
        'action' => 'build',
        'form_id' => $form_id,
        'form_name' => $form_name,
        'slug' => isset($package['slug']) ? $package['slug'] : '',
        'created_at' => gmdate('c'),
        'name_to_id' => $name_to_id,
    );
    if (file_put_contents($manifest_path, ezfc_build_encode_json($manifest)) === false) {
        ezfc_build_stop("форма {$form_id} создана, но не записан манифест отката {$manifest_path}");
    }

    wp_cache_flush();
    echo "создана форма id={$form_id} «{$form_name}»\n";
    echo "манифест отката: {$manifest_path}\n";
    echo "name -> id:\n";
    foreach ($name_to_id as $el_name => $el_id) {
        echo "  {$el_name}\t{$el_id}\n";
    }
    echo "готово; сбросить LiteSpeed: wp litespeed-purge all\n";
    exit(0);
}

if ($package['action'] === 'update-options') {
    $form_id = isset($package['form_id']) ? (int) $package['form_id'] : 0;
    if ($form_id <= 0 || empty($package['elements']) || !is_array($package['elements'])) {
        ezfc_build_stop('неполный пакет update-options');
    }
    $form_name = $wpdb->get_var($wpdb->prepare("SELECT name FROM {$forms_table} WHERE id = %d", $form_id));
    if ($form_name === null) {
        ezfc_build_stop("формы {$form_id} нет");
    }
    ezfc_build_assert_safe_form($wpdb, $form_id, $allow_published);

    $db_rows = $wpdb->get_results($wpdb->prepare(
        "SELECT id, f_id, e_id, data, position FROM {$elements_table} WHERE f_id = %d",
        $form_id
    ), ARRAY_A);
    $by_name = array();
    foreach ($db_rows as $row) {
        $decoded = json_decode($row['data'], true);
        if (is_array($decoded) && !empty($decoded['name'])) {
            $by_name[(string) $decoded['name']] = array('row' => $row, 'data' => $decoded);
        }
    }

    $allowed_types = array(4, 5, 6);
    $plan = array();
    foreach ($package['elements'] as $el_name => $spec_el) {
        if (!isset($by_name[$el_name])) {
            ezfc_build_stop("элемент '{$el_name}' не найден в форме {$form_id}");
        }
        $item = $by_name[$el_name];
        $e_id = (int) $item['row']['e_id'];
        if (!in_array($e_id, $allowed_types, true)) {
            ezfc_build_stop("элемент '{$el_name}' (e_id={$e_id}) не является dropdown/radio/checkbox");
        }
        $old_opts = isset($item['data']['options']) && is_array($item['data']['options']) ? $item['data']['options'] : array();
        $merged_opts = ezfc_build_merge_options($old_opts, $spec_el['options']);
        $diff = ezfc_build_diff_options($old_opts, $merged_opts);
        $plan[$el_name] = array(
            'row' => $item['row'],
            'data' => $item['data'],
            'options' => $merged_opts,
            'diff' => $diff,
        );
    }

    echo "update-options форма {$form_id} «{$form_name}», " . ($apply ? 'запись в БД' : 'dry-run, без записи') . "\n";
    foreach ($plan as $el_name => $p) {
        $d = $p['diff'];
        echo "  {$el_name} (id={$p['row']['id']}): same={$d['same']} +" . count($d['added']) . " -" . count($d['removed']) . " ~" . count($d['changed']) . "\n";
        foreach (array_merge($d['added'], $d['removed'], $d['changed']) as $line) {
            echo "    {$line}\n";
        }
    }

    if (!$apply) {
        exit(0);
    }

    $backup_path = '/tmp/ezfc-build-options-' . $form_id . '-' . gmdate('Ymd-His') . '.json';
    $saved_rows = array();
    foreach ($plan as $p) {
        $saved_rows[] = $p['row'];
    }
    $backup_payload = array(
        'action' => 'update-options',
        'form_id' => $form_id,
        'created_at' => gmdate('c'),
        'elements' => $saved_rows,
    );
    if (file_put_contents($backup_path, ezfc_build_encode_json($backup_payload)) === false) {
        ezfc_build_stop("не записан бэкап {$backup_path}");
    }
    echo "бэкап: {$backup_path}\n";

    foreach ($plan as $el_name => $p) {
        $data = $p['data'];
        $data['options'] = $p['options'];
        $ok = $wpdb->update(
            $elements_table,
            array('data' => ezfc_build_encode_json($data)),
            array('id' => (int) $p['row']['id'], 'f_id' => $form_id)
        );
        if ($ok === false) {
            ezfc_build_stop("ошибка обновления '{$el_name}': откат — restore {$backup_path}");
        }
        echo "{$el_name} ({$p['row']['id']}): обновлено " . count($p['options']) . " опций\n";
    }

    wp_cache_flush();
    echo "готово; сбросить LiteSpeed: wp litespeed-purge all\n";
    exit(0);
}

ezfc_build_stop("неизвестный action: {$package['action']}");
