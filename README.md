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
| **Vaultwarden** | `https://pass.oss.local` | Bezpečný správce hesel (odlehčená alternativa k Bitwardenu). |
| **Landing page** | `https://oss.local` | Jednoduchý rozcestník s odkazy na všechny běžící služby. |
| **Restic** | — | Nástroj pro automatizované, šifrované zálohování celého labu. |

## Požadavky

- **Virtuální stroj:** Ubuntu 22.04 LTS (doporučeno min. **4 GB RAM**, **50 GB disk**).
- **Konektivita:** Přístup k internetu (pro stažení Docker obrazů a závislostí).
- **Klient:** Prohlížeč na libovolném OS (Windows, macOS, Linux) s přístupem do sítě VM.

---

## Rychlý start (Instalace)

### 1. Příprava systému
Pokud instalujete na čistý Linux, nejprve nainstalujte Git:
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
Kopírujte šablonu a vyplňte vlastní silná hesla pro databáze a admin účty.
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
Vytvořte směrování pro IP adresu vašeho serveru (zjistíte příkazem `ip a`).
- **macOS/Linux:** `sudo nano /etc/hosts`
- **Windows:** Upravte jako správce `C:\Windows\System32\drivers\etc\hosts`

Přidejte řádek:
```text
192.168.x.x  oss.local auth.oss.local assets.oss.local ciso.oss.local pass.oss.local
```

### B. Import Trust certifikátu (Caddy Root CA)
Aby prohlížeč hlásil "Zabezpečeno", stáhněte si ze serveru kořenový certifikát:
```bash
scp user@192.168.x.x:/opt/lab/caddy/data/caddy/pki/authorities/local/root.crt ~/Desktop/caddy-root.crt
```
- **macOS:** Importujte do **Keychain Access** (System) a nastavte "Always Trust".
- **Windows:** Importujte do úložiště **Důvěryhodné kořenové certifikační autority**.

---

## První přihlášení a SSO

Většina služeb je integrována přes **Single Sign-On (SSO)**.

- **Keycloak (`auth.oss.local`):** Správa celého identity managementu. Login jako `admin` s heslem z `vault.yml`.
- **Snipe-IT & CISO Assistant:** Na přihlašovací stránce zvolte možnost **"Log in with SAML"** (nebo OIDC). Budete přesměrováni na Keycloak a po zadání údajů administrátora se automaticky přihlásíte s plnými právy.
- **Vaultwarden:** Z bezpečnostních důvodů nepodporuje automatický provisioning. Při prvním přístupu si **manuálně vytvořte účet** přímo v aplikaci.

---

## Správa a údržba

### Zálohování (Restic)
Zálohy probíhají automaticky každý den v 02:00 do adresáře `/home/USER/cybersecurity-backups`.
```bash
./run-backup.sh          # Ruční záloha
restic snapshots         # Výpis snapshotů
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
