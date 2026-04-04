#!/bin/bash
# =============================================================================
#  CISO ASSISTANT SETUP SCRIPT
#  Orchestruje hotfixy a API upload pro CISO Assistant
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Barvy pro output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================================${NC}"
echo -e "${GREEN}  CISO ASSISTANT - SETUP SCRIPT${NC}"
echo -e "${GREEN}=====================================================${NC}"

cd "$PROJECT_DIR"

# 1. Najdi backend container
echo -e "\n${YELLOW}[1/6] Hledám backend kontejner...${NC}"
BACKEND_CONTAINER=$(docker compose ps -q ciso-assistant-backend 2>/dev/null || docker ps -q -f "name=ciso-assistant-backend")

if [ -z "$BACKEND_CONTAINER" ]; then
    echo -e "${RED}   ✗ Backend kontejner nenalezen!${NC}"
    echo "   Ujistěte se, že je spuštěný: docker compose up -d"
    exit 1
fi
echo -e "${GREEN}   ✓ Nalezen: ${BACKEND_CONTAINER:0:12}${NC}"

# 2. Čekej na health check
echo -e "\n${YELLOW}[2/6] Čekám na health check backendu...${NC}"
HEALTH_STATUS=""
for i in {1..60}; do
    HEALTH_STATUS=$(docker inspect -f '{{.State.Health.Status}}' "$BACKEND_CONTAINER" 2>/dev/null || echo "unknown")
    if [ "$HEALTH_STATUS" == "healthy" ]; then
        break
    fi
    echo "   ... $HEALTH_STATUS (pokus $i/60)"
    sleep 5
done

if [ "$HEALTH_STATUS" != "healthy" ]; then
    echo -e "${RED}   ✗ Backend není healthy po 5 minutách!${NC}"
    exit 1
fi
echo -e "${GREEN}   ✓ Backend je healthy${NC}"

# 3. Aplikuj hotfixy na models.py
echo -e "\n${YELLOW}[3/6] Aplikuji hotfixy na models.py...${NC}"
docker cp "$SCRIPT_DIR/apply_hotfixes.py" "$BACKEND_CONTAINER:/code/apply_hotfixes.py"
docker exec "$BACKEND_CONTAINER" python3 /code/apply_hotfixes.py

# 4. Aplikuj patch na settings.py
echo -e "\n${YELLOW}[4/6] Aplikuji patch na settings.py...${NC}"
docker cp "$SCRIPT_DIR/patch_ciso_settings.py" "$BACKEND_CONTAINER:/code/patch_ciso_settings.py"
docker exec "$BACKEND_CONTAINER" python3 /code/patch_ciso_settings.py

# 5. Restartuj backend
echo -e "\n${YELLOW}[5/6] Restartuji backend...${NC}"
docker restart "$BACKEND_CONTAINER"

# Čekej na restart
echo "   ... čekám na restart..."
sleep 10

for i in {1..30}; do
    HEALTH_STATUS=$(docker inspect -f '{{.State.Health.Status}}' "$BACKEND_CONTAINER" 2>/dev/null || echo "unknown")
    if [ "$HEALTH_STATUS" == "healthy" ]; then
        break
    fi
    sleep 3
done

if [ "$HEALTH_STATUS" != "healthy" ]; then
    echo -e "${RED}   ✗ Backend se nerestartoval správně!${NC}"
    exit 1
fi
echo -e "${GREEN}   ✓ Backend restartován${NC}"

# 6. Nahraj data přes API
echo -e "\n${YELLOW}[6/6] Nahrávám data přes API...${NC}"
docker cp "$SCRIPT_DIR/ciso_upload.py" "$BACKEND_CONTAINER:/code/ciso_upload.py"

# Instaluj requests pokud chybí
docker exec "$BACKEND_CONTAINER" pip install requests -q 2>/dev/null || true

docker exec "$BACKEND_CONTAINER" python3 /code/ciso_upload.py

echo -e "\n${GREEN}=====================================================${NC}"
echo -e "${GREEN}  ✓ CISO ASSISTANT SETUP DOKONČEN${NC}"
echo -e "${GREEN}=====================================================${NC}"
