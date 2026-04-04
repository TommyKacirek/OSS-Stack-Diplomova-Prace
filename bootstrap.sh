#!/bin/bash
# bootstrap.sh
# Jednorázová příprava Ubuntu VM pro nasazení OSS Cybersecurity Lab.
# Skript nainstaluje Docker Engine a Ansible, poté přidá aktuálního uživatele
# do skupiny docker.
#
# Použití:
#   chmod +x bootstrap.sh
#   ./bootstrap.sh
#   newgrp docker   # nebo se odhlásit a znovu přihlásit
#
# Po dokončení pokračuj podle kroků vypsaných na konci výstupu.

set -e   # Ukončí skript při první chybě

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'   # Reset barvy

echo -e "${GREEN}[+] Aktualizace systemu a instalace zakladnich balicku...${NC}"
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg python3 python3-pip python3-venv git htop

# Instalace Docker Engine (přes oficiální APT repozitář od Docker Inc.)
if ! command -v docker &> /dev/null; then
    echo -e "${GREEN}[+] Instalace Docker Engine...${NC}"
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# Instalace Ansible (přes oficiální PPA od Ansible komunity)
if ! command -v ansible &> /dev/null; then
    echo -e "${GREEN}[+] Instalace Ansible...${NC}"
    sudo apt-get install -y software-properties-common
    sudo add-apt-repository --yes --update ppa:ansible/ansible
    sudo apt-get install -y ansible
fi

# Přidá aktuálního uživatele do skupiny docker, aby mohl spouštět Docker příkazy bez sudo
sudo usermod -aG docker $USER

echo -e "${GREEN}[+] Bootstrap hotov!${NC}"
echo -e "${YELLOW}[!] Proved tyto kroky pred spustenim playbooku:${NC}"
echo -e "    1. Odhlas se a znovu prihlas (nebo: newgrp docker)"
echo -e "    2. Zkopiruj inventory/group_vars/all/vault.yml.example -> vault.yml"
echo -e "    3. Vyplň hesla ve vault.yml"
echo -e "    4. ansible-playbook playbooks/deploy.yml"
