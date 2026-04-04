#!/usr/bin/env python3
import os
import sys
import django

# Nastavení prostředí pro Django - umožňuje skriptu přistupovat k databázi aplikace napřímo
sys.path.append('/code')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ciso_assistant.settings")
django.setup()

# Importy Django modelů (tabulek v databázi)
from core.models import (
    Framework, RequirementNode, Folder, Asset, Policy, OrganisationObjective,
    TaskTemplate, AssetClass
)
from django.db import transaction

# --- DATA ---
FW_REF_ID = "VYHL-410-2025"
FW_NAME = "Vyhlaska 410/2025 Sb. - Nizsi rezim (Final)"
FW_DESC = "Pozadavky pro subjekty v rezimu nizsich povinnosti podle NIS2."
ORG_NAME = "Energo-Služby s.r.o."

# Definice struktury Vyhlášky 410/2025 Sb. přímo v kódu
FW_STRUCTURE = {
    "Organizační opatření": [
        ("§ 3 Evidence aktiv", "Povinnost vést evidenci aktiv a provádět jejich hodnocení."),
        ("§ 4 Vrcholné vedení", "Stanovení rolí a odpovědností ve vedení."),
        ("§ 5 Lidské zdroje", "Zajištění školení a rozvoje zaměstnanců."),
        ("§ 14 Zvládání incidentů", "Metodika pro hlášení a řešení kybernetických incidentů.")
    ],
    "Technická opatření": [
        ("§ 6 Kontinuita", "Zajištění kontinuity činností a plány obnovy."),
        ("§ 7 Řízení přístupu", "Řízení identit, přístupových práv a MFA."),
        ("§ 8 Hesla", "Metodika a technické zajištění správy hesel."),
        ("§ 9 Detekce", "Systémy pro detekci kybernetických útoků a událostí."),
        ("§ 11 Sítě", "Zabezpečení komunikačních sítí a segmentace."),
        ("§ 12 Zranitelnosti", "Detekce a hodnocení technických zranitelností."),
        ("§ 13 Kryptografie", "Používání šifrování a správa certifikátů."),
        ("§ 16 Řízení přístupů", "Technické prostředky řízení přístupu."),
        ("§ 22 Zálohování", "Technika a periodicita zálohování dat.")
    ]
}

IMPLEMENTATION_TASKS = [
    ("Nasazení Snipe-IT", "Evidence aktiv podle § 3 (Energo-Služby)", "§ 3"),
    ("Keycloak & SSO", "Řízení přístupů podle § 7", "§ 7"),
    ("Kapacita týmu a role", "Jmenování rolí podle § 4", "§ 4"),
    ("Vaultwarden", "Správa hesel podle § 8", "§ 8"),
    ("Vzdělávací portál", "Školení uživatelů podle § 5", "§ 5"),
    ("Auditování a Logging", "Detekce událostí podle § 9", "§ 9"),
    ("Zabbix & Monitoring", "Detekce a dohled podle § 9", "§ 9"),
    ("Síťová segmentace", "Zabezpečení sítí podle § 11", "§ 11"),
    ("Trivy & OpenVAS", "Skenování zranitelností podle § 12", "§ 12"),
    ("Certifikáty & TLS", "Kryptografie podle § 13", "§ 13")
]

ASSETS = [
    ("SRV-DB-01", "Databázový server", "Server"),
    ("SRV-BACKUP-01", "Zálohovací server", "Server")
]

POLICIES = [
    ("Heslová politika", "Pravidla pro tvorbu a správu hesel."),
    ("Strategie školení uživatelů", "Plán rozvoje kybernetické bezpečnosti."),
    ("Metodika hlášení incidentů", "Postup při zjištění útoku.")
]

@transaction.atomic
def seed():
    """Hlavní funkce pro naplnění databáze. Používá transakci pro zajištění konzistence."""
    print("🌱 Zahajuji přímý import dat...")
    
    # 1. Folders - Vytvoření organizační struktury složek
    global_folder, _ = Folder.objects.get_or_create(name="Global")
    org_folder, _ = Folder.objects.get_or_create(name=ORG_NAME, defaults={"parent": global_folder})
    project_folder, _ = Folder.objects.get_or_create(name="Implementace Vyhlášky 410-2025 Sb.", defaults={"parent": org_folder})
    
    # 2. Framework - Vložení záznamu o vyhlášce do databáze
    fw, created = Framework.objects.get_or_create(
        ref_id=FW_REF_ID,
        defaults={
            "name": FW_NAME,
            "description": FW_DESC,
            "folder": global_folder,
            "annotation": "Legislativa CR"
        }
    )
    if not created:
        fw.name = FW_NAME
        fw.description = FW_DESC
        fw.folder = global_folder
        fw.save()
    print(f"   ✓ Framework: {fw.name} (ID: {fw.id})")

    # 3. Content (RequirementNodes) - Vložení jednotlivých paragrafů a požadavků
    existing_nodes = {n.ref_id: n for n in RequirementNode.objects.filter(framework=fw)}
    
    for group_name, requirements in FW_STRUCTURE.items():
        group_ref = group_name.split(' ')[0] if ' ' in group_name else group_name
        group_node = existing_nodes.get(group_ref)
        
        if not group_node:
            group_node = RequirementNode.objects.create(
                framework=fw,
                folder=global_folder,
                name=group_name,
                ref_id=group_ref,
                assessable=False,
                description=group_name,
                annotation=""
            )
            print(f"   ✓ Skupina: {group_name}")
        
        for req_name, req_desc in requirements:
            req_ref = req_name.split(' ')[0] if ' ' in req_name else req_name
            if req_ref not in existing_nodes:
                RequirementNode.objects.create(
                    framework=fw,
                    folder=global_folder,
                    parent_urn=group_node.urn,
                    name=req_name,
                    ref_id=req_ref,
                    assessable=True,
                    description=req_desc,
                    annotation=""
                )
                print(f"      - Požadavek: {req_name}")

    # 4. Tasks
    for name, desc, ref_id in IMPLEMENTATION_TASKS:
        TaskTemplate.objects.get_or_create(
            name=name,
            folder=project_folder,
            defaults={
                "description": desc,
                "ref_id": ref_id,
                "enabled": True
            }
        )
    print("   ✓ Úkoly vytvořeny.")

    # 5. Org Data - Vložení vzorových aktiv, politik a cílů organizace
    for name, desc, a_class_name in ASSETS:
        a_class, _ = AssetClass.objects.get_or_create(name=a_class_name, defaults={"folder": global_folder})
        Asset.objects.get_or_create(
            name=name,
            folder=org_folder,
            defaults={"description": desc, "asset_class": a_class}
        )
    
    for name, desc in POLICIES:
        Policy.objects.get_or_create(
            name=name,
            folder=org_folder,
            defaults={"description": desc}
        )
        
    OrganisationObjective.objects.get_or_create(
        name="Dostupnost služby",
        folder=org_folder,
        defaults={"description": "Zajištění 99.9% dostupnosti kritických systémů."}
    )
    print("   ✓ Organizační data vytvořena.")

    print("\n✅ SEEDING DOKONČEN!")

if __name__ == "__main__":
    try:
        seed()
    except Exception as e:
        print(f"❌ CHYBA: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
