# Лендинг — Работа курьером в Санкт-Петербурге

Одностраничный продающий сайт для набора курьеров в СПб. Переводит трафик из пабликов в Telegram-бот.

---

## 📋 Содержание

1. [Требования](#требования)
2. [Установка на Ubuntu 24.04](#установка-на-ubuntu-2404)
3. [Сборка проекта](#сборка-проекта)
4. [Настройка перед публикацией](#настройка-перед-публикацией)
5. [Вариант A: Nginx (рекомендуется)](#вариант-a-размещение-через-nginx-рекомендуется)
6. [Вариант B: Apache](#вариант-b-размещение-через-apache)
7. [Вариант C: Netlify / Vercel](#вариант-c-netlifyvercel-бесплатно)
8. [SSL-сертификат (Let's Encrypt)](#ssl-сертификат-lets-encrypt)
9. [Привязка домена](#привязка-домена)
10. [UTM-метки и Deep Links](#utm-метки-и-deep-links)
11. [Обновление сайта](#обновление-сайта)
12. [Устранение проблем](#устранение-проблем)

---

## Требования

- **ОС:** Ubuntu 24.04 LTS (или любой Linux)
- **Node.js:** 18+ (рекомендуется 20 LTS или 22 LTS)
- **npm:** 9+ (ставится вместе с Node.js)
- **Веб-сервер:** Nginx (рекомендуется) или Apache
- **Домен:** любой (например `courier-spb.ru`)
- **VPS/сервер:** минимум 512 MB RAM, 1 CPU (сайт статический — нагрузка минимальная)

---

## Установка на Ubuntu 24.04

### Шаг 1. Обновите систему

```bash
sudo apt update && sudo apt upgrade -y
```

### Шаг 2. Установите Node.js 20 LTS

```bash
# Через NodeSource (рекомендуется)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Проверьте версии
node --version   # должно быть v20.x.x
npm --version    # должно быть 9.x или 10.x
```

**Альтернатива — через nvm (если нужно несколько версий Node.js):**

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20
```

### Шаг 3. Установите Git (если ещё нет)

```bash
sudo apt install -y git
```

### Шаг 4. Скопируйте проект на сервер

**Вариант A — через Git:**
```bash
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/courier-landing.git
sudo chown -R $USER:$USER /opt/courier-landing
cd /opt/courier-landing
```

**Вариант B — через SCP (загрузка архива с локальной машины):**
```bash
# На ЛОКАЛЬНОЙ машине (где лежит проект):
tar -czf courier-landing.tar.gz courier-landing/
scp courier-landing.tar.gz user@YOUR_SERVER_IP:/opt/

# На СЕРВЕРЕ:
cd /opt
tar -xzf courier-landing.tar.gz
cd courier-landing
```

**Вариант C — через SFTP (FileZilla и др.):**
1. Подключитесь к серверу по SFTP (порт 22)
2. Загрузите всю папку проекта в `/opt/courier-landing/`

### Шаг 5. Установите зависимости

```bash
cd /opt/courier-landing
npm install
```

---

## Сборка проекта

```bash
cd /opt/courier-landing
npm run build
```

После сборки в папке `dist/` появится файл `index.html` — это **единственный файл**, который нужно разместить на веб-сервере. Проект использует `vite-plugin-singlefile`, который инлайнит все CSS и JS прямо в HTML.

Также в `dist/` будут скопированы файлы из `public/`:
- `robots.txt`
- `sitemap.xml`
- `_redirects` (для Netlify)
- `assets/icons/bike-e.svg`

```bash
# Проверьте, что сборка прошла успешно:
ls -la dist/
# Должны увидеть: index.html, robots.txt, sitemap.xml, assets/
```

---

## Настройка перед публикацией

### 1. BOT_LINK (Telegram-бот)

Бот уже настроен на `@kurer_pro_bot`. Если нужно изменить:

**Файл `src/config.ts`** — основной конфиг:
```typescript
export const CONFIG = {
  BOT_LINK: "https://t.me/kurer_pro_bot?start=",
  // Замените kurer_pro_bot на имя вашего бота
};
```

**Файл `config.json`** — справочный конфиг:
```json
{
  "BOT_LINK": "tg://resolve?domain=kurer_pro_bot&start=SOURCE_PLACEHOLDER"
}
```

После изменения пересоберите: `npm run build`

### 2. Аналитика

Откройте `vie/index.html` (исходный шаблон, НЕ `dist/index.html`):

**Google Analytics 4:**
Найдите закомментированный блок `GA4 Placeholder` и раскомментируйте его, заменив `G-XXXXXXXXXX` на ваш Measurement ID.

**Яндекс.Метрика:**
Найдите закомментированный блок `Yandex.Metrika Placeholder` и раскомментируйте его, заменив `XXXXXXXX` на ваш ID счётчика.

После изменений: `npm run build`

### 3. Домен в sitemap.xml и robots.txt

```bash
# Замените your-domain.com на ваш реальный домен:
sed -i 's/your-domain.com/courier-spb.ru/g' public/sitemap.xml
sed -i 's/your-domain.com/courier-spb.ru/g' public/robots.txt

# Пересоберите
npm run build
```

---

## Вариант A: Размещение через Nginx (рекомендуется)

### Шаг 1. Установите Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

### Шаг 2. Создайте директорию для сайта

```bash
sudo mkdir -p /var/www/courier-landing
sudo cp -r /opt/courier-landing/dist/* /var/www/courier-landing/
sudo chown -R www-data:www-data /var/www/courier-landing
sudo chmod -R 755 /var/www/courier-landing
```

### Шаг 3. Создайте конфиг Nginx

```bash
sudo nano /etc/nginx/sites-available/courier-landing
```

Вставьте содержимое (замените `courier-spb.ru` на ваш домен):

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name courier-spb.ru www.courier-spb.ru;

    root /var/www/courier-landing;
    index index.html;

    # Gzip сжатие
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
        application/rss+xml
        image/svg+xml;

    # Brotli (если установлен модуль)
    # brotli on;
    # brotli_comp_level 6;
    # brotli_types text/plain text/css application/javascript application/json image/svg+xml;

    # Кеширование статики
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

    # robots.txt и sitemap.xml
    location = /robots.txt {
        access_log off;
        log_not_found off;
    }

    location = /sitemap.xml {
        access_log off;
    }

    # SPA fallback — все пути ведут на index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Запретить доступ к скрытым файлам
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

### Шаг 4. Активируйте конфиг

```bash
# Создайте симлинк
sudo ln -s /etc/nginx/sites-available/courier-landing /etc/nginx/sites-enabled/

# Удалите дефолтный сайт (опционально)
sudo rm -f /etc/nginx/sites-enabled/default

# Проверьте конфигурацию на ошибки
sudo nginx -t

# Перезагрузите Nginx
sudo systemctl reload nginx
```

### Шаг 5. Проверьте

```bash
# Если домен ещё не привязан, проверьте по IP:
curl -I http://YOUR_SERVER_IP

# Должны увидеть: HTTP/1.1 200 OK
```

Откройте в браузере: `http://YOUR_SERVER_IP` — должен отобразиться сайт.

---

## Вариант B: Размещение через Apache

### Шаг 1. Установите Apache

```bash
sudo apt install -y apache2
sudo systemctl enable apache2
sudo systemctl start apache2

# Включите необходимые модули
sudo a2enmod rewrite
sudo a2enmod headers
sudo a2enmod deflate
```

### Шаг 2. Скопируйте файлы

```bash
sudo mkdir -p /var/www/courier-landing
sudo cp -r /opt/courier-landing/dist/* /var/www/courier-landing/
sudo chown -R www-data:www-data /var/www/courier-landing
```

### Шаг 3. Создайте конфиг Apache

```bash
sudo nano /etc/apache2/sites-available/courier-landing.conf
```

Вставьте:

```apache
<VirtualHost *:80>
    ServerName courier-spb.ru
    ServerAlias www.courier-spb.ru
    DocumentRoot /var/www/courier-landing

    <Directory /var/www/courier-landing>
        AllowOverride All
        Require all granted

        # SPA fallback
        RewriteEngine On
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule ^ /index.html [L]
    </Directory>

    # Gzip сжатие
    <IfModule mod_deflate.c>
        AddOutputFilterByType DEFLATE text/html text/css application/javascript application/json image/svg+xml
    </IfModule>

    # Кеширование
    <IfModule mod_expires.c>
        ExpiresActive On
        ExpiresByType text/html "access plus 1 hour"
        ExpiresByType text/css "access plus 30 days"
        ExpiresByType application/javascript "access plus 30 days"
        ExpiresByType image/svg+xml "access plus 30 days"
    </IfModule>

    # Безопасность
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"

    ErrorLog ${APACHE_LOG_DIR}/courier-error.log
    CustomLog ${APACHE_LOG_DIR}/courier-access.log combined
</VirtualHost>
```

### Шаг 4. Активируйте

```bash
sudo a2ensite courier-landing.conf
sudo a2dissite 000-default.conf  # отключить дефолтный (опционально)
sudo systemctl reload apache2
```

---

## Вариант C: Netlify/Vercel (бесплатно)

### Netlify

1. Зарегистрируйтесь на [netlify.com](https://netlify.com)
2. Нажмите **"Add new site"** → **"Deploy manually"**
3. Перетащите папку `dist/` в окно Netlify
4. Готово! Netlify выдаст URL вида `xxx.netlify.app`
5. Для своего домена: **Site settings → Domain management → Add custom domain**

### Vercel

1. Зарегистрируйтесь на [vercel.com](https://vercel.com)
2. Установите CLI: `npm i -g vercel`
3. В папке проекта:
```bash
cd /opt/courier-landing
vercel --prod
```
4. Следуйте инструкциям (Vercel определит Vite автоматически)

---

## SSL-сертификат (Let's Encrypt)

**Важно:** сначала привяжите домен к серверу (см. раздел ниже), иначе сертификат не выдадут.

### Установка Certbot

```bash
sudo apt install -y certbot
```

### Для Nginx:

```bash
sudo apt install -y python3-certbot-nginx
sudo certbot --nginx -d courier-spb.ru -d www.courier-spb.ru
```

Certbot автоматически:
- Получит сертификат
- Настроит Nginx на HTTPS
- Добавит редирект с HTTP на HTTPS

### Для Apache:

```bash
sudo apt install -y python3-certbot-apache
sudo certbot --apache -d courier-spb.ru -d www.courier-spb.ru
```

### Автообновление сертификата

Certbot на Ubuntu 24.04 автоматически создаёт таймер systemd:

```bash
# Проверьте, что таймер работает:
sudo systemctl status certbot.timer

# Тестовое обновление:
sudo certbot renew --dry-run
```

---

## Привязка домена

### Шаг 1. Узнайте IP вашего сервера

```bash
curl ifconfig.me
# Например: 185.123.45.67
```

### Шаг 2. Настройте DNS у регистратора домена

Зайдите в панель управления доменом (Reg.ru, Timeweb, Beget, Namecheap и т.д.) и добавьте записи:

| Тип  | Имя             | Значение        | TTL  |
|------|-----------------|-----------------|------|
| A    | @               | 185.123.45.67   | 3600 |
| A    | www             | 185.123.45.67   | 3600 |

### Шаг 3. Подождите 5–30 минут

DNS-записи обновляются от 5 минут до 48 часов (обычно 5–30 минут).

```bash
# Проверьте, что домен указывает на ваш IP:
dig +short courier-spb.ru
# Должен показать ваш IP
```

### Шаг 4. Получите SSL (см. раздел выше)

---

## UTM-метки и Deep Links

При размещении ссылок в пабликах используйте UTM-метки:

```
https://courier-spb.ru/?utm_source=vk
https://courier-spb.ru/?utm_source=telegram
https://courier-spb.ru/?utm_source=avito
https://courier-spb.ru/?utm_source=dzen
```

Сайт автоматически подставит источник в ссылку бота:
- `?utm_source=vk` → бот получит `?start=vk`
- `?utm_source=telegram` → бот получит `?start=telegram`
- Без UTM → бот получит `?start=pub` (по умолчанию)

---

## Обновление сайта

Если вы внесли изменения в код:

```bash
cd /opt/courier-landing

# Если через Git — подтяните изменения:
git pull origin main

# Пересоберите
npm run build

# Скопируйте в Nginx
sudo cp -r dist/* /var/www/courier-landing/
sudo chown -R www-data:www-data /var/www/courier-landing

# Готово! Nginx подхватит новые файлы автоматически.
```

### Автоматизация (скрипт обновления)

Создайте скрипт:

```bash
sudo nano /opt/courier-landing/deploy.sh
```

```bash
#!/bin/bash
set -e

echo "🔄 Обновление сайта..."
cd /opt/courier-landing

echo "📦 Установка зависимостей..."
npm install

echo "🔨 Сборка..."
npm run build

echo "📂 Копирование в /var/www/..."
sudo cp -r dist/* /var/www/courier-landing/
sudo chown -R www-data:www-data /var/www/courier-landing

echo "✅ Готово! Сайт обновлён."
```

```bash
chmod +x /opt/courier-landing/deploy.sh

# Запуск:
/opt/courier-landing/deploy.sh
```

---

## Устранение проблем

| Проблема | Решение |
|----------|---------|
| `npm: command not found` | Установите Node.js (см. Шаг 2) |
| Ошибка при `npm install` | `rm -rf node_modules package-lock.json && npm install` |
| Nginx: `nginx -t` ошибка | Проверьте синтаксис конфига, особенно точки с запятой |
| Сайт не открывается по IP | `sudo ufw allow 80/tcp && sudo ufw allow 443/tcp` |
| Certbot не работает | Убедитесь, что домен указывает на сервер (`dig +short domain.com`) |
| Белая страница в браузере | Откройте DevTools (F12) → Console, проверьте ошибки |
| Кнопки не ведут в бот | Проверьте `src/config.ts` — поле `BOT_LINK` |
| После обновления старая версия | Очистите кеш браузера (`Ctrl+Shift+R`) |

### Полезные команды для диагностики:

```bash
# Статус Nginx
sudo systemctl status nginx

# Логи Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Проверка портов
sudo ss -tlnp | grep -E ':80|:443'

# Проверка firewall
sudo ufw status

# Открыть порты (если заблокированы)
sudo ufw allow 'Nginx Full'
# или
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## Структура проекта

```
courier-landing/
├── package.json            ← Корневые скрипты-обёртки (`npm run build`, `npm run dev`)
├── tg/                     ← Telegram-бот (aiogram + SQLite)
├── vie/
│   ├── package.json        ← Фронтенд-зависимости
│   ├── vite.config.ts      ← Конфиг Vite
│   ├── index.html          ← HTML шаблон с мета и аналитикой
│   ├── src/
│   │   ├── App.tsx         ← Главный компонент лендинга
│   │   ├── config.ts       ← BOT_LINK и UTM логика
│   │   ├── index.css       ← Стили (Tailwind + кастомные)
│   │   ├── main.tsx        ← Точка входа React
│   │   └── utils/cn.ts     ← Утилита для классов
│   └── public/
│       ├── robots.txt      ← Для поисковых роботов
│       ├── sitemap.xml     ← Карта сайта (замените домен!)
│       ├── _redirects      ← Для Netlify
│       └── assets/icons/
│           └── bike-e.svg  ← SVG-иконка электровелосипеда
└── dist/                   ← Результат `npm run build` (готово для хостинга)
```
