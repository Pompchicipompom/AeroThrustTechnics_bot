# Требования к серверу

## Операционная система

- Ubuntu 22.04 / 24.04 LTS (рекомендуется) или другой Linux с Docker Engine
- Архитектура: x86_64 или ARM64

## Программное обеспечение

- Docker Engine 24+
- Плагин Docker Compose v2 (`docker compose version`)
- По желанию: `curl`, `git`, `openssl`

Установка Docker на Ubuntu:

```bash
bash infra/scripts/install_docker_ubuntu.sh
```

## Аппаратные ресурсы (MVP)

| Ресурс | Минимум | Рекомендуется |
|--------|---------|---------------|
| CPU | 1 vCPU | 2 vCPU |
| RAM | 2 GB | 4 GB |
| Диск | 20 GB SSD | 40+ GB SSD |
| Сеть | исходящий HTTPS к Telegram Bot API | то же |

Объём диска растёт вместе с вложениями в volume `uploads_data`.

## Порты

| Порт | Назначение | Открывать наружу? |
|------|------------|-------------------|
| `ADMIN_HOST_PORT` (по умолчанию 80) | Админка + API proxy + `/healthz` | Да (или через TLS-прокси) |
| 443 | HTTPS (если TLS на хосте) | Да |
| 5432 (PostgreSQL) | База данных | **Нет** — в compose не публикуется |
| 6379 (Redis) | Кэш / FSM | **Нет** — не публикуется |
| 8000 (backend) | Внутренний API | **Нет** в prod compose |

## Исходящий доступ

Бот использует **long polling** к Telegram:

- с сервера должен быть доступен `https://api.telegram.org`
- входящий webhook-порт для бота **не нужен**

Если на VPS нестабилен IPv6 до Telegram, оставьте `BOT_FORCE_IPV4=true` (значение по умолчанию).

## Домен и TLS

- Домен или публичный IP для админ-панели
- Рекомендуется TLS-сертификат (Let's Encrypt)
- `TODO: проверить вручную` — правила firewall / WAF компании

## Что нужно от компании

1. Токен Telegram-бота (BotFather) — `TELEGRAM_BOT_TOKEN`
2. SSH-доступ (если разворачивает подрядчик) с правами на Docker
3. Управление DNS домена (если HTTPS на домене компании)
4. Надёжные пароли и `ADMIN_JWT_SECRET` (или генерация подрядчиком с передачей по защищённому каналу)
