# Admin UI

React + Vite интерфейс для административной части MVP.

## Реализовано
- вход по email/password через `/admin/auth/login`;
- получение профиля `/admin/auth/me`;
- вкладка Reports:
  - фильтры и пагинация `/admin/reports`;
  - просмотр карточки `/admin/reports/{id}`;
  - смена статуса `/admin/reports/{id}/status`;
- вкладка Analytics:
  - overview `/admin/analytics/overview`;
  - dynamics `/admin/analytics/dynamics`;
- вкладка Audit Logs:
  - фильтры и пагинация `/admin/audit-logs`.

## Локальный запуск
1. Установите зависимости:
```powershell
cd admin
npm install
```
2. Запустите UI:
```powershell
npm run dev
```
3. Откройте `http://localhost:5173`.

По умолчанию API вызывается через dev-proxy Vite (`/admin/*` -> `http://backend:8000` внутри Docker, либо задайте `VITE_PROXY_TARGET`).
Если нужен прямой API URL без прокси, укажите `VITE_API_BASE_URL`.

## Production image
Для VPS используется `admin/Dockerfile.prod`:
- сборка `npm run build`;
- раздача статики через `nginx`;
- проксирование `/admin/*` и `/healthz` в `backend:8000`.
