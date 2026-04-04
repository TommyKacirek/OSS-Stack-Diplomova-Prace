# OSS Cybersecurity Lab

Vítejte v repozitáři OSS Cybersecurity Lab. Tento projekt slouží jako plně automatizovaný, lokální stack pro testování a výuku kybernetické bezpečnosti. Celé prostředí běží v Dockeru a jeho nasazení je řízeno pomocí Ansible.

## Architektura

Stack obsahuje následující předkonfigurované služby:

| Služba | URL | Popis |
|---|---|---|
| **Caddy** | — | Reverse proxy, která se automaticky stará o lokální HTTPS certifikáty a směrování provozu. |
| **Keycloak** | `https://auth.oss.local` | Centrální Identity Provider pro správu uživatelů a SSO (přes SAML/OIDC). |
| **Snipe-IT** | `https://assets.oss.local` | Systém pro evidenci a správu IT aktiv (Asset Management). |
| **CISO Assistant** | `https://ciso.oss.local` | GRC nástroj pro řízení kybernetické bezpečnosti (obsahuje seeder pro Vyhlášku 410/2025). |
| **Vaultwarden** | `https://pass.oss.local` | Bezpečný správce hesel (odlehčená alternativa k Bitwardenu). |
| **Landing page** | `https://oss.local` | Jednoduchý rozcestník s odkazy na všechny běžící služby. |
| **Restic** | — | Nástroj pro automatizované, šifrované zálohování celého labu. |

## Požadavky

- Virtuální stroj s Ubuntu 22.04 LTS (min. **4 GB RAM**, **30 GB disk**).
- Přístup k internetu pro stahování Docker obrazů během instalace.
- Klientský počítač (Windows, macOS nebo Linux) s webovým prohlížečem pro přístup k rozhraní.

## Rychlý start

### 1. Příprava Git (na čistém Linuxu)

Pokud instalujete na čistý systém, nejprve nainstalujte Git:

```bash
sudo apt update && sudo apt install -y git
```

### 2. Klonování repozitáře

```bash
git clone https://github.com/TommyKacirek/OSS-Stack-Diplomova-Prace.git
cd ~/cybersecurity-lab
```

### 3. Příprava serveru (Bootstrap)

Tento skript nainstaluje Docker, Ansible a všechny potřebné systémové závislosti:

```bash
chmod +x bootstrap.sh
./bootstrap.sh
newgrp docker   # Aplikuje členství uživatele ve skupině docker
```

### 4. Konfigurace prostředí (vars.yml)

Před spuštěním instalace si můžete přizpůsobit domény a údaje hlavního uživatele v souboru `inventory/group_vars/all/vars.yml`. Pokud ponecháte výchozí hodnoty, lab poběží na doméně `oss.local`.

```bash
nano inventory/group_vars/all/vars.yml
```

Zde můžete změnit zejména údaje hlavního uživatele laboratoře:
```yaml
keycloak_lab_user_name: "vase_jmeno"
keycloak_lab_user_first_name: "Vaše"
keycloak_lab_user_last_name: "Jméno"
keycloak_lab_user_email: "email@oss.local"
```

### 5. Nastavení hesel (Ansible Vault)

Zkopírujte šablonu a vyplňte vlastní hesla. Soubor obsahuje nejen heslo pro administrátora Keycloaku, ale také hesla k databázím a šifrovací klíč pro zálohy (`restic_password`).

```bash
cp inventory/group_vars/all/vault.yml.example inventory/group_vars/all/vault.yml
nano inventory/group_vars/all/vault.yml
```

*(Pro vygenerování opravdu silných a náhodných hesel si můžete pomoci příkazem jako `pwgen -s 32 1` nebo `openssl rand -base64 24`.)*


### 6. Spuštění instalace

```bash
ansible-playbook playbooks/deploy.yml
```

*První nasazení může trvat 5–10 minut, protože server musí stáhnout všechny potřebné Docker obrazy.*

---

## Konfigurace klientského počítače

Aby vám ve vašem prohlížeči fungovaly lokální domény a zelený zámeček u HTTPS, je potřeba provést dva kroky na stroji, ze kterého se budete do labu připojovat.

### A. Přidání záznamů do DNS (soubor hosts)

Nejprve zjistěte IP adresu vašeho Ubuntu serveru (příkaz `ip a`). Následně upravte soubor `hosts` na vašem počítači:
* **macOS/Linux:** `sudo nano /etc/hosts`
* **Windows:** Otevřete Poznámkový blok jako správce a upravte `C:\Windows\System32\drivers\etc\hosts`

Přidejte následující řádek (místo `192.168.x.x` doplňte reálnou IP adresu serveru):

```
192.168.x.x  oss.local auth.oss.local assets.oss.local ciso.oss.local pass.oss.local
```

### B. Import kořenového certifikátu Caddy (Root CA)

Aby prohlížeč nehlásil chybu certifikátu, musíte si stáhnout a začlenit lokální certifikační autoritu Caddy.

```bash
# Stáhněte certifikát ze serveru (např. pomocí scp)
scp user@192.168.x.x:/opt/lab/caddy/data/caddy/pki/authorities/local/root.crt ~/Desktop/caddy-root.crt
```

* **macOS:** Přetáhněte stažený soubor `caddy-root.crt` do aplikace **Keychain Access** (sekce System). Dvojklikem jej otevřete, rozbalte "Trust" a nastavte "Always Trust". Potvrďte heslem.
* **Windows:** Dvakrát klikněte na soubor `caddy-root.crt` -> Nainstalovat certifikát. Zvolte "Místní počítač" a certifikát umístěte do úložiště **Důvěryhodné kořenové certifikační autority** (Trusted Root Certification Authorities).
* **Linux/Firefox:** Naimportujte certifikát přímo ve správci certifikátů vašeho webového prohlížeče.

---

## První přihlášení do služeb

Díky nasazenému SSO přes Keycloak máte u většiny služeb přístup vyřešený z jednoho místa.

* **Keycloak (`https://auth.oss.local`):** Do Administration Console se přihlašujete jako uživatel `admin`. Heslo odpovídá hodnotě `keycloak_admin_password`, kterou jste zadali do `vault.yml`.
* **Snipe-IT (`https://assets.oss.local`) & CISO Assistant (`https://ciso.oss.local`):** Pro tyto služby je již nastaveno Single Sign-On (SSO). Přihlásíte se automaticky stejným účtem z Keycloak realmu.
* **Vaultwarden (`https://pass.oss.local`):** *Upozornění:* Tato služba z bezpečnostních důvodů nepodporuje automatický SSO provisioning. Při prvním spuštění si musíte přímo na stránce manuálně vytvořit účet (a zapamatovat si svůj Master Password).

---

## Zálohování a obnova dat

Vaše data jsou chráněna. Zálohy celého labu řeší automaticky nástroj Restic každý den ve 02:00 v noci. Konfigurace uchovává historii po dobu 7 dnů. Zálohovací repozitář se standardně nachází v `/home/USER/cybersecurity-backups`.

Pokud potřebujete se zálohami pracovat manuálně, můžete použít tyto příkazy přímo na serveru:

```bash
./run-backup.sh                     # Okamžité ruční spuštění zálohy
cat /var/log/restic-backup.json     # Zobrazení logů ze zálohovacích operací
restic snapshots                    # Výpis všech aktuálně uložených snapshotů
```

## Řešení problémů

Pokud některá služba nestartuje nebo se chová zvláštně, doporučujeme nahlédnout přímo do logů Dockeru:

```bash
docker ps -a                        # Zobrazí stav a uptime všech kontejnerů
docker logs caddy                   # Logy reverzní proxy
docker logs keycloak                # Logy Keycloak (při startu čeká na DB ~60s)
docker logs snipeit                 # Logy Snipe-IT
docker logs cisobackend             # Logy backendu CISO Assistanta
```