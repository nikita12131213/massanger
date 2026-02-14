# Messenger Lite (FastAPI + React)

## 1) Local dev

### Start infra
```bash
docker compose up -d postgres redis
```

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install .
cp .env.example .env
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
cp .env.example .env
npm i
npm run dev
```

Open `http://localhost:5173`.

## 2) Full docker mode
```bash
docker compose up --build
```

## 3) GitHub Pages (frontend only)
1. В репозитории откройте **Settings → Pages** и выберите **GitHub Actions** как источник деплоя.
2. Добавьте репозиторный secret `VITE_API_URL` (например, URL вашего backend API).
3. Запушьте в ветку `work` / `main` / `master` — workflow `.github/workflows/deploy-pages.yml` соберёт фронтенд и задеплоит его.
4. Для SPA-роутинга добавляется `404.html` (копия `index.html`), чтобы прямые переходы по маршрутам работали на Pages.

> Важно: GitHub Pages хостит только frontend. Backend (FastAPI, WS, Postgres, Redis) должен быть доступен отдельно по `VITE_API_URL`.

## Seed users
- alice / password
- bob / password
- charlie / password

## API examples
```bash
curl -X POST http://localhost:8000/api/auth/register -H 'Content-Type: application/json' -d '{"username":"john","password":"secret123"}'

curl -X POST http://localhost:8000/api/auth/login -c cookies.txt -H 'Content-Type: application/json' -d '{"username":"alice","password":"password"}'

curl -X POST http://localhost:8000/api/auth/refresh -b cookies.txt

curl -X GET 'http://localhost:8000/api/messages?conversation_id=1&limit=20' -H 'Authorization: Bearer <ACCESS>'
```

## Manual smoke checks
1. Register + login.
2. Find user and create dialog.
3. Open two tabs, send messages and verify realtime updates + typing.
4. Upload png/jpg/webp and check inline image preview.
5. Edit/delete own message from chat bubble actions.
6. Search messages in active dialog via chat search box.
7. Verify online indicator dot in dialogs (presence poll).

## Troubleshooting
- `401 on /refresh`: check cookie domain/samesite values in backend `.env`.
- `WS closes immediately`: ensure access token passed to `/ws?token=...`.
- `alembic can't connect`: verify postgres is up and `DATABASE_URL` is correct.
- `CORS`: set frontend URL in `ALLOWED_ORIGINS`.
- GitHub Pages `404` on refresh route: убедитесь, что workflow создал `dist/404.html`.
- GitHub Pages blank app/assets 404: проверьте `VITE_BASE_PATH` (должен быть `/repo-name/` для project pages).

## Roadmap
- Group chats, read receipts, pinned dialogs.
- Postgres FTS and message indexes.
- E2E tests (Playwright) and unit tests.
- WebRTC calls and push notifications.
