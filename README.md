# OSS Cybersecurity Lab

Vítejte v repozitáři **OSS Cybersecurity Lab**. Tento projekt slouží jako plně automatizovaný, lokální stack pro testování, výuku a demonstraci nástrojů kybernetické bezpečnosti. Celé prostředí běží v kontejnerech Docker a jeho nasazení je plně řízeno pomocí Ansible.

## Architektura

Stack obsahuje následující předkonfigurované služby integrované do jednoho celku:

| Služba | URL | Popis |
|---|---|---|
| **Caddy** | — | Reverse proxy, která automaticky spravuje lokální HTTPS certifikáty a směrování. |
| **Keycloak** | `https://auth.oss.local` | Centrální Identity Provider (IdP) pro správu uživatelů a SSO (přes SAML/OIDC). |
| **Snipe-IT** | `https://assets.oss.local` | Systém pro evidenci a správu IT aktiv (Asset Management). |
| **CISO Assistant** | `https://ciso.oss.local` | GRC nástroj pro řízení kyberbezpečnosti (vč. Vyhlášky 410/2025). |
| **Landing page** | `https://oss.local` | Jednoduchý rozcestník s odkazy na všechny běžící služby. |
| **Restic** | — | Nástroj pro automatizované, šifrované zálohování celého labu. |

## Požadavky

- **Server:** Ubuntu 22.04 LTS (doporučeno min. **6 GB RAM**, **50 GB disk**) — VM nebo WSL2.
- **Konektivita:** Přístup k internetu (pro stažení Docker obrazů a závislostí).
- **Klient:** Prohlížeč na libovolném OS (Windows, macOS, Linux) s přístupem do sítě serveru.

---

## Rychlý start (Instalace)

> [!NOTE]
> **Windows uživatelé:** Ansible nelze spustit nativně na Windows. Použijte jednu z těchto možností:
> - **WSL2 (doporučeno):** Nainstalujte WSL2 s Ubuntu 22.04 — `wsl --install -d Ubuntu-22.04` v PowerShellu jako správce, poté pokračujte kroky níže uvnitř WSL2 terminálu.
> - **Virtuální stroj:** VirtualBox nebo VMware s Ubuntu 22.04 LTS.

### 1. Příprava systému
Pokud instalujete na čistý Linux nebo WSL2, nejprve nainstalujte Git:
```bash
sudo apt update && sudo apt install -y git
```

### 2. Klonování repozitáře
```bash
git clone https://github.com/TommyKacirek/OSS-Stack-Diplomova-Prace.git
cd OSS-Stack-Diplomova-Prace
```

### 3. Příprava serveru (Bootstrap)
Tento skript automaticky nainstaluje Docker, Ansible a nastaví oprávnění:
```bash
chmod +x bootstrap.sh
./bootstrap.sh
newgrp docker
```

### 4. Konfigurace prostředí (vars.yml)
Zde můžete přizpůsobit domény a údaje o výchozím uživateli. Pokud ponecháte výchozí hodnoty, lab poběží na doméně `oss.local`.
```bash
nano inventory/group_vars/all/vars.yml
```
> [!TIP]
> **Doporučení:** Ponechte e-mail administrátora na `admin@oss.local`. Systém je navržen tak, aby při prvním přihlášení přes SSO automaticky spároval tento e-mail s právy Superusera v aplikaci CISO Assistant.

### 5. Nastavení hesel (Ansible Vault)
Kopírujte šablonu a vyplňte vlastní silná hesla pro databáze a admin účty. Poznámka: Příkaz cp je povinný i v případě, že ponecháváte výchozí hesla. Bez souboru vault.yml nasazení selže.
```bash
cp inventory/group_vars/all/vault.yml.example inventory/group_vars/all/vault.yml
nano inventory/group_vars/all/vault.yml
```
*(Tip: Pro vygenerování hesel použijte např. `openssl rand -base64 24`)*

> [!WARNING]
> Soubor `vault.yml` obsahuje citlivá data. Pro produkční nasazení nebo nahrávání do Gitu jej **vždy zašifrujte** pomocí příkazu `ansible-vault encrypt inventory/group_vars/all/vault.yml`. Pokud soubor zašifrujete, budete muset při spuštění instalace dodat parametr `--ask-vault-pass`.

### 6. Spuštění instalace
Samotný proces nasazení všech služeb spustíte příkazem:
```bash
ansible-playbook playbooks/deploy.yml
```
*První nasazení trvá 5–10 minut (závisí na rychlosti internetu pro stažení obrazů).*

---

## Konfigurace klientského počítače

Aby fungovaly lokální domény a HTTPS bezpečně, proveďte na svém počítači tyto kroky:

### A. Přidání záznamů do DNS (soubor hosts)
Zjistěte IP adresu serveru příkazem `ip a` (hledejte rozhraní `eth0` nebo `ens*`).

**macOS/Linux:**
```bash
sudo nano /etc/hosts
```

**Windows (Notepad jako správce):**
```
C:\Windows\System32\drivers\etc\hosts
```
Nebo rychle v PowerShellu jako správce:
```powershell
Add-Content C:\Windows\System32\drivers\etc\hosts "192.168.x.x  oss.local auth.oss.local assets.oss.local ciso.oss.local"
```

Přidejte řádek (nahraďte IP adresou vašeho serveru):
```text
192.168.x.x  oss.local auth.oss.local assets.oss.local ciso.oss.local
```

> [!NOTE]
> **WSL2 uživatelé:** IP adresu zjistíte příkazem `hostname -I` uvnitř WSL2. Hosts soubor upravte na straně Windows, ne v WSL2.

### B. Import Trust certifikátu (Caddy Root CA)
Aby prohlížeč hlásil "Zabezpečeno", stáhněte si ze serveru kořenový certifikát:

**macOS/Linux:**
```bash
scp user@192.168.x.x:/opt/lab/caddy/data/caddy/pki/authorities/local/root.crt ~/Desktop/caddy-root.crt
```
- **macOS:** Importujte do **Keychain Access** (System) a nastavte "Always Trust".
- **Linux:** `sudo cp caddy-root.crt /usr/local/share/ca-certificates/ && sudo update-ca-certificates`

**Windows (PowerShell jako správce):**
```powershell
scp user@192.168.x.x:/opt/lab/caddy/data/caddy/pki/authorities/local/root.crt $env:USERPROFILE\Desktop\caddy-root.crt
Import-Certificate -FilePath "$env:USERPROFILE\Desktop\caddy-root.crt" -CertStoreLocation Cert:\LocalMachine\Root
```
Nebo ručně: dvojklik na soubor → **Nainstalovat certifikát** → **Místní počítač** → **Důvěryhodné kořenové certifikační autority**.

> [!NOTE]
> **WSL2 uživatelé:** Certifikát importujte na straně Windows (výše), nikoliv uvnitř WSL2. Prohlížeč běží na Windows a používá Windows certificate store.

---

## První přihlášení a SSO

Většina služeb je integrována přes **Single Sign-On (SSO)**.

- **Keycloak (`auth.oss.local`):** Správa celého identity managementu. Login jako `admin` s heslem z `vault.yml`.
- **Snipe-IT & CISO Assistant:** Na přihlašovací stránce zvolte možnost **"Log in with SAML"** (nebo OIDC). Budete přesměrováni na Keycloak a přihlaste se jako admin s heslem z vault.yml (pole keycloak_admin_password).

---

## Struktura repozitáře

```
.
├── inventory/
│   ├── group_vars/
│   │   └── all/
│   │       ├── vars.yml
│   │       └── vault.yml.example
│   └── hosts
├── playbooks/
│   ├── ciso_only.yml
│   └── deploy.yml
├── roles/
│   ├── backup/
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── templates/
│   │       └── backup.sh.j2
│   ├── caddy/
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── templates/
│   │       ├── Caddyfile.j2
│   │       └── docker-compose.yml.j2
│   ├── ciso_assistant/
│   │   ├── files/
│   │   │   ├── apply_hotfixes.py
│   │   │   └── ciso_upload.py
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   ├── tasks/
│   │   │   ├── main.yml
│   │   │   └── post_deploy.yml
│   │   └── templates/
│   │       ├── docker-compose.yml.j2
│   │       ├── settings.py.j2
│   │       └── setup_oidc.py.j2
│   ├── common/
│   │   └── tasks/
│   │       └── main.yml
│   ├── keycloak/
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── templates/
│   │       ├── docker-compose.yml.j2
│   │       └── realm-export.json.j2
│   ├── landing/
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── templates/
│   │       └── index.html.j2
│   └── snipeit/
│       ├── files/
│       │   ├── configure_saml.php
│       │   ├── debug_sso_state.php
│       │   ├── fix_snipeit_saml.py
│       │   ├── force_saml_sql.php
│       │   ├── inject_saml.php
│       │   ├── saml_settings.json
│       │   ├── saml_settings_flat.txt
│       │   ├── setup_saml.php
│       │   ├── snipeit_demo_assets.py
│       │   ├── snipeit_energo_upload.py
│       │   └── snipeit_upload.py
│       ├── handlers/
│       │   └── main.yml
│       ├── tasks/
│       │   └── main.yml
│       └── templates/
│           ├── docker-compose.yml.j2
│           └── saml_settings_flat.txt.j2
├── scripts/
│   ├── ciso/
│   │   ├── apply_hotfixes.py
│   │   ├── ciso_seed.py
│   │   ├── ciso_setup.sh
│   │   ├── ciso_upload.py
│   │   └── patch_ciso_settings.py
│   └── snipeit/
│       ├── snipeit_demo_assets.py
│       ├── snipeit_setup.sh
│       └── snipeit_upload.py
├── .gitignore
├── README.md
├── ansible.cfg
├── bootstrap.sh
├── export_realm.sh
└── run-backup.sh
```

---

## Správa a údržba

### Zálohování (Restic)
Zálohy probíhají automaticky každý den v 02:00 do adresáře `/home/USER/cybersecurity-backups`. Zálohuje se obsah `/opt/lab`.
```bash
./run-backup.sh          # Ruční záloha

# Výpis snapshotů (repozitář patří rootovi, nutné sudo)
sudo RESTIC_REPOSITORY=~/cybersecurity-backups RESTIC_PASSWORD='heslo_z_vault.yml' restic snapshots

cat /var/log/restic-backup.json  # Logy
```

### Diagnostika (Logy)
Pokud některá služba nefunguje, podívejte se na výpis z kontejnerů:
```bash
docker ps -a                 # Stav všech služeb
docker logs caddy            # Problematika HTTPS a směrování
docker logs keycloak         # Problémy s přihlašováním
docker logs snipeit          # Diagnostika Asset Managementu
```

---
