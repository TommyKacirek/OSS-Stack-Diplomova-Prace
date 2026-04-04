#!/usr/bin/env python3
"""
Skript pro inicializaci legislativních rámců a konfiguraci dat přes REST API
===========================================================================
Automaticky importuje legislativu (Vyhláška 410/2025 Sb.), implementační úkoly 
a data fiktivní organizace Energo-Služby s.r.o. do systému CISO Assistant.

Použití:
    python3 ciso_upload.py
"""

import requests  # Knihovna pro HTTP požadavky (komunikace s API)
import urllib3   # Pro správu síťových připojení
import sys       # Systémové operace (ukončení skriptu)
import os        # Práce s proměnnými prostředí (URL, hesla)
import warnings  # Správa varovných hlášení
import json      # Práce s datovým formátem JSON

# --- KONFIGURACE ---
# Základní URL adresa API, uživatelské jméno a heslo pro přístup do CISO Assistant
BASE_URL = os.getenv("CISO_API_URL", "http://localhost:8000/api")
USERNAME = os.getenv("CISO_USERNAME", "admin@oss.local")
PASSWORD = os.getenv("CISO_PASSWORD", "StrongPassword123")

# --- SUPPRESS WARNINGS ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=UserWarning, module='urllib3')

# --- DATA PRO FRAMEWORK ---
# Definice legislativního rámce (Vyhláška 410/2025 Sb.)
FW_REF_ID = "VYHL-410-2025-v7"
FW_NAME = "Vyhlaska 410/2025 Sb. - Nizsi rezim (Final)"
FW_DESC = "Pozadavky pro subjekty v rezimu nizsich povinnosti."

# Hierarchická struktura vyhlášky rozdělená na organizační a technická opatření
FW_STRUCTURE = {
    "Organizační opatření": [
        ("§ 3 Evidence aktiv", "Povinnost vést evidenci aktiv."),
        ("§ 4 Vrcholné vedení", "Jmenování rolí a odpovědnosti."),
        ("§ 5 Lidské zdroje", "Školení a osvěta."),
        ("§ 14 Zvládání incidentů", "Proces hlášení a řešení incidentů.")
    ],
    "Technická opatření": [
        ("§ 6 Kontinuita", "Zálohování a plány obnovy."),
        ("§ 7 Řízení přístupu", "Řízení identit, SSO a MFA."),
        ("§ 8 Hesla", "Bezpečná správa hesel."),
        ("§ 9 Detekce", "Detekce bezpečnostních událostí."),
        ("§ 11 Sítě", "Bezpečnost sítí a segmentace."),
        ("§ 12 Zranitelnosti", "Řízení a skenování zranitelností."),
        ("§ 13 Kryptografie", "Šifrování a správa certifikátů."),
        ("§ 16 Řízení přístupů", "Technické řízení přístupů."),
        ("§ 22 Zálohování", "Technické zálohování.")
    ]
}

# --- IMPLEMENTAČNÍ ÚKOLY ---
# Seznam úkolů, které propojují legislativní požadavky s konkrétními technickými nástroji
IMPLEMENTATION_TASKS = [
    {"name": "§3 Evidence aktiv: Nasadit Snipe-IT", "description": "Nasadit a nakonfigurovat Snipe-IT pro evidenci aktiv.", "ref_id": "TASK-SNIPE-IT"},
    {"name": "§4 Vrcholné vedení: Jmenování rolí", "description": "Jmenovat osobu pověřenou kybernetickou bezpečností.", "ref_id": "TASK-ROLES"},
    {"name": "§5 Lidské zdroje: Školení (Moodle/Gophish)", "description": "Zavést systém pro řízení vzdělávání a simulaci phishingu.", "ref_id": "TASK-TRAINING"},
    {"name": "§6 Kontinuita: Zálohování (Restic)", "description": "Nasadit Restic pro šifrované zálohování dat.", "ref_id": "TASK-BACKUP"},
    {"name": "§7 Řízení přístupu: Nasadit Keycloak", "description": "Nasadit Keycloak jako centrální IdP a SSO.", "ref_id": "TASK-KEYCLOAK"},
    {"name": "§8 Hesla: Nasadit Vaultwarden", "description": "Nasadit Vaultwarden pro bezpečnou správu hesel.", "ref_id": "TASK-VAULTWARDEN"},
    {"name": "§9 Detekce: Nasadit Wazuh a Suricata", "description": "Nasadit Wazuh (SIEM) a Suricata (IDS) pro detekci incidentů.", "ref_id": "TASK-WAZUH"},
    {"name": "§11 Sítě: Nasadit OPNsense", "description": "Nasadit OPNsense firewall pro segmentaci sítě.", "ref_id": "TASK-OPNSENSE"},
    {"name": "§12 Zranitelnosti: Nasadit OpenVAS", "description": "Nasadit OpenVAS pro pravidelné skenování zranitelností.", "ref_id": "TASK-OPENVAS"},
    {"name": "§13 Kryptografie: Nasadit EJBCA a Matrix", "description": "Nasadit EJBCA pro certifikáty a Matrix pro šifrovanou komunikaci.", "ref_id": "TASK-CRYPTO"}
]

# --- DATA PRO ORGANIZACI (Energo-Služby s.r.o.) ---
ORG_NAME = "Energo-Služby s.r.o."
POLICIES = [
    ("BP-2026-01", "Bezpečnostní politika - hesla", "Min 12 znaků pro uživatele, 17 pro adminy."),
    ("S-2026-01", "Plán školení", "Vstupní školení pro nováčky a pravidelné roční školení."),
    ("M-2026-01", "Metodika posuzování incidentů", "Kanál pro hlášení neobvyklého chování (helpdesk/email).")
]
ASSETS = [
    ("SRV-DB-01", "Databázový server s daty o spotřebě (Primární aktivum).", "High"),
    ("SRV-BACKUP-01", "Zálohovací server umístěný v odděleném segmentu.", "High")
]

def get_headers(token):
    """Pomocná funkce pro vygenerování HTTP hlaviček s autorizačním tokenem."""
    return {"Authorization": f"Token {token}", "Content-Type": "application/json"}

def login():
    """Provede přihlášení do API a vrátí autorizační token."""
    print("🔐 Přihlašuji se...")
    endpoints = [
        (f"{BASE_URL}/iam/login/", {"username": USERNAME, "password": PASSWORD}),
        (f"{BASE_URL}/_allauth/app/v1/auth/login", {"email": USERNAME, "password": PASSWORD}),
    ]
    for url, payload in endpoints:
        try:
            r = requests.post(url, json=payload, verify=False, timeout=10)
            if r.status_code == 200:
                data = r.json()
                for key in ["token", "key", "session_token"]:
                    if key in data:
                        print(f"   ✓ Přihlášen")
                        return data[key]
        except: continue
    print("   ✗ Login selhal."); sys.exit(1)

def create_framework(headers, folder_id=None):
    """Zkontroluje existenci frameworku (vyhlášky) a pokud neexistuje, vytvoří jej."""
    print(f"\n📋 Zpracovávám Framework: '{FW_NAME}'...")
    try:
        r = requests.get(f"{BASE_URL}/frameworks/?search={FW_REF_ID}", headers=headers, verify=False)
        for fw in r.json().get('results', []):
            if fw['ref_id'] == FW_REF_ID:
                print(f"   ✓ Framework již existuje (ID: {fw['id']})")
                return fw['id']
    except: pass
    
    payload = {
        "name": FW_NAME, 
        "description": FW_DESC, 
        "ref_id": FW_REF_ID, 
        "is_active": True, 
        "annotation": "Legislativa CR",
        "reference_controls": []
    }
    if folder_id:
        payload["folder"] = folder_id
        
    r = requests.post(f"{BASE_URL}/frameworks/", json=payload, headers=headers, verify=False)
    if r.status_code == 201:
        fid = r.json()['id']
        print(f"   ✓ Framework vytvořen (ID: {fid})")
        return fid
    else:
        print(f"   ✗ Chyba při vytváření frameworku ({r.status_code}): {r.text}")
    return None

def create_content(headers, fw_id):
    """Nahraje konkrétní paragrafy a požadavky vyhlášky do frameworku."""
    if not fw_id: return
    print(f"📋 Nahrávám obsah pro Framework (ID: {fw_id})...")
    
    # 0. Zjistíme složku (folder) frameworku, abychom ji mohli přiřadit uzlům
    fw_resp = requests.get(f"{BASE_URL}/frameworks/{fw_id}/", headers=headers, verify=False)
    folder_data = fw_resp.json().get('folder', {})
    folder_id = folder_data.get('id') if isinstance(folder_data, dict) else folder_data
    if not folder_id:
        print("   ✗ Nepodařilo se zjistit složku frameworku.")
        return

    # 1. Zjistíme stávající uzly (RequirementNode), abychom se vyhnuli duplicitám
    r_list = requests.get(f"{BASE_URL}/requirement-nodes/?framework={fw_id}", headers=headers, verify=False)
    existing_nodes = {}
    if r_list.status_code == 200:
        for node in r_list.json().get('results', []):
            existing_nodes[node['ref_id']] = node['id']

    for group_name, requirements in FW_STRUCTURE.items():
        # Uzel pro skupinu (Paragraph/Group) - assessable=False
        group_ref_id = group_name.split(' ')[0] if ' ' in group_name else group_name
        group_id = existing_nodes.get(group_ref_id)
        
        if not group_id:
            payload = {
                "framework": fw_id,
                "folder": folder_id,
                "name": group_name,
                "ref_id": group_ref_id,
                "assessable": False,
                "description": group_name,
                "annotation": "",
                "threats": [],
                "display_short": group_name,
                "display_long": group_name,
                "reference_controls": []
            }
            r = requests.post(f"{BASE_URL}/requirement-nodes/", json=payload, headers=headers, verify=False)
            if r.status_code == 201:
                group_id = r.json()['id']
                print(f"   ✓ Skupina vytvořena: {group_name}")
            else:
                print(f"   ✗ Chyba při vytváření skupiny {group_name} ({r.status_code}): {r.text}")
                continue
        else:
            print(f"   ✓ Skupina již existuje: {group_name}")

        # Uzly pro konkrétní požadavky - assessable=True
        for req_name, req_desc in requirements:
            req_ref_id = req_name.split(' ')[0] if ' ' in req_name else req_name
            if existing_nodes.get(req_ref_id):
                print(f"      - Požadavek již existuje: {req_name}")
                continue
                
            payload = {
                "framework": fw_id,
                "folder": folder_id,
                "parent": group_id,
                "name": req_name,
                "description": req_desc,
                "ref_id": req_ref_id,
                "assessable": True,
                "annotation": "",
                "threats": [],
                "display_short": req_name,
                "display_long": f"{req_name}: {req_desc}",
                "reference_controls": []
            }
            r = requests.post(f"{BASE_URL}/requirement-nodes/", json=payload, headers=headers, verify=False)
            if r.status_code == 201:
                print(f"      - Požadavek vytvořen: {req_name}")
            else:
                print(f"      ✗ Chyba u {req_name}: {r.text}")

def create_folder(headers, name):
    """Vytvoří novou složku v aplikaci, pokud již neexistuje (slouží k organizaci dat)."""
    try:
        r = requests.get(f"{BASE_URL}/folders/?search={name}", headers=headers, verify=False)
        for f in r.json().get('results', []):
            if f['name'] == name: return f['id']
    except: pass
    r = requests.post(f"{BASE_URL}/folders/", json={"name": name, "parent": None}, headers=headers, verify=False)
    return r.json().get('id') if r.status_code in [201, 200] else None

def create_organization_data(headers):
    """Nahraje vzorová data organizace: perimetry, politiky, aktiva a cíle."""
    print(f"\n🏢 Vytvářím data pro organizaci: {ORG_NAME}...")
    folder_id = create_folder(headers, ORG_NAME)
    if not folder_id: return
    
    # Perimeters
    requests.post(f"{BASE_URL}/perimeters/", json={"name": "Distribuce dat o spotrebě", "folder": folder_id}, headers=headers, verify=False)

    # Policies
    for code, name, desc in POLICIES:
        requests.post(f"{BASE_URL}/policies/", json={"name": name, "description": desc, "folder": folder_id, "ref_id": code}, headers=headers, verify=False)

    # Assets
    for name, desc, crit in ASSETS:
        requests.post(f"{BASE_URL}/assets/", json={"name": name, "description": desc, "folder": folder_id}, headers=headers, verify=False)

    # Objectives
    requests.post(f"{BASE_URL}/organisation-objectives/", json={"name": "Dostupnost služby", "description": "Max výpadek 4 hodiny.", "folder": folder_id}, headers=headers, verify=False)
    print("   ✓ Data organizace vytvořena.")

def create_tasks(headers):
    """Vytvoří v aplikaci šablony úkolů (implementační kroky pro nástroje)."""
    print(f"\n📋 Vytvářím implementační úkoly...")
    folder_id = create_folder(headers, "Implementace Vyhlášky 410-2025 Sb.")
    for task in IMPLEMENTATION_TASKS:
        payload = {
            "name": task['name'], 
            "description": task['description'], 
            "ref_id": task['ref_id'], 
            "folder": folder_id,
            "enabled": True
        }
        requests.post(f"{BASE_URL}/task-templates/", json=payload, headers=headers, verify=False)
    print("   ✓ Úkoly vytvořeny.")

def main():
    print("=" * 60)
    print("  CISO ASSISTANT - API UPLOAD (MERGED)")
    print("=" * 60)
    token = login()
    if not token: return
    headers = get_headers(token)
    
    # Najít cílovou složku
    folder_id = create_folder(headers, ORG_NAME)
    
    fw_id = create_framework(headers, folder_id)
    create_content(headers, fw_id)
    create_tasks(headers)
    create_organization_data(headers)
    
    print("\n" + "=" * 60)
    print("  ✓ HOTOVO! Všechna data jsou uložena.")
    print("=" * 60)

if __name__ == "__main__":
    main()
