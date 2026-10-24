<?php
/**
 * Plugin Name: Insain Calc Bridge
 * Description: Мост ez Form Calculator и Python calc_service. Методы insaincalc.calcApi, showResult, showError, syncUrl.
 * Version: 0.2.3
 * Author: Insain
 */

if (!defined('ABSPATH')) {
    exit;
}

function insain_calc_bridge_enqueue_scripts(): void
{
    // В шапке: custom JS ez Form Calculator может вызваться раньше footer-скриптов.
    wp_enqueue_script(
        'insain-calc-bridge',
        plugin_dir_url(__FILE__) . 'js/insain-calc-bridge.js',
        array(),
        '0.2.3',
        false
    );

    wp_localize_script(
        'insain-calc-bridge',
        'InsainCalcBridgeConfig',
        array(
            // На insain.ru API проксируется на том же домене (nginx location /api/).
            'apiBase' => '/api/v1',
        )
    );
}

add_action('wp_enqueue_scripts', 'insain_calc_bridge_enqueue_scripts');
