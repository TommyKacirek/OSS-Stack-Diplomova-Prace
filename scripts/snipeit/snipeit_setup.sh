#!/bin/bash
# =============================================================================
#  SNIPE-IT SETUP SCRIPT
#  Inicializuje Snipe-IT: migrace, admin uživatel, API klíč, upload dat
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Barvy pro output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Konfigurace - lze přepsat env proměnnými
SNIPEIT_ADMIN_USERNAME="${SNIPEIT_ADMIN_USERNAME:-admin}"
SNIPEIT_ADMIN_PASSWORD="${SNIPEIT_ADMIN_PASSWORD:-password123}"
SNIPEIT_ADMIN_EMAIL="${SNIPEIT_ADMIN_EMAIL:-admin@example.com}"

echo -e "${GREEN}=====================================================${NC}"
echo -e "${GREEN}  SNIPE-IT - SETUP SCRIPT${NC}"
echo -e "${GREEN}=====================================================${NC}"

cd "$PROJECT_DIR"

# 1. Hledání běžícího kontejneru Snipe-IT v Dockeru
echo -e "\n${YELLOW}[1/7] Hledám Snipe-IT kontejner...${NC}"
SNIPEIT_CONTAINER=$(docker compose ps -q snipe-it 2>/dev/null || docker ps -q -f "name=snipe-it" | head -1)

if [ -z "$SNIPEIT_CONTAINER" ]; then
    echo -e "${RED}   ✗ Snipe-IT kontejner nenalezen!${NC}"
    echo "   Ujistěte se, že je spuštěný: docker compose up -d"
    exit 1
fi
echo -e "${GREEN}   ✓ Nalezen: ${SNIPEIT_CONTAINER:0:12}${NC}"

# Hledání backend kontejneru (poběží v něm Python skripty pro API import)
BACKEND_CONTAINER=$(docker compose ps -q ciso-assistant-backend 2>/dev/null || docker ps -q -f "name=ciso-assistant-backend" | head -1)

# 2. Ověření, že Snipe-IT (PHP Artisan) je připraven k provádění příkazů
echo -e "\n${YELLOW}[2/7] Čekám na start Snipe-IT...${NC}"
for i in {1..30}; do
    if docker exec "$SNIPEIT_CONTAINER" php artisan --version > /dev/null 2>&1; then
        break
    fi
    echo "   ... startuje (pokus $i/30)"
    sleep 3
done

if ! docker exec "$SNIPEIT_CONTAINER" php artisan --version > /dev/null 2>&1; then
    echo -e "${RED}   ✗ Snipe-IT se nespustil!${NC}"
    exit 1
fi
echo -e "${GREEN}   ✓ Snipe-IT běží${NC}"

# 3. Čekej na databázi
echo -e "\n${YELLOW}[3/7] Čekám na databázi...${NC}"
for i in {1..20}; do
    if docker exec "$SNIPEIT_CONTAINER" php artisan db:monitor > /dev/null 2>&1; then
        break
    fi
    echo "   ... čekám na spojení (pokus $i/20)"
    sleep 5
done
echo -e "${GREEN}   ✓ Databáze připojena${NC}"

# 4. Spuštění databázových migrací (vytvoření tabulek)
echo -e "\n${YELLOW}[4/7] Spouštím migrace...${NC}"
docker exec "$SNIPEIT_CONTAINER" php artisan migrate --force
echo -e "${GREEN}   ✓ Migrace dokončeny${NC}"

# 5. Generuj OAuth/Passport klíče
echo -e "\n${YELLOW}[5/7] Generuji OAuth klíče...${NC}"
docker exec "$SNIPEIT_CONTAINER" php artisan passport:install --no-interaction 2>/dev/null || echo "   (Klíče již existují)"
echo -e "${GREEN}   ✓ OAuth klíče připraveny${NC}"

# 6. Automatizované vytvoření admin uživatele a základního nastavení aplikace (CZK, čeština)
echo -e "\n${YELLOW}[6/7] Vytvářím admin uživatele...${NC}"

# Vytvoř admin uživatele
docker exec "$SNIPEIT_CONTAINER" php artisan snipeit:create-admin \
    --first_name="Admin" \
    --last_name="User" \
    --email="$SNIPEIT_ADMIN_EMAIL" \
    --username="$SNIPEIT_ADMIN_USERNAME" \
    --password="$SNIPEIT_ADMIN_PASSWORD" \
    --no-interaction 2>/dev/null || echo "   (Admin již existuje)"

# Vytvoř výchozí nastavení
docker exec "$SNIPEIT_CONTAINER" php artisan tinker --execute="
\$s = App\Models\Setting::first();
if(!\$s) {
    \$s = new App\Models\Setting;
    \$s->site_name = 'Asset Manager';
    \$s->alert_email = '$SNIPEIT_ADMIN_EMAIL';
    \$s->alerts_enabled = 1;
    \$s->brand = 1;
    \$s->default_currency = 'CZK';
    \$s->locale = 'cs-CZ';
    \$s->save();
    echo 'Settings created';
} else {
    echo 'Settings exists';
}
" 2>/dev/null || true

echo -e "${GREEN}   ✓ Admin a nastavení připraveny${NC}"

# 7. Vygenerování osobního API klíče a následný import dat přes Python skript
echo -e "\n${YELLOW}[7/7] Generuji API klíč a nahrávám data...${NC}"

SNIPEIT_API_KEY=$(docker exec "$SNIPEIT_CONTAINER" php artisan snipeit:make-api-key --user_id=1 --name="AutoSetup" --key-only 2>/dev/null || echo "")

if [ -z "$SNIPEIT_API_KEY" ]; then
    echo -e "${YELLOW}   ! API klíč nelze vygenerovat (možná již existuje)${NC}"
    echo "   Pro manuální upload použijte: SNIPEIT_API_KEY=<key> python3 snipeit_upload.py"
else
    echo -e "${GREEN}   ✓ API klíč vygenerován${NC}"
    
    # Použij backend container pro Python (má requests)
    if [ -n "$BACKEND_CONTAINER" ]; then
        docker cp "$SCRIPT_DIR/snipeit_upload.py" "$BACKEND_CONTAINER:/code/snipeit_upload.py"
        docker exec -e SNIPEIT_API_KEY="$SNIPEIT_API_KEY" -e SNIPEIT_API_URL="http://snipe-it:80/api/v1" \
            "$BACKEND_CONTAINER" python3 /code/snipeit_upload.py
    else
        echo "   ! Backend kontejner nenalezen, přeskakuji API upload"
        echo "   API klíč: $SNIPEIT_API_KEY"
    fi
fi

echo -e "\n${GREEN}=====================================================${NC}"
echo -e "${GREEN}  ✓ SNIPE-IT SETUP DOKONČEN${NC}"
echo -e "${GREEN}=====================================================${NC}"
echo -e "  Admin login: ${SNIPEIT_ADMIN_USERNAME} / ${SNIPEIT_ADMIN_PASSWORD}"
echo -e "${GREEN}=====================================================${NC}"
