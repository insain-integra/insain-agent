<?php
/**
 * Plugin Name: Insain Calc Bridge
 * Description: Подключает JS-мост между ez Form Calculator и Python calc_service.
 * Version: 0.1.0
 * Author: Insain
 */

if (!defined('ABSPATH')) {
    exit;
}

function insain_calc_bridge_enqueue_scripts(): void
{
    $plugin_url = plugin_dir_url(__FILE__);

    wp_enqueue_script(
        'insain-calc-bridge',
        $plugin_url . 'js/insain-calc-bridge.js',
        array(),
        '0.1.0',
        true
    );

    wp_localize_script(
        'insain-calc-bridge',
        'InsainCalcBridgeConfig',
        array(
            // На insain.ru API проксируется на том же домене (nginx location /api/).
            'apiBase' => '/api/v1',
            'autoInit' => true,
            'products' => array(
                'puzzle' => array(
                    'productSlug' => 'puzzle',
                    'calcSlug' => 'puzzle',
                    'pagePathIncludes' => 'kalkulyator-pazlov',
                    'inputSelectors' => array(
                        'quantity' => array(
                            '#ezfc_element-3103',
                            '#ezfc_element_3103',
                            '[name="numn"]',
                            '[name$="[numn]"]',
                            '[data-element-name="numn"]',
                            '[data-ezfc-id="3103"]',
                        ),
                        'puzzle_id' => array(
                            '#ezfc_element-3104',
                            '#ezfc_element_3104',
                            '[name="dpdformat"]',
                            '[name$="[dpdformat]"]',
                            '[data-element-name="dpdformat"]',
                            '[data-ezfc-id="3104"]',
                        ),
                    ),
                    'selectCodeMap' => array(
                        'puzzle_id' => array(
                            '0' => 'Puzzle300420',
                            '1' => 'Puzzle208298',
                            '2' => 'Puzzle159215',
                        ),
                    ),
                    // Заполнить в WordPress после проверки DOM output-полей формы.
                    'resultSelectors' => array(),
                ),
            ),
        )
    );
}

add_action('wp_enqueue_scripts', 'insain_calc_bridge_enqueue_scripts');
