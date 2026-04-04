#!/usr/bin/env python3
"""
Snipe-IT Demo Data Generator
============================
Creates demo asset models and hardware assets.
"""

import requests  # API komunikace
import os        # Práce se systémem a cestami
import sys       # Práce s parametry skriptu
import random    # Pro simulaci náhodných dat (pokud je potřeba)

# --- KONFIGURACE ---
API_URL = os.getenv("SNIPEIT_API_URL", "http://snipe-it:80/api/v1")
API_TOKEN = os.getenv("SNIPEIT_API_KEY")

if not API_TOKEN:
    print("✗ Chyba: SNIPEIT_API_KEY není nastaven!")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Definice modelů hardwaru, které se v organizaci používají
MODELS = [
    {"name": "MacBook Pro 14 M3", "manufacturer": "Apple", "category": "Laptops", "model_number": "A2992"},
    {"name": "ThinkPad X1 Carbon Gen 11", "manufacturer": "Lenovo", "category": "Laptops", "model_number": "21HM"},
    {"name": "Dell XPS 15", "manufacturer": "Dell", "category": "Laptops", "model_number": "9530"},
    {"name": "iPhone 15 Pro", "manufacturer": "Apple", "category": "Mobile Phones", "model_number": "A3102"},
    {"name": "Cisco Catalyst 9200", "manufacturer": "Cisco", "category": "Networking", "model_number": "C9200L"},
]

# Konkrétní kusy hardwaru (assets) s unikátními ID (tagy) a sériovými čísly
ASSETS = [
    {"tag": "HW-001", "model": "MacBook Pro 14 M3", "status": "Ready to Deploy", "serial": "C02XYZ123"},
    {"tag": "HW-002", "model": "MacBook Pro 14 M3", "status": "Deployed", "serial": "C02ABC456", "name": "Kaca's MacBook"},
    {"tag": "HW-003", "model": "ThinkPad X1 Carbon Gen 11", "status": "Ready to Deploy", "serial": "PF123456"},
    {"tag": "HW-004", "model": "Dell XPS 15", "status": "In Repair", "serial": "8JKL901"},
    {"tag": "HW-005", "model": "iPhone 15 Pro", "status": "Ready to Deploy", "serial": "F1234567890"},
    {"tag": "NET-001", "model": "Cisco Catalyst 9200", "status": "Deployed", "serial": "FDO12345678", "name": "Core Switch"},
]

def get_id(endpoint, name):
    """
    Pomocná funkce, která vyhledá ID objektu (výrobce, kategorie, stavu) 
    podle jeho jména, protože API pro vytvoření modelu vyžaduje číselná ID.
    """
    try:
        r = requests.get(f"{API_URL}/{endpoint}?search={name}", headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        for item in data.get("rows", []):
            if item["name"] == name:
                return item["id"]
    except Exception as e:
        print(f"Error finding {name} in {endpoint}: {e}")
    return None

def main():
    """Hlavní logika: nejprve vytvoří modely a poté do nich nahraje konkrétní aktiva."""
    print("="*60)
    print("  SNIPE-IT DEMO DATA GENERATOR")
    print("="*60)

    # 1. Create Models
    print("\n💻 Models:")
    for m in MODELS:
        # Check if exists
        model_id = get_id("models", m["name"])
        if model_id:
            print(f"   ✓ {m['name']} exists (ID: {model_id})")
            continue

        # Get dependency IDs
        man_id = get_id("manufacturers", m["manufacturer"])
        cat_id = get_id("categories", m["category"])
        
        if not man_id or not cat_id:
            print(f"   ✗ Skipping {m['name']}: Manufacturer or Category not found")
            continue

        payload = {
            "name": m["name"],
            "manufacturer_id": man_id,
            "category_id": cat_id,
            "model_number": m["model_number"]
        }
        
        try:
            r = requests.post(f"{API_URL}/models", json=payload, headers=HEADERS)
            r.raise_for_status()
            print(f"   ✓ Created {m['name']}")
        except Exception as e:
            print(f"   ✗ Error creating {m['name']}: {e}")

    # 2. Create Assets
    print("\n📦 Assets:")
    for a in ASSETS:
        # Check if exists
        try:
            r = requests.get(f"{API_URL}/hardware/bytag/{a['tag']}", headers=HEADERS)
            if r.status_code == 200:
                 print(f"   ✓ {a['tag']} exists")
                 continue
        except: pass

        model_id = get_id("models", a["model"])
        status_id = get_id("statuslabels", a["status"])

        if not model_id or not status_id:
             print(f"   ✗ Skipping {a['tag']}: Model or Status not found")
             continue

        payload = {
            "asset_tag": a["tag"],
            "status_id": status_id,
            "model_id": model_id,
            "serial": a.get("serial"),
            "name": a.get("name", "")
        }

        try:
            r = requests.post(f"{API_URL}/hardware", json=payload, headers=HEADERS)
            if r.status_code == 200 and r.json().get("status") == "success":
                print(f"   ✓ Created {a['tag']} ({a['model']})")
            else:
                print(f"   ✗ Failed {a['tag']}: {r.text}")
        except Exception as e:
            print(f"   ✗ Error creating {a['tag']}: {e}")

    print("\n" + "="*60)
    print("  ✓ HOTOVO! Demo data nahrána.")

if __name__ == "__main__":
    main()
