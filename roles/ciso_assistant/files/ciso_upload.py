#!/usr/bin/env python3
"""
CISO Assistant - Seed Script
=============================
Nahraje celou strukturu Vyhlášky 410/2025 Sb. (nižší režim, §1–§14),
organizační data Energo-Služby s.r.o. a namapuje nástroje OSS stacku
na jednotlivé požadavky přes compliance assessment.

Spouští se uvnitř kontejneru cisobackend:
    docker exec cisobackend /code/.venv/bin/python3 /code/ciso_upload.py
"""

import os
import sys
import django

sys.path.append('/code')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ciso_assistant.settings")
django.setup()

from core.models import (
    Framework, RequirementNode, Folder, Asset, Policy,
    OrganisationObjective, TaskTemplate, ComplianceAssessment,
    RequirementAssessment, Perimeter
)
from django.db import transaction

# ---------------------------------------------------------------------------
# FRAMEWORK: Vyhláška 410/2025 Sb. – nižší režim
# ---------------------------------------------------------------------------
FW_REF_ID = "VYHL-410-2025"
FW_NAME = "Vyhlaska 410/2025 Sb. - Nizsi rezim"
FW_DESC = "Minimalni pozadavky na kybernetickou bezpecnost pro subjekty v rezimu nizsich povinnosti (ZKB c. 264/2025 Sb.)."

# Struktura: skupina -> [(ref_id, nazev, popis, assessable), ...]
FW_STRUCTURE = {
    "Obecna ustanoveni": [
        ("§1",  "§ 1 Predmet upravy",
         "Vymezeni predmetu a rozsahu upravy kyberneticke bezpecnosti.",
         False),
        ("§2",  "§ 2 Vymezeni pojmu",
         "Definice pojmu pouzivanych v teto vyhlasce.",
         False),
        ("§3",  "§ 3 System zajistovani minimalni kyberneticke bezpecnosti",
         "Zavedeni, udrzbovani a prubezne zlepsovani systemu minimalni KB.",
         True),
    ],
    "Organizacni opatreni": [
        ("§4",  "§ 4 Pozadavky na vrcholne vedeni",
         "Zapojeni a odpovednost vrcholneho vedeni, jmenovani odpovenych osob.",
         True),
        ("§5",  "§ 5 Bezpecnost lidskych zdroju",
         "Vzdelavani, povedomost a bezpecnostni opatreni vuci zamestnancum.",
         True),
        ("§6",  "§ 6 Rizeni kontinuity cinnosti",
         "Zajisteni nepretrzitosti kritickych procesu, zalohovani a obnova.",
         True),
    ],
    "Technicka opatreni": [
        ("§7",  "§ 7 Rizeni pristupu",
         "Principy nejmensich opravneni, fizicka a logicka kontrola pristupu.",
         True),
        ("§8",  "§ 8 Rizeni identit a jejich opravneni",
         "Sprava uctu, MFA, zivotni cyklus identit a auditni trail.",
         True),
        ("§9",  "§ 9 Detekce a zaznamovani kybernetickych bezpecnostnich udalosti",
         "Monitoring, centralni logging, korelace a detekce anomalii.",
         True),
        ("§10", "§ 10 Reseni kybernetickych bezpecnostnich incidentu",
         "Identifikace, zvladani, eskalace a hlaseni incidentu NUKIB.",
         True),
        ("§11", "§ 11 Bezpecnost komunikacnich siti",
         "Sitova segmentace, ochrana perimetru, sifrovana komunikace.",
         True),
        ("§12", "§ 12 Aplikacni bezpecnost",
         "Bezpecne nastaveni aplikaci, autentizace, sprava opravneni.",
         True),
        ("§13", "§ 13 Kryptograficke algoritmy",
         "Pouzivani schvalenych kryptografickych algoritmu a sprava klicu.",
         True),
    ],
    "Priloha - Hodnoceni incidentu": [
        ("§14", "§ 14 Stanoveni vyznamnosti dopadu kybernetickeho bezpecnostniho incidentu",
         "Metodika klasifikace zavaznosti incidentu a kriterium pro hlaseni.",
         True),
    ],
}

# ---------------------------------------------------------------------------
# POLITIKY A NASTROJE (AppliedControl / Policy)
# ---------------------------------------------------------------------------
POLICIES = [
    # Organizacni politiky
    ("POL-01", "Politika spravy aktiv",
     "Pravidla pro evidenci, klasifikaci a hodnoceni aktiv; implementovano v Snipe-IT."),
    ("POL-02", "Politika rizeni rizik",
     "Metodika identifikace, hodnoceni a osetreni rizik v CISO Assistant."),
    ("POL-03", "Politika bezpecnosti hesel",
     "Min. 12 znaku pro uzivatele, 17 pro adminy; rotace 90 dni; MFA povinne pro privilegovane ucty."),
    ("POL-04", "Plan skoleni a osvety",
     "Vstupni skoleni novacku a rocni opakovani; implementovano pres Moodle a Gophish."),
    ("POL-05", "Plan kontinuity a obnovy (BRP)",
     "Postup obnovy po incidentu, RTO <= 4 h, RPO <= 24 h; podpirany Restic zalohy."),
    ("POL-06", "Metodika hlaseni incidentu",
     "Kanal hlaseni (helpdesk), eskalacni matice, sablona hlaseni NUKIB."),
    ("POL-07", "Politika kryptografie",
     "Pozadavky na algoritmy: AES-256 (data), TLS 1.2+ (komunikace), Ed25519 (SSH)."),
    # Technicke nastroje
    ("TOOL-01", "Snipe-IT - Evidence a sprava aktiv",
     "Inventarizace HW/SW aktiv, sledovani zivotniho cyklu, export pro audity."),
    ("TOOL-02", "Keycloak - Centralni sprava identit (IdP)",
     "SSO, TOTP/MFA, RBAC, SAML 2.0 (Snipe-IT), OIDC (CISO Assistant)."),
    ("TOOL-03", "Restic - Sifrovane automaticke zalohovani",
     "AES-256, denni zalohy, 30denni retence, test obnovy 1x mesicne."),
    ("TOOL-04", "Wazuh - SIEM a detekce hrozeb",
     "Centralni sber logu, korelace udalosti, detekce anomalii, alerting."),
    ("TOOL-05", "Suricata - Detekce sitovych anomalii (IDS/IPS)",
     "Analyza sitoveho provozu, detekce utoku a nalezitosti."),
    ("TOOL-06", "OPNsense - Firewall a sitova segmentace",
     "Stavovy firewall, VLAN segmentace, ACL pravidla, VPN."),
    ("TOOL-07", "Caddy - TLS reverzni proxy",
     "Automaticka TLS (interna CA), HTTP->HTTPS redirect, ochrana webovych sluzeb."),
    ("TOOL-08", "CISO Assistant - Sprava shody a incidentu",
     "GRC platforma: hodnoceni shody s vyhlaskou, evidence incidentu, rizeni rizik."),
]

# Mapovani: ref_id pozadavku -> [seznam nazvu politik/nastroju]
# §1 a §2 jsou non-assessable, neni treba je mapovat
POLICY_MAPPING = {
    "§3":  ["CISO Assistant - Sprava shody a incidentu",
            "Snipe-IT - Evidence a sprava aktiv"],
    "§4":  ["CISO Assistant - Sprava shody a incidentu",
            "Politika spravy aktiv"],
    "§5":  ["Plan skoleni a osvety"],
    "§6":  ["Restic - Sifrovane automaticke zalohovani",
            "Plan kontinuity a obnovy (BRP)"],
    "§7":  ["Keycloak - Centralni sprava identit (IdP)",
            "Politika bezpecnosti hesel"],
    "§8":  ["Keycloak - Centralni sprava identit (IdP)",
            "Politika bezpecnosti hesel"],
    "§9":  ["Wazuh - SIEM a detekce hrozeb",
            "Suricata - Detekce sitovych anomalii (IDS/IPS)"],
    "§10": ["Wazuh - SIEM a detekce hrozeb",
            "Metodika hlaseni incidentu",
            "CISO Assistant - Sprava shody a incidentu"],
    "§11": ["OPNsense - Firewall a sitova segmentace",
            "Caddy - TLS reverzni proxy",
            "Suricata - Detekce sitovych anomalii (IDS/IPS)"],
    "§12": ["Caddy - TLS reverzni proxy",
            "Keycloak - Centralni sprava identit (IdP)"],
    "§13": ["Caddy - TLS reverzni proxy",
            "Restic - Sifrovane automaticke zalohovani",
            "Politika kryptografie"],
    "§14": ["Metodika hlaseni incidentu",
            "CISO Assistant - Sprava shody a incidentu"],
}

# ---------------------------------------------------------------------------
# IMPLEMENTACNI UKOLY
# ---------------------------------------------------------------------------
IMPLEMENTATION_TASKS = [
    ("§3 Governance: CISO Assistant",
     "Nasadit CISO Assistant pro rizeni shody, hodnoceni rizik a evidenci incidentu.",
     "TASK-CISO"),
    ("§3 Evidence aktiv: Snipe-IT",
     "Nasadit a nakonfigurovat Snipe-IT pro inventarizaci HW/SW aktiv.",
     "TASK-SNIPE-IT"),
    ("§4 Vrcholne vedeni: Jmenovani roli a odpovednosti",
     "Jmenovat osobu poverenou KB, definovat odpovednosti a reporting.",
     "TASK-ROLES"),
    ("§5 Skoleni zamestnancu: Moodle + Gophish",
     "Nasadit LMS Moodle a phishing simulator Gophish pro bezpecnostni osvetu.",
     "TASK-TRAINING"),
    ("§6 Kontinuita: Restic (sifrovane zalohovani)",
     "Nasadit Restic s automatickymi dennimi zalohami a testem obnovy.",
     "TASK-BACKUP"),
    ("§7/§8 Pristup a identity: Keycloak (IdP + MFA)",
     "Nasadit Keycloak jako centralni IdP se SSO, TOTP/MFA a RBAC.",
     "TASK-KEYCLOAK"),
    ("§9 Detekce: Wazuh SIEM + Suricata IDS",
     "Nasadit Wazuh pro centralni logging a Suricata pro sitovou detekci.",
     "TASK-WAZUH"),
    ("§11 Site: OPNsense (Firewall + VLAN)",
     "Nasadit OPNsense se segmentaci siti, ACL pravidly a VPN.",
     "TASK-OPNSENSE"),
]

# ---------------------------------------------------------------------------
# DATA ORGANIZACE
# ---------------------------------------------------------------------------
ORG_NAME = "Energo-Sluzby s.r.o."
ASSETS = [
    ("SRV-DB-01",     "Databazovy server s daty o spotrebe (Primarni aktivum)."),
    ("SRV-BACKUP-01", "Zalohovaci server umisteny v oddelenem segmentu."),
    ("SRV-APP-01",    "Aplikacni server pro webove sluzby (Caddy, Keycloak, Snipe-IT)."),
]


# ---------------------------------------------------------------------------
# SEED
# ---------------------------------------------------------------------------
@transaction.atomic
def seed():
    print("=" * 60)
    print("  CISO ASSISTANT - SEED SCRIPT (Django ORM)")
    print("=" * 60)

    # 1. Folders
    global_folder = Folder.objects.filter(content_type="GLOBAL").first()
    if not global_folder:
        global_folder, _ = Folder.objects.get_or_create(name="Global")

    org_folder, _ = Folder.objects.get_or_create(
        name=ORG_NAME,
        defaults={"parent_folder": global_folder}
    )
    project_folder, _ = Folder.objects.get_or_create(
        name="Implementace Vyhlasky 410-2025 Sb.",
        defaults={"parent_folder": org_folder}
    )
    print(f"   OK Slozky: {global_folder.name} > {org_folder.name} > {project_folder.name}")

    # 2. Framework – pri existenci resetuj uzly a CA (nova struktura)
    FW_URN = f"urn:intuitem:risk:framework:{FW_REF_ID}"

    fw, created = Framework.objects.get_or_create(
        ref_id=FW_REF_ID,
        defaults={
            "name": FW_NAME,
            "description": FW_DESC,
            "folder": global_folder,
            "annotation": "Legislativa CR - ZKB c. 264/2025 Sb.",
            "urn": FW_URN,
        }
    )
    if not created:
        fw.name = FW_NAME
        fw.description = FW_DESC
        fw.urn = FW_URN
        fw.save()
        old_nodes = RequirementNode.objects.filter(framework=fw).count()
        RequirementNode.objects.filter(framework=fw).delete()
        ComplianceAssessment.objects.filter(framework=fw).delete()
        print(f"   OK Framework nalezen, resetovano {old_nodes} uzlu a stary CA.")
    else:
        print(f"   OK Framework vytvoren (ID: {fw.id})")

    # 3. Requirement nodes – skupiny + §§
    print("Pozadavky frameworku...")
    node_refs = {}  # ref_id -> RequirementNode

    NODE_URN_PREFIX = f"urn:intuitem:risk:req_node:{FW_REF_ID}"

    for group_name, requirements in FW_STRUCTURE.items():
        group_ref = group_name[:3].upper()
        group_urn = f"{NODE_URN_PREFIX}:{group_ref}"
        group_node = RequirementNode.objects.create(
            framework=fw,
            folder=global_folder,
            name=group_name,
            ref_id=group_ref,
            urn=group_urn,
            assessable=False,
            description=group_name,
            annotation=""
        )
        print(f"   OK Skupina: {group_name}")

        for ref_id, req_name, req_desc, assessable in requirements:
            node = RequirementNode.objects.create(
                framework=fw,
                folder=global_folder,
                name=req_name,
                ref_id=ref_id,
                urn=f"{NODE_URN_PREFIX}:{ref_id}",
                parent_urn=group_urn,
                assessable=assessable,
                description=req_desc,
                annotation=""
            )
            node_refs[ref_id] = node
            flag = "" if assessable else " (informativni)"
            print(f"      - {ref_id}: {req_name}{flag}")

    # 4. Implementacni ukoly
    print("Implementacni ukoly...")
    for name, desc, ref_id in IMPLEMENTATION_TASKS:
        TaskTemplate.objects.get_or_create(
            name=name,
            folder=project_folder,
            defaults={"description": desc, "ref_id": ref_id, "enabled": True}
        )
    print("   OK Ukoly vytvoreny.")

    # 5. Organizacni data
    print(f"Organizace: {ORG_NAME}...")
    for name, desc in ASSETS:
        Asset.objects.get_or_create(
            name=name,
            folder=org_folder,
            defaults={"description": desc}
        )

    policy_objs = {}
    for code, name, desc in POLICIES:
        p, _ = Policy.objects.get_or_create(
            name=name,
            folder=org_folder,
            defaults={"description": desc, "ref_id": code}
        )
        policy_objs[name] = p

    OrganisationObjective.objects.get_or_create(
        name="Dostupnost distribuce dat",
        folder=org_folder,
        defaults={"description": "Max. vypadek regulovane sluzby 4 hodiny (RTO <= 4 h)."}
    )

    perimeter, _ = Perimeter.objects.get_or_create(
        name="Distribuce dat o spotrebe",
        folder=org_folder,
        defaults={"description": "Primarni oblast regulovane sluzby – distribuce energetickych dat."}
    )
    print("   OK Organizacni data vytvorena.")

    # 6. Compliance assessment
    print("Compliance assessment...")
    ca = ComplianceAssessment.objects.create(
        name="Audit shody - Vyhlaska 410/2025 Sb.",
        framework=fw,
        folder=org_folder,
        perimeter=perimeter,
        status="in_progress",
        version="1.0"
    )
    ca.create_requirement_assessments()
    print(f"   OK Compliance assessment vytvoren (ID: {ca.id})")

    # 7. Mapovani nastroju/politik na pozadavky
    print("Mapovani nastroju na pozadavky...")
    mapped_total = 0

    req_assessments = RequirementAssessment.objects.filter(
        compliance_assessment=ca
    ).select_related('requirement')

    for ra in req_assessments:
        req_ref = ra.requirement.ref_id if ra.requirement else ""
        controls_for_req = POLICY_MAPPING.get(req_ref, [])

        added = []
        for control_name in controls_for_req:
            policy = policy_objs.get(control_name)
            if not policy:
                print(f"      VAROVANI: Nenalezena politika '{control_name}'")
                continue
            if not ra.applied_controls.filter(id=policy.id).exists():
                ra.applied_controls.add(policy)
                added.append(control_name)
                mapped_total += 1

        if added:
            ra.status = "partially_compliant"
            ra.save()
            print(f"      {req_ref}: {', '.join(added)}")

    print(f"   OK Celkem pridano {mapped_total} mapovani.")

    print("\n" + "=" * 60)
    print("  OK HOTOVO!")
    print(f"  Framework:  {fw.name}")
    print(f"  Uzly:       {RequirementNode.objects.filter(framework=fw).count()} pozadavku")
    print(f"  Politiky:   {len(policy_objs)} politik/nastroju")
    print(f"  CA:         {ca.name}")
    print(f"  Mapovani:   {mapped_total} prirazeni")
    print("=" * 60)


if __name__ == "__main__":
    try:
        seed()
    except Exception as e:
        print(f"CHYBA: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
