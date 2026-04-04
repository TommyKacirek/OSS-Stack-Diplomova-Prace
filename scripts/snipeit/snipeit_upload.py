#!/usr/bin/env python3
"""
Snipe-IT API Upload Script
==========================
Nahraje základní data (manufacturers, categories, status labels) do Snipe-IT.

Použití:
    python3 snipeit_upload.py

Proměnné prostředí:
    SNIPEIT_API_URL   - Base URL API (default: http://snipe-it:80/api/v1)
    SNIPEIT_API_KEY   - API Bearer token (POVINNÉ)
"""

import requests  # Knihovna pro HTTP požadavky na API Snipe-IT
import os        # Práce s proměnnými prostředí (URL, API klíč)
import sys       # Systémové operace (ukončení skriptu)

# --- KONFIGURACE ---
# URL adresa a API token pro autorizaci požadavků
API_URL = os.getenv("SNIPEIT_API_URL", "http://snipe-it:80/api/v1")
API_TOKEN = os.getenv("SNIPEIT_API_KEY")

if not API_TOKEN:
    print("✗ Chyba: SNIPEIT_API_KEY není nastaven! API token je nutný pro autorizaci.")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",  # Předání Bearer tokenu v hlavičce
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# --- DATA PRO IMPORT ---

# Seznam výrobců hardwaru
MANUFACTURERS = [
    {"name": "Apple", "url": "https://apple.com"},
    {"name": "Dell", "url": "https://dell.com"},
    {"name": "Lenovo", "url": "https://lenovo.com"},
    {"name": "HP", "url": "https://hp.com"},
    {"name": "Microsoft", "url": "https://microsoft.com"},
    {"name": "Cisco", "url": "https://cisco.com"},
    {"name": "Samsung", "url": "https://samsung.com"},
    {"name": "ASUS", "url": "https://asus.com"},
]

# Kategorie aktiv (asset), příslušenství (accessory), spotřebního materiálu (consumable) a licencí (license)
CATEGORIES = [
    {"name": "Laptops", "category_type": "asset", "eula_text": "Prosím, starejte se o svůj notebook."},
    {"name": "Desktops", "category_type": "asset"},
    {"name": "Servers", "category_type": "asset"},
    {"name": "Mobile Phones", "category_type": "asset"},
    {"name": "Tablets", "category_type": "asset"},
    {"name": "Networking", "category_type": "asset"},
    {"name": "Monitors", "category_type": "asset"},
    {"name": "Printers", "category_type": "asset"},
    {"name": "Keyboards", "category_type": "accessory"},
    {"name": "Mice", "category_type": "accessory"},
    {"name": "Headsets", "category_type": "accessory"},
    {"name": "Cables", "category_type": "consumable"},
    {"name": "Software Licenses", "category_type": "license"},
    {"name": "Operating Systems", "category_type": "license"},
]

# Stavy aktiv (nasaditelný, v opravě, ztracený, archivovaný)
STATUS_LABELS = [
    {"name": "Ready to Deploy", "type": "deployable", "notes": "Aktiva připravená k přidělení uživateli."},
    {"name": "Deployed", "type": "deployable", "notes": "Aktivum je aktuálně u uživatele."},
    {"name": "In Repair", "type": "pending", "notes": "Aktivum se momentálně opravuje."},
    {"name": "Pending Return", "type": "pending", "notes": "Čeká se na vrácení aktiva od uživatele."},
    {"name": "Lost/Stolen", "type": "undeployable", "notes": "Ztracené nebo ukradené aktivum."},
    {"name": "Broken", "type": "undeployable", "notes": "Poškozené aktivum bez možnosti opravy."},
    {"name": "Archived/Disposed", "type": "archived", "notes": "Aktivum bylo vyřazeno z evidence."},
]


def create_if_not_exists(endpoint, payload, search_field="name"):
    """
    Pomocná funkce, která nejprve zkusí vyhledat záznam podle jména.
    Pokud neexistuje, vytvoří jej pomocí POST požadavku.
    To zajišťuje, že skript je 'idempotentní' (lze ho spouštět opakovaně).
    """
    name = payload.get(search_field)
    search_url = f"{API_URL}/{endpoint}?search={name}"
    
    try:
        # Check if exists
        r = requests.get(search_url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if data.get("total", 0) > 0:
            for item in data.get("rows", []):
                if item.get(search_field) == name:
                    return "exists", item

        # Create new
        r = requests.post(f"{API_URL}/{endpoint}", json=payload, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return "created", r.json().get("payload")
        
    except requests.exceptions.RequestException as e:
        return "error", str(e)


def main():
    """Hlavní smyčka skriptu, která postupně nahrává výrobce, kategorie a stavy."""
    print("=" * 60)
    print("  SNIPE-IT - API UPLOAD")
    print("=" * 60)
    print(f"  API URL:  {API_URL}")
    print("=" * 60)

    # 1. Manufacturers
    print("\n📦 Manufacturers:")
    created, existed, errors = 0, 0, 0
    for m in MANUFACTURERS:
        status, _ = create_if_not_exists("manufacturers", m)
        if status == "created": created += 1
        elif status == "exists": existed += 1
        else: errors += 1
    print(f"   ✓ {created} vytvořeno, {existed} existuje, {errors} chyb")

    # 2. Categories
    print("\n📁 Categories:")
    created, existed, errors = 0, 0, 0
    for c in CATEGORIES:
        status, _ = create_if_not_exists("categories", c)
        if status == "created": created += 1
        elif status == "exists": existed += 1
        else: errors += 1
    print(f"   ✓ {created} vytvořeno, {existed} existuje, {errors} chyb")

    # 3. Status Labels
    print("\n🏷️  Status Labels:")
    created, existed, errors = 0, 0, 0
    for s in STATUS_LABELS:
        status, _ = create_if_not_exists("statuslabels", s)
        if status == "created": created += 1
        elif status == "exists": existed += 1
        else: errors += 1
    print(f"   ✓ {created} vytvořeno, {existed} existuje, {errors} chyb")

    print("\n" + "=" * 60)
    print("  ✓ HOTOVO! Základní data nahrána do Snipe-IT.")
    print("=" * 60)


if __name__ == "__main__":
    main()
