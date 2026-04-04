<?php
// Force SQL update to bypass any Model weirdness
chdir('/var/www/html');
require __DIR__ . '/vendor/autoload.php';
$app = require_once __DIR__ . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

use Illuminate\Support\Facades\DB;

echo "--- START FORCE CONFIG ---\n";
try {
    // 1. Fetch Metadata
    $metadataUrl = 'https://auth.oss.local/realms/Lab/protocol/saml/descriptor';
    $arrContextOptions=array("ssl"=>array("verify_peer"=>false,"verify_peer_name"=>false));  
    $xmlContent = @file_get_contents($metadataUrl, false, stream_context_create($arrContextOptions));
    if (!$xmlContent) throw new Exception("Metadata fetch failed.");
    
    preg_match('/<ds:X509Certificate>(.*?)<\/ds:X509Certificate>/s', $xmlContent, $matches);
    $cert = trim(str_replace(["\r", "\n", " "], '', $matches[1]));

    // 2. Construct JSON
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
    $json = json_encode($samlSettings);

    // 3. FORCE UPDATE via DB Facade (Raw)
    $affected = DB::table('settings')->update([
        'saml_enabled' => 1,
        'saml_idp_metadata' => null,
        'saml_custom_settings' => $json,
        'saml_attr_mapping_username' => 'username',
        'saml_forcelogin' => 0
    ]);

    echo "Update executed. Rows affected: $affected\n";
    
    // Verify immediately
    $current = DB::table('settings')->value('saml_custom_settings');
    echo "Verification (Length): " . strlen($current) . "\n";

} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
    exit(1);
}
echo "--- END FORCE CONFIG ---\n";
