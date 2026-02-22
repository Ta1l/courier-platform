#!/bin/bash
# ═══════════════════════════════════════════════════════
# Быстрое обновление сайта (после внесения изменений)
# Использование: sudo bash update.sh
# ═══════════════════════════════════════════════════════

set -e

PROJECT_DIR="/opt/courier-landing"
WEB_DIR="/var/www/courier-landing"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔄 Обновление сайта...${NC}"

cd "$PROJECT_DIR"

echo -e "${YELLOW}📦 Установка зависимостей...${NC}"
npm install --silent

echo -e "${YELLOW}🔨 Сборка...${NC}"
npm run build

echo -e "${YELLOW}📂 Копирование в $WEB_DIR...${NC}"
sudo cp -r dist/* "$WEB_DIR/"
sudo chown -R www-data:www-data "$WEB_DIR"

echo -e "${GREEN}✅ Сайт обновлён!${NC}"
