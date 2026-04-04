#!/usr/bin/env python3
"""
CISO Assistant Settings Patch
=============================
Přidává RemoteUserMiddleware a AUTHENTICATION_BACKENDS pro SSO.

Použití:
    python3 patch_ciso_settings.py

Tento skript se spouští uvnitř backend kontejneru.
"""

import os
import sys

SETTINGS_PATH = '/code/ciso_assistant/settings.py'


def main():
    """
    Hlavní funkce, která upravuje settings.py v běžícím kontejneru.
    Povoluje SSO (Single Sign-On) pomocí Middlewaru Django.
    """
    print("=" * 50)
    print("  CISO ASSISTANT - PATCH SETTINGS")
    print("=" * 50)
    print(f"  Soubor: {SETTINGS_PATH}")
    print("=" * 50)

    try:
        with open(SETTINGS_PATH, 'r') as f:
            content = f.read()

        changes_made = False

        # Přidání RemoteUserMiddleware do fronty middlewaru.
        # To umožní aplikaci číst identitu uživatele z HTTP hlaviček (např. od OPNsense/NGINX).
        if 'django.contrib.auth.middleware.RemoteUserMiddleware' not in content:
            content = content.replace(
                '"django.contrib.auth.middleware.AuthenticationMiddleware",',
                '"django.contrib.auth.middleware.AuthenticationMiddleware",\n    "django.contrib.auth.middleware.RemoteUserMiddleware",'
            )
            print("   ✓ Přidán RemoteUserMiddleware")
            changes_made = True
        else:
            print("   ✓ RemoteUserMiddleware již existuje")

        # Přidání autentizačních backendů. RemoteUserBackend je nutný pro SSO.
        if 'AUTHENTICATION_BACKENDS' not in content:
            content += '''

# Remote User Authentication (SSO) - Nastavení pro vzdálené přihlašování
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.RemoteUserBackend",  # Povoluje přihlášení přes SSO
    "django.contrib.auth.backends.ModelBackend",       # Ponechává standardní přihlášení (heslo)
]
'''
            print("   ✓ Přidán AUTHENTICATION_BACKENDS")
            changes_made = True
        else:
            print("   ✓ AUTHENTICATION_BACKENDS již existuje")

        if changes_made:
            with open(SETTINGS_PATH, 'w') as f:
                f.write(content)
            print("\n   ✓ Settings úspěšně patchován!")
        else:
            print("\n   ✓ Žádné změny nebyly potřeba.")

    except FileNotFoundError:
        print(f"   ✗ Soubor nenalezen: {SETTINGS_PATH}")
        sys.exit(1)
    except Exception as e:
        print(f"   ✗ Chyba: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
