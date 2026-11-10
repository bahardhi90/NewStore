# Putting RADA online (www.radawear.com)

Everything runs with Docker on one Linux server. Caddy in front gets free HTTPS certificates automatically.

| Address | What it serves |
|---|---|
| `https://www.radawear.com` | The shop (Next.js) |
| `https://api.radawear.com` | The API, and the admin panel at `/admin/` |
| `https://radawear.com` | Redirects to www |

Steps 1–5 are done once. After that, publishing changes is step 6.

---

## 1. DNS (at your domain registrar)

Create three **A records** pointing to your server's public IP:

| Name | Type | Value |
|---|---|---|
| `@` (radawear.com) | A | your server IP |
| `www` | A | your server IP |
| `api` | A | your server IP |

If you use Cloudflare or ArvanCloud in front, set these records to **DNS only** (grey cloud) at first, so Caddy can get the certificates.

Check from your PC: `nslookup www.radawear.com` should show your server IP.

## 2. Prepare the server (Ubuntu/Debian, once)

```bash
ssh root@YOUR_SERVER_IP

# Docker + Git
curl -fsSL https://get.docker.com | sh
apt-get install -y git

# Firewall: only SSH, HTTP, HTTPS
ufw allow OpenSSH && ufw allow 80 && ufw allow 443 && ufw --force enable
```

**If the server is in Iran:** Docker Hub, npm and PyPI may be blocked or slow. Configure a Docker mirror, for example ArvanCloud's (`https://docker.arvancloud.ir`), in `/etc/docker/daemon.json`:

```json
{ "registry-mirrors": ["https://docker.arvancloud.ir"] }
```

Then run `systemctl restart docker`.

## 3. Send the code to the server

**On your PC**, put the project in a **private** Git repository (GitHub, GitLab…) once, from `D:\NewStore`:

```powershell
cd D:\NewStore
git init
git add .
git commit -m "RADA store"
git branch -M main
git remote add origin https://github.com/YOUR_USER/radawear.git   # create the empty private repo first
git push -u origin main
```

Secrets are not uploaded: `.env` files, uploaded images (`media/`) and `node_modules` are excluded.

**On the server:**

```bash
git clone https://github.com/YOUR_USER/radawear.git /srv/radawear
```

For a private repo, Git asks for a username and a token. On GitHub, create one under Settings → Developer settings → Personal access tokens.

## 4. Settings and first start

```bash
cd /srv/radawear/deploy
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(50))"   # copy this into SECRET_KEY
nano .env      # set SECRET_KEY, POSTGRES_PASSWORD (letters and digits only), ACME_EMAIL, ZARINPAL_MERCHANT_ID
docker compose up -d --build
```

The first build takes 5–10 minutes. Check that everything is running:

```bash
docker compose ps                 # all "Up"
docker compose logs caddy --tail 20   # look for "certificate obtained successfully"
```

Open https://www.radawear.com. At this point the database is empty. Step 5 brings your current content over; if you'd rather start fresh, create an admin user instead:

```bash
docker compose exec web python manage.py createsuperuser
```

### Server already runs nginx (other websites on ports 80/443)

If `docker compose up` fails with `failed to bind host port 0.0.0.0:80/tcp: address already in use`, nginx owns the ports. Keep it, and let it forward the RADA domains to Caddy on a local port:

```bash
cd /srv/radawear/deploy
# 1. Turn on the behind-nginx mode (uncomment these two lines in .env):
#      COMPOSE_FILE=docker-compose.yml:docker-compose.behind-nginx.yml
#      CADDY_HTTP_PORT=8080          # any free local port
nano .env
docker compose up -d                  # Caddy now listens on 127.0.0.1:8080 only

# 2. nginx site for radawear.com, www and api
sudo cp nginx/radawear.conf /etc/nginx/sites-available/radawear.conf
sudo ln -s /etc/nginx/sites-available/radawear.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 3. HTTPS certificates through nginx
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d radawear.com -d www.radawear.com -d api.radawear.com --redirect
```

Your other nginx sites are not touched. `update.sh` keeps using this mode because it is set in `.env`.

## 5. Bring over your current content (products, images, settings)

**On your PC** (PowerShell), from `D:\NewStore\store-backend` while the local backend is running:

```powershell
docker compose exec -T db pg_dump -U store -Fc --no-owner -f /tmp/store.dump store
docker compose cp db:/tmp/store.dump ..\store.dump
tar -czf ..\media.tar.gz -C media .
scp ..\store.dump ..\media.tar.gz root@YOUR_SERVER_IP:/srv/radawear/
```

**On the server**, from `/srv/radawear/deploy`. Replace `store` if you changed `POSTGRES_USER` / `POSTGRES_DB`:

```bash
docker compose stop web celery beat
docker compose cp ../store.dump db:/tmp/store.dump
docker compose exec db pg_restore -U store -d store --clean --if-exists --no-owner /tmp/store.dump
docker compose run --rm --no-deps -v /srv/radawear:/import web sh -c "tar -xzf /import/media.tar.gz -C /app/media"
docker compose up -d
rm ../store.dump ../media.tar.gz
```

Your admin login (09124077041 and its password) is now the same as on your PC.

## 6. Publishing changes later

Commit and push on your PC:

```powershell
cd D:\NewStore
git add .
git commit -m "describe the change"
git push
```

Then on the server:

```bash
sh /srv/radawear/deploy/update.sh
```

## 7. After going live: checklist in the admin panel (https://api.radawear.com/admin/)

- **روش‌های پرداخت:** activate Zarinpal (and Digipay or SnappPay) with your real merchant details. The test gateway is hidden in production.
- **تنظیمات پیامک:** switch to Melipayamak, then enter the pattern codes in **پیامک‌های خودکار**. Add the server's IP in the Melipayamak panel's allowed IP list.
- At your payment gateway, register the site address `https://www.radawear.com` if they ask for it.

## Daily backup (recommended)

```bash
crontab -e
# add this line: database backup every night at 03:00, kept 14 days, in /srv/radawear/deploy/backups
0 3 * * * cd /srv/radawear/deploy && COMPOSE_FILE=docker-compose.yml sh ../store-backend/scripts/backup_db.sh >> /var/log/radawear-backup.log 2>&1
```

Copy backups off the server from time to time. The uploaded images are in the Docker volume `radawear_media`.

## Useful commands (in `/srv/radawear/deploy`)

| What | Command |
|---|---|
| Status | `docker compose ps` |
| Logs of the site / API / SMS | `docker compose logs -f frontend` / `web` / `celery` |
| Restart everything | `docker compose restart` |
| Change admin password | `docker compose exec web python manage.py changepassword 09124077041` |
| Stop | `docker compose down` (data is kept) |
