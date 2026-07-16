# Требования к серверу

## Операционная система

- Ubuntu 22.04 / 24.04 LTS (рекомендуется) или иной Linux с поддержкой Docker Engine
- Архитектура: x86_64 или ARM64

## Программное обеспечение

Для запуска требуется:

- Docker Engine 24+
- Docker Compose plugin v2 (`docker compose version`)
- Git — при обновлении через `git pull`
- По необходимости: `curl`, `openssl`

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

Объём диска увеличивается вместе с файловыми вложениями в volume `uploads_data`.

## Порты

| Порт | Назначение | Публикация наружу |
|------|------------|-------------------|
| `ADMIN_HOST_PORT` (по умолчанию 80) | Админка, API proxy, `/healthz` | Да (или через TLS-прокси) |
| 443 | HTTPS при TLS на хосте | Да |
| 5432 (PostgreSQL) | База данных | Нет (в compose не публикуется) |
| 6379 (Redis) | FSM / rate limit | Нет |
| 8000 (backend) | Внутренний API | Нет в prod compose |

## Сетевой доступ

- Исходящий доступ к `https://api.telegram.org` обязателен
- Входящий webhook-порт для бота не требуется (используется long polling)
- При нестабильном IPv6 до Telegram рекомендуется `BOT_FORCE_IPV4=true`

## Домен и HTTPS

- Для доступа к админке используется домен или внутренний/публичный адрес сервера
- Для промышленной среды рекомендуется HTTPS (Let's Encrypt или корпоративный сертификат)
- TLS-терминация выполняется на хосте / reverse proxy / балансировщике перед контейнером `admin`

## Хранение данных

На сервере должны сохраняться Docker volumes:

| Volume | Назначение |
|--------|------------|
| `aerotrust_postgres_data` | PostgreSQL |
| `aerotrust_uploads_data` | Вложения |
| `aerotrust_redis_data` | FSM / rate limit |

Команда `docker compose down -v` удаляет volumes и приводит к потере данных.

## Резервное копирование

На сервере рекомендуется:

- регулярный backup PostgreSQL;
- backup каталога вложений;
- хранение копий вне тома приложения.

Порядок описан в `BACKUP_AND_RESTORE.md`.

## Учётные данные и доступы для эксплуатации

Для развёртывания и сопровождения необходимы:

1. `TELEGRAM_BOT_TOKEN`
2. Доступ к серверу с правами на Docker
3. Права на DNS домена (при использовании HTTPS на домене)
4. Надёжные значения `POSTGRES_PASSWORD`, `ADMIN_JWT_SECRET` и пароля администратора
