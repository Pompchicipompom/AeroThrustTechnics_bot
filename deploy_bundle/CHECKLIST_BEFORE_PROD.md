# Чеклист перед запуском в production

## Код и пакет передачи

- [ ] Доступ к приватному репозиторию **или** чистый архив без `.env` / `node_modules` / кэшей
- [ ] В комплекте есть папка `deploy_bundle/`
- [ ] Просмотрен `.env.production.example`
- [ ] В передаваемой ветке нет реальных токенов в истории git

## Сервер

- [ ] Установлены Docker и Docker Compose
- [ ] Достаточно места на диске (вложения растут)
- [ ] Есть исходящий доступ к `api.telegram.org`
- [ ] Firewall: снаружи только нужные порты (80/443)
- [ ] PostgreSQL и Redis не открыты в интернет

## Секретные данные

- [ ] Надёжный `POSTGRES_PASSWORD`
- [ ] Тот же пароль в `DATABASE_URL`
- [ ] Уникальный сильный `ADMIN_JWT_SECRET` (не `change-me-for-prod`)
- [ ] Действительный `TELEGRAM_BOT_TOKEN`
- [ ] Сильный пароль администратора (не примеры из README)
- [ ] `APP_ENV=prod`

## Первый запуск

- [ ] Успешно выполнен `bash infra/scripts/deploy_vps.sh`
- [ ] `curl /healthz` возвращает `status: ok`
- [ ] Открывается `/admin/`
- [ ] Создан пользователь админки
- [ ] Создан invite-код
- [ ] Бот: `/start` + invite-код работает
- [ ] Тестовое обращение видно в админке
- [ ] Смена статуса обращения работает
- [ ] Вложение (если используется) сохраняется и скачивается из админки

## Сохранность данных

- [ ] Команда знает: в production **нельзя** `docker compose down -v`
- [ ] Хотя бы раз проверен скрипт резервного копирования
- [ ] Volumes зафиксированы в эксплуатационной документации хостинга

### Резервное копирование PostgreSQL

```bash
mkdir -p backups
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U aerotrust aerotrust | gzip > "backups/aerotrust_$(date +%Y%m%d_%H%M%S).sql.gz"
```

Или:

```bash
bash infra/scripts/backup_postgres.sh
```

### Резервное копирование вложений

```bash
bash infra/scripts/backup_uploads.sh
```

### Восстановление БД (перезаписывает данные)

```bash
gunzip -c backups/aerotrust_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U aerotrust -d aerotrust
```

### Проверка после перезапуска

```bash
docker compose -f docker-compose.prod.yml restart
docker compose -f docker-compose.prod.yml ps
# убедиться, что обращения по-прежнему видны в админке
```

## Безопасность

- [ ] Перед админкой настроен TLS (рекомендуется)
- [ ] Не используются пароли-примеры из README
- [ ] При `APP_ENV=prod` недоступен `/docs`
- [ ] API обращений требует авторизации администратора
- [ ] Для анонимных обращений автор скрыт в UI/API админки

## Проверить вручную

- [ ] `TODO: проверить вручную` — HTTPS-сертификат и домен
- [ ] `TODO: проверить вручную` — SSO / VPN компании (если требуется)
- [ ] `TODO: проверить вручную` — настройки приватности и описание бота в Telegram
- [ ] `TODO: проверить вручную` — ночной cron резервного копирования на хосте
- [ ] `TODO: проверить вручную` — мониторинг / оповещения о доступности
