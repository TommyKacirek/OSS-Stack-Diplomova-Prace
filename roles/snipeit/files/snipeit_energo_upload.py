#!/usr/bin/env python3
"""
Snipe-IT Energo-Sluzby Seeding Script
====================================
Automatizovaně nahraje výrobce, kategorie, modely a konkrétních 
27 aktiv pro organizaci Energo-Služby s.r.o.

Použití:
    python3 snipeit_energo_upload.py

Proměnné prostředí:
    SNIPEIT_API_URL   - Base URL API (default: http://localhost:80/api/v1)
    SNIPEIT_API_KEY   - API Bearer token (POVINNÉ)
"""

import requests
import os
import sys
import json

# Configuration
API_URL = os.getenv("SNIPEIT_API_URL", "http://localhost:80/api/v1")
API_TOKEN = os.getenv("SNIPEIT_API_KEY")

if not API_TOKEN:
    print("Chyba: SNIPEIT_API_KEY není nastaven!")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# --- KONFIGURACE DAT ---
MANUFACTURERS = ["Apple", "Dell", "Generic"]
CATEGORIES = [
    {"name": "Laptops", "type": "asset"},
    {"name": "Servers", "type": "asset"},
    {"name": "Mobile Phones", "type": "asset"}
]
MODELS = [
    {"name": "MacBook Air M2", "man": "Apple", "cat": "Laptops"},
    {"name": "Dell Precision 5570", "man": "Dell", "cat": "Laptops"},
    {"name": "iPhone 15", "man": "Apple", "cat": "Mobile Phones"},
    {"name": "PowerEdge R750", "man": "Dell", "cat": "Servers"}
]

# Definice 27 aktiv (zkráceně pro skript)
ASSETS_SPEC = [
    {"tag": "SRV-001", "name": "DB-SPOTREBA-01", "model": "PowerEdge R750", "serial": "SN-SRV-101"},
    {"tag": "SRV-002", "name": "BACKUP-01", "model": "PowerEdge R750", "serial": "SN-SRV-102"},
]
# iPhony (5 ks)
for i in range(1, 6):
    ASSETS_SPEC.append({"tag": f"MOB-{i:03}", "model": "iPhone 15", "serial": f"SN-MOB-{100+i}"})
# Notebooky (20 ks)
for i in range(1, 11):
    ASSETS_SPEC.append({"tag": f"LT-A-{i:03}", "model": "MacBook Air M2", "serial": f"SN-LTA-{200+i}"})
for i in range(1, 11):
    ASSETS_SPEC.append({"tag": f"LT-D-{i:03}", "model": "Dell Precision 5570", "serial": f"SN-LTD-{300+i}"})

def get_id(endpoint, name):
    r = requests.get(f"{API_URL}/{endpoint}?search={name}", headers=HEADERS)
    if r.status_code == 200:
        data = r.json()
        for item in data.get("rows", []):
            if item.get("name") == name: return item["id"]
    return None

def main():
    print("="*60); print("  SNIPE-IT - ENERGO SEEDING"); print("="*60)
    
    # 1. Manufacturers
    print("\nManufacturers:")
    man_ids = {}
    for m in MANUFACTURERS:
        mid = get_id("manufacturers", m)
        if not mid:
            r = requests.post(f"{API_URL}/manufacturers", json={"name": m}, headers=HEADERS)
            mid = r.json().get("payload", {}).get("id")
        man_ids[m] = mid
        print(f"   {m} (ID: {mid})")

    # 2. Categories
    print("\nCategories:")
    cat_ids = {}
    for c in CATEGORIES:
        cid = get_id("categories", c["name"])
        if not cid:
            r = requests.post(f"{API_URL}/categories", json={"name": c["name"], "category_type": c["type"]}, headers=HEADERS)
            cid = r.json().get("payload", {}).get("id")
        cat_ids[c["name"]] = cid
        print(f"   {c['name']} (ID: {cid})")

    # 3. Models
    print("\nModels:")
    model_ids = {}
    for m in MODELS:
        mid = get_id("models", m["name"])
        if not mid:
            r = requests.post(f"{API_URL}/models", json={
                "name": m["name"],
                "manufacturer_id": man_ids[m["man"]],
                "category_id": cat_ids[m["cat"]],
                "model_number": m["name"][:10]
            }, headers=HEADERS)
            mid = r.json().get("payload", {}).get("id")
        model_ids[m["name"]] = mid
        print(f"   {m['name']} (ID: {mid})")

    # 4. Status Label (Ready to Deploy)
    status_id = get_id("statuslabels", "Ready to Deploy")

    # 5. Assets
    print("\nAssets (27 items):")
    created, skipped = 0, 0
    for a in ASSETS_SPEC:
        # Kontrola existence podle inventárního štítku
        check = requests.get(f"{API_URL}/hardware/bytag/{a['tag']}", headers=HEADERS)
        if check.status_code == 200 and "Asset does not exist" not in check.text:
            skipped += 1; continue

        payload = {
            "asset_tag": a["tag"],
            "status_id": status_id,
            "model_id": model_ids[a["model"]],
            "name": a.get("name", ""),
            "serial": a["serial"]
        }
        r = requests.post(f"{API_URL}/hardware", json=payload, headers=HEADERS)
        if r.status_code == 200: created += 1

    print(f"   {created} vytvořeno, {skipped} přeskočeno.")
    print("\n" + "="*60); print("  HOTOVO!"); print("="*60)

if __name__ == "__main__":
    main()
