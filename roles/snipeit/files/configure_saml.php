<?php
// Ensure we are in the right directory
chdir('/var/www/html');

require __DIR__ . '/vendor/autoload.php';
$app = require_once __DIR__ . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

use App\Models\Setting;
use Illuminate\Support\Facades\Schema;

echo "--- START SAML CONFIG ---\n";
try {
    // 1. Fetch Metadata
    $metadataUrl = 'https://auth.oss.local/realms/Lab/protocol/saml/descriptor';
    echo "Fetching metadata from: $metadataUrl\n";
    
    $arrContextOptions=array(
        "ssl"=>array(
            "verify_peer"=>false,
            "verify_peer_name"=>false,
        ),
    );  
    $xmlContent = @file_get_contents($metadataUrl, false, stream_context_create($arrContextOptions));

    if (!$xmlContent) {
        throw new Exception("Failed to fetch metadata from Keycloak. Check network/DNS.");
    }
    echo "Metadata fetched successfully (" . strlen($xmlContent) . " bytes).\n";

    // 2. Extract Certificate
    $cert = '';
    if (preg_match('/<ds:X509Certificate>(.*?)<\/ds:X509Certificate>/s', $xmlContent, $matches)) {
        $cert = trim(str_replace(["\r", "\n", " "], '', $matches[1]));
        echo "Certificate extracted.\n";
    } else {
        throw new Exception("Could not find X509Certificate in metadata.");
    }

    // 3. Construct Nested JSON
    $samlSettings = [
        'strict' => false,
        'debug' => true,
        'sp' => [
            'entityId' => 'https://assets.oss.local',
            'assertionConsumerService' => [
                'url' => 'https://assets.oss.local/saml/acs',
                'binding' => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'
            ],
            'NameIDFormat' => 'urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified'
        ],
        'idp' => [
            'entityId' => 'https://auth.oss.local/realms/Lab',
            'singleSignOnService' => [
                'url' => 'https://auth.oss.local/realms/Lab/protocol/saml',
                'binding' => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
            ],
            'singleLogoutService' => [
                'url' => 'https://auth.oss.local/realms/Lab/protocol/saml',
                'binding' => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
            ],
            'x509cert' => $cert
        ]
    ];

    // 4. Update Database
    $s = Setting::first();
    if (!$s) {
        echo "Creating new settings record...\n";
        $s = new Setting();
        $s->site_name = 'OSS Lab';
        $s->locale = 'en-US';
        $s->auto_increment_assets = 1;
        $s->alert_email = 'admin@oss.local';
        $s->brand = 1;
    }

    $s->saml_enabled = 1;
    $s->saml_idp_metadata = null; // FORCE CLEAR
    $s->saml_custom_settings = json_encode($samlSettings);
    $s->saml_attr_mapping_username = 'username';
    $s->saml_forcelogin = 0;

    // Check optional JIT
    if (Schema::hasColumn('settings', 'saml_jit')) {
        $s->saml_jit = 1;
        echo "JIT Enabled.\n";
    }

    $s->save();
    echo "SUCCESS: Settings saved to database.\n";

} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
    exit(1);
}
echo "--- END SAML CONFIG ---\n";
