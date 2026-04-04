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

import requests
import os
import sys

# Configuration
API_URL = os.getenv("SNIPEIT_API_URL", "http://snipe-it:80/api/v1")
API_TOKEN = os.getenv("SNIPEIT_API_KEY")

if not API_TOKEN:
    print("Chyba: SNIPEIT_API_KEY není nastaven!")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# --- DATA ---

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

# Types: asset, accessory, consumable, component, license
CATEGORIES = [
    {"name": "Laptops", "category_type": "asset", "eula_text": "Please take care of your laptop."},
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

# Types: deployable, pending, undeployable, archived
STATUS_LABELS = [
    {"name": "Ready to Deploy", "type": "deployable", "notes": "Asset is ready to be assigned."},
    {"name": "Deployed", "type": "deployable", "notes": "Asset is currently assigned to a user."},
    {"name": "In Repair", "type": "pending", "notes": "Asset is currently being repaired."},
    {"name": "Pending Return", "type": "pending", "notes": "Asset is pending return from user."},
    {"name": "Lost/Stolen", "type": "undeployable", "notes": "Asset is missing or stolen."},
    {"name": "Broken", "type": "undeployable", "notes": "Asset is damaged beyond repair."},
    {"name": "Archived/Disposed", "type": "archived", "notes": "Asset has been disposed of."},
]


def create_if_not_exists(endpoint, payload, search_field="name"):
    """Vytvoří záznam pokud neexistuje."""
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
    print("=" * 60)
    print("  SNIPE-IT - API UPLOAD")
    print("=" * 60)
    print(f"  API URL:  {API_URL}")
    print("=" * 60)

    # 1. Manufacturers
    print("\nManufacturers:")
    created, existed, errors = 0, 0, 0
    for m in MANUFACTURERS:
        status, _ = create_if_not_exists("manufacturers", m)
        if status == "created": created += 1
        elif status == "exists": existed += 1
        else: errors += 1
    print(f"   {created} vytvořeno, {existed} existuje, {errors} chyb")

    # 2. Categories
    print("\nCategories:")
    created, existed, errors = 0, 0, 0
    for c in CATEGORIES:
        status, _ = create_if_not_exists("categories", c)
        if status == "created": created += 1
        elif status == "exists": existed += 1
        else: errors += 1
    print(f"   {created} vytvořeno, {existed} existuje, {errors} chyb")

    # 3. Status Labels
    print("\nStatus Labels:")
    created, existed, errors = 0, 0, 0
    for s in STATUS_LABELS:
        status, _ = create_if_not_exists("statuslabels", s)
        if status == "created": created += 1
        elif status == "exists": existed += 1
        else: errors += 1
    print(f"   {created} vytvořeno, {existed} existuje, {errors} chyb")

    print("\n" + "=" * 60)
    print("  HOTOVO! Základní data nahrána do Snipe-IT.")
    print("=" * 60)


if __name__ == "__main__":
    main()
