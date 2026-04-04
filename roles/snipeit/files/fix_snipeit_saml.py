#!/usr/bin/env python3
"""
Snipe-IT SAML Hotfix Script
============================
Opravuje PHP middleware pro správnou funkci SAML SSO za reverse proxy (Caddy).

Problém:
  OneLogin PHP-SAML library ignoruje X-Forwarded-Proto header, protože
  Laravel's TrustProxies middleware nemá nastavené $proxies.
  Výsledek: currentURL = http:// místo https:// -> Recipient mismatch -> HTTP 400.

Opravy:
  1. Saml.php: setProxyVars(true) místo request()->isFromTrustedProxy()
  2. TrustProxies.php: $proxies = "*" pro důvěru Caddy proxy
  3. EncryptCookies.php: snipeit_session vyňat z šifrování (ACS route je mimo web group)

Použití (uvnitř kontejneru):
  python3 /tmp/fix_snipeit_saml.py

Spouští se přes Ansible task po startu kontejneru.
"""

import sys

FIXES = [
    {
        "file": "/var/www/html/app/Services/Saml.php",
        "old": "OneLogin_Saml2_Utils::setProxyVars(request()->isFromTrustedProxy());",
        "new": "OneLogin_Saml2_Utils::setProxyVars(true); // Always behind Caddy reverse proxy",
        "desc": "Saml.php: force proxyVars=true",
    },
    {
        "file": "/var/www/html/app/Http/Middleware/TrustProxies.php",
        "old": "protected $proxies;",
        "new": 'protected $proxies = "*";',
        "desc": "TrustProxies.php: trust all proxies",
    },
    {
        "file": "/var/www/html/app/Http/Middleware/EncryptCookies.php",
        "old": "    protected $except = [\n        //\n    ];",
        "new": "    protected $except = [\n        'snipeit_session',\n    ];",
        "desc": "EncryptCookies.php: exclude snipeit_session",
    },
]

errors = 0
for fix in FIXES:
    try:
        with open(fix["file"]) as f:
            content = f.read()
        if fix["new"] in content:
            print(f"   OK {fix['desc']} (already applied)")
            continue
        if fix["old"] not in content:
            print(f"   WARN {fix['desc']} (pattern not found - may be different version)")
            continue
        content = content.replace(fix["old"], fix["new"])
        with open(fix["file"], "w") as f:
            f.write(content)
        print(f"   OK {fix['desc']} - APPLIED")
    except Exception as e:
        print(f"   ERROR {fix['desc']}: {e}")
        errors += 1

if errors:
    print(f"\n{errors} error(s) occurred.")
    sys.exit(1)
else:
    print("\nVsechny Snipe-IT SAML hotfixy aplikovany uspesne.")
