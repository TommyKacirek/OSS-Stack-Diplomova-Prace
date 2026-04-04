<?php
require __DIR__ . '/vendor/autoload.php';
$app = require_once __DIR__ . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

use App\Models\Setting;

echo "--- START DEBUG LOG ---\n";
echo "Timestamp: " . date('Y-m-d H:i:s') . "\n";

try {
    $s = Setting::first();
    if (!$s) {
        echo "CRITICAL: No settings record found!\n";
        exit(1);
    }

    echo "SAML Enabled: " . ($s->saml_enabled ? 'YES' : 'NO') . "\n";
    echo "SAML Metadata URL (saml_idp_metadata): " . ($s->saml_idp_metadata ?: '(null)') . "\n";

    $rawJson = $s->saml_custom_settings;
    echo "Raw saml_custom_settings:\n";
    echo $rawJson . "\n";
    echo "--------------------------\n";

    if (empty($rawJson)) {
        echo "ERROR: saml_custom_settings is EMPTY.\n";
    } else {
        $data = json_decode($rawJson, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            echo "ERROR: JSON Decode Failed: " . json_last_error_msg() . "\n";
        } else {
            echo "JSON Decode Success. Structure Analysis:\n";
            if (isset($data['idp'])) {
                echo "OK: 'idp' key found.\n";
                if (isset($data['idp']['entityId'])) {
                    echo "OK: 'idp.entityId' found: " . $data['idp']['entityId'] . "\n";
                } else {
                    echo "FAIL: 'idp.entityId' MISSING.\n";
                }
                if (isset($data['idp']['x509cert'])) {
                     echo "OK: 'idp.x509cert' found (length: " . strlen($data['idp']['x509cert']) . ")\n";
                } else {
                     echo "FAIL: 'idp.x509cert' MISSING.\n";
                }
            } else {
                echo "FAIL: 'idp' key MISSING in root of JSON.\n";
            }
            
            if (isset($data['sp'])) {
                echo "OK: 'sp' key found.\n";
            } else {
                 echo "FAIL: 'sp' key MISSING.\n";
            }
        }
    }

} catch (Exception $e) {
    echo "EXCEPTION: " . $e->getMessage() . "\n";
}
echo "--- END DEBUG LOG ---\n";
