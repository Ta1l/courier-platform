#!/bin/bash
# ═══════════════════════════════════════════════════════
# Скрипт деплоя лендинга курьеров на Ubuntu 24.04
# Использование: sudo bash deploy.sh
# ═══════════════════════════════════════════════════════

set -e

# ─── Настройки (измените перед запуском) ───
DOMAIN="courier-spb.ru"              # Ваш домен
PROJECT_DIR="/opt/courier-landing"   # Папка проекта
WEB_DIR="/var/www/courier-landing"   # Папка веб-сервера
ENABLE_SSL=false                     # true — запросить SSL через Certbot

# ─── Цвета для вывода ───
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  Деплой лендинга курьеров — Ubuntu 24.04  ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""

# ─── Проверка root ───
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}✗ Запустите скрипт с sudo: sudo bash deploy.sh${NC}"
  exit 1
fi

# ─── 1. Обновление системы ───
echo -e "${YELLOW}[1/8] Обновление системы...${NC}"
apt update -y && apt upgrade -y

# ─── 2. Установка Node.js 20 LTS ───
echo -e "${YELLOW}[2/8] Установка Node.js 20 LTS...${NC}"
if ! command -v node &> /dev/null || [[ $(node -v | cut -d. -f1 | tr -d v) -lt 18 ]]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt install -y nodejs
  echo -e "${GREEN}✓ Node.js $(node -v) установлен${NC}"
else
  echo -e "${GREEN}✓ Node.js $(node -v) уже установлен${NC}"
fi

# ─── 3. Установка Nginx ───
echo -e "${YELLOW}[3/8] Установка Nginx...${NC}"
apt install -y nginx
systemctl enable nginx
systemctl start nginx
echo -e "${GREEN}✓ Nginx установлен и запущен${NC}"

# ─── 4. Сборка проекта ───
echo -e "${YELLOW}[4/8] Сборка проекта...${NC}"
cd "$PROJECT_DIR"
npm install
npm run build
echo -e "${GREEN}✓ Проект собран${NC}"

# ─── 5. Копирование файлов ───
echo -e "${YELLOW}[5/8] Копирование файлов на веб-сервер...${NC}"
mkdir -p "$WEB_DIR"
cp -r dist/* "$WEB_DIR/"
chown -R www-data:www-data "$WEB_DIR"
chmod -R 755 "$WEB_DIR"
echo -e "${GREEN}✓ Файлы скопированы в $WEB_DIR${NC}"

# ─── 6. Настройка Nginx ───
echo -e "${YELLOW}[6/8] Настройка Nginx...${NC}"
cat > /etc/nginx/sites-available/courier-landing << NGINX_CONF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};

    root ${WEB_DIR};
    index index.html;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_min_length 256;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/json
        application/xml
        image/svg+xml;

    # Кеширование
    location ~* \.(html)$ {
        expires 1h;
        add_header Cache-Control "public, must-revalidate";
    }

    location ~* \.(css|js|svg|png|jpg|jpeg|webp|avif|ico|woff|woff2|ttf)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Безопасность
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # SPA fallback
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Скрытые файлы
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
NGINX_CONF

# Активация сайта
ln -sf /etc/nginx/sites-available/courier-landing /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации
nginx -t
systemctl reload nginx
echo -e "${GREEN}✓ Nginx настроен для $DOMAIN${NC}"

# ─── 7. Firewall ───
echo -e "${YELLOW}[7/8] Настройка firewall...${NC}"
if command -v ufw &> /dev/null; then
  ufw allow 'Nginx Full' > /dev/null 2>&1 || true
  ufw allow ssh > /dev/null 2>&1 || true
  echo -e "${GREEN}✓ Firewall: порты 80, 443, 22 открыты${NC}"
else
  echo -e "${YELLOW}⚠ ufw не установлен — пропущено${NC}"
fi

# ─── 8. SSL (опционально) ───
if [ "$ENABLE_SSL" = true ]; then
  echo -e "${YELLOW}[8/8] Получение SSL-сертификата...${NC}"
  apt install -y certbot python3-certbot-nginx
  certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN"
  echo -e "${GREEN}✓ SSL-сертификат установлен${NC}"
else
  echo -e "${YELLOW}[8/8] SSL пропущен (ENABLE_SSL=false). Для включения:${NC}"
  echo -e "  sudo apt install -y certbot python3-certbot-nginx"
  echo -e "  sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
fi

# ─── Готово ───
echo ""
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ Деплой завершён!                      ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""
echo -e "  Сайт доступен: http://$DOMAIN"
echo -e "  Файлы сайта:   $WEB_DIR"
echo -e "  Исходники:     $PROJECT_DIR"
echo ""
echo -e "  ${YELLOW}Не забудьте:${NC}"
echo -e "  1. Привязать домен $DOMAIN к IP этого сервера"
echo -e "  2. Получить SSL: sudo certbot --nginx -d $DOMAIN"
echo -e "  3. Заменить домен в public/sitemap.xml и public/robots.txt"
echo ""
