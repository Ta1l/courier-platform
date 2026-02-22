# Deploy/Update Guide (Ubuntu 24.04)

Домен: `https://kurer-spb.ru`  
API/админка: `127.0.0.1:8000` за Nginx  
Путь проекта (рекомендовано): `/opt/kurer-spb`

## 1. Первичная подготовка сервера

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip nginx curl

# Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

## 2. Клонирование проекта

```bash
cd /opt
sudo git clone <YOUR_REPO_URL> kurer-spb
sudo chown -R $USER:$USER /opt/kurer-spb
cd /opt/kurer-spb
```

## 3. Python окружение и зависимости

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r tg/requirements.txt
```

## 4. Env-конфигурация

Файл: `tg/.env`

Минимально должно быть:

```env
BOT_TOKEN=...
ADMIN_ID=...
DB_PATH=/opt/kurer-spb/tg/applications.db
API_HOST=127.0.0.1
API_PORT=8000
API_CORS_ORIGINS=https://kurer-spb.ru,https://www.kurer-spb.ru
API_JWT_SECRET=...
API_JWT_ALGORITHM=HS256
API_ACCESS_TOKEN_EXPIRE_MINUTES=15
API_REFRESH_TOKEN_EXPIRE_DAYS=30
API_LOGIN_RATE_LIMIT=5
API_LOGIN_RATE_WINDOW_SECONDS=900
ADMIN_BOOTSTRAP_LOGIN=admin
ADMIN_BOOTSTRAP_PASSWORD=...
ADMIN_BOOTSTRAP_NAME=Administrator
ADMIN_DIST_DIR=admin-dist
SITE_BASE_URL=https://kurer-spb.ru
```

## 5. Сборка фронтенда

```bash
# Лэндинг
npm --prefix vie ci
npm --prefix vie run build

# Админ SPA
npm --prefix admin-spa ci
npm --prefix admin-spa run build
```

После сборки должны существовать:
- `/opt/kurer-spb/dist`
- `/opt/kurer-spb/admin-dist`

## 6. Миграции БД

```bash
source /opt/kurer-spb/.venv/bin/activate
python tg/migrations/runner.py --db /opt/kurer-spb/tg/applications.db upgrade
```

## 7. systemd сервисы

### `/etc/systemd/system/kurer-api.service`

```ini
[Unit]
Description=Kurer FastAPI backend
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/kurer-spb/tg
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/kurer-spb/.venv/bin/python /opt/kurer-spb/tg/server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### `/etc/systemd/system/kurer-bot.service`

```ini
[Unit]
Description=Kurer Telegram bot
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/kurer-spb/tg
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/kurer-spb/.venv/bin/python /opt/kurer-spb/tg/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Применить:

```bash
sudo systemctl daemon-reload
sudo systemctl enable kurer-api kurer-bot
sudo systemctl restart kurer-api kurer-bot
sudo systemctl status kurer-api --no-pager
sudo systemctl status kurer-bot --no-pager
```

## 8. Nginx (домен + SSL)

### `/etc/nginx/sites-available/kurer-spb.ru`

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name kurer-spb.ru www.kurer-spb.ru;

    root /opt/kurer-spb/dist;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /admin {
        proxy_pass http://127.0.0.1:8000/admin;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:8000/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

Применить:

```bash
sudo ln -sf /etc/nginx/sites-available/kurer-spb.ru /etc/nginx/sites-enabled/kurer-spb.ru
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

SSL:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d kurer-spb.ru -d www.kurer-spb.ru
```

## 9. Обновление проекта на сервере (после git push)

```bash
cd /opt/kurer-spb
git pull

source .venv/bin/activate
pip install -r tg/requirements.txt

npm --prefix vie ci
npm --prefix vie run build
npm --prefix admin-spa ci
npm --prefix admin-spa run build

python tg/migrations/runner.py --db /opt/kurer-spb/tg/applications.db upgrade

sudo systemctl restart kurer-api kurer-bot
sudo systemctl reload nginx
```

Проверка:

```bash
curl -I https://kurer-spb.ru
curl -I https://kurer-spb.ru/admin
curl -I https://kurer-spb.ru/api/docs
```
