<?php
/**
 * inject_saml.php
 *
 * Skript pro injekci SAML konfigurace do databáze Snipe-IT.
 * Čte flat konfiguraci z /tmp/saml_settings_flat.txt (formát key=value)
 * a uloží ji do tabulky settings jako saml_custom_settings.
 *
 * Spouštění: php inject_saml.php (uvnitř Docker kontejneru snipeit)
 * Volán automaticky přes Ansible task po startu kontejneru.
 */

// Inicializace Laravel bootstrapu pro přístup k Eloquent ORM
require __DIR__ . '/vendor/autoload.php';
$app = require_once __DIR__ . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

try {
    // Načti první (a jediný) řádek nastavení z tabulky settings
    $s = App\Models\Setting::first();
    if (!$s) {
        throw new Exception("Settings not found");
    }

    // Načti SAML konfiguraci ze souboru vygenerovaného Ansiblem
    // Soubor obsahuje flat key=value páry s dynamickým X.509 certifikátem Keycloaku
    $config_content = file_get_contents('/tmp/saml_settings_flat.txt');
    if ($config_content === false) {
        throw new Exception("Could not read /tmp/saml_settings_flat.txt");
    }

    // Ulož SAML konfiguraci do databáze a aktivuj SAML přihlašování
    $s->saml_custom_settings = $config_content;
    $s->saml_idp_metadata = null;          // Nepoužíváme XML metadata, pouze flat config
    $s->saml_enabled = 1;                  // Zapni SAML v Snipe-IT
    $s->saml_attr_mapping_username = 'username'; // Mapování atributu username z Keycloaku
    $s->save();

    echo "SAML Config Injected Successfully.\n";
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
    exit(1);
}
