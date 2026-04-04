<?php
try {
    $s = App\Models\Setting::first();
    if (!$s) {
        $s = new App\Models\Setting();
        $s->site_name = 'OSS Lab';
        $s->locale = 'en-US';
        $s->auto_increment_assets = 1;
        $s->alert_email = 'admin@oss.local';
        $s->next_auto_tag_base = 1000;
        $s->default_currency = 'USD';
        $s->brand = 1;
    }

    $cert = 'MIIClTCCAX0CBgGbJ5FoeTANBgkqhkiG9w0BAQsFADAOMQwwCgYDVQQDDANMYWIwHhcNMjUxMjE2MTQyODE5WhcNMzUxMjE2MTQyOTU5WjAOMQwwCgYDVQQDDANMYWIwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCOBlB3FMe+b1RwyvpO+xO9BXkQFkbetF6ucKgU117WNGBYRS1uteQDYJQ2h/eihbq5RW3wG5IbnBsk+pvnkcizcovaETW6D2H/DTRciiv8VyhLRKYQAJ/rBRsAQWaGD1/ukfmOHS46JmoU28cpn8jsGMiCvipsS0uxM8/CQSEGBjXl/0/6jYCpYOqW++B8cZ9Nygay+3azTdmMQNUNWg8/bp3Ppk6iTTs9KMcFenZfjMg2syxrDPal3EEWhKPzcP3SlHXwDylIohSP5QG3OhUVHAamPtjG/Dw/XrYOfkT76cwLaqbp9l38l/m8kf2nl3H0klj0g95refKuUKWyFy3XAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAEqmVUyp29Ze1F26hStSAfLZ7ToRBbofH/+hFsEESdhGcz7uPzXvPK85YHFBYOcwtdfgS137ZF0HhPi8DUqWvoaxTosjnNlDMkx4NQlbMtV7mZe2ZxDHt/erxYbwCt526ihPFpAYmqFa1wqXMB2MaRjDp5PjT+T0xljvSEApx9xbaZJqcEVzv4QQodlOceGXLLWbuRoNd1SrkK8TBFRSQLU1mh1x9FuIghY4SEDSw1EApztilks+iXkYIDJ/BM5l4cpREZKH8sPKWe5j8BF+kMX7pAIELH3snPrXbUBK2JPSLkd1T++3NnIACbvrGU7Ssvf90jIJeSjz+byeRd8OKSM=';
    
    $settings = [
        'idp' => [
            'entityId' => 'https://auth.oss.local/realms/Lab',
            'singleSignOnService' => [
                'url' => 'https://auth.oss.local/realms/Lab/protocol/saml',
                'binding' => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
            ],
            'singleLogoutService' => [
                'url' => 'https://auth.oss.local/realms/Lab/protocol/saml',
                'binding' => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
            ],
            'x509cert' => $cert,
        ],
    ];

    $s->saml_enabled = 1;
    $s->saml_idp_metadata = null; // Clear metadata XML to force custom settings
    $s->saml_custom_settings = json_encode($settings);
    $s->saml_attr_mapping_username = 'username';
    $s->saml_forcelogin = 0;
    
    $s->save();
    echo "Settings updated successfully (Manual Config).\n";

} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
    exit(1);
}
