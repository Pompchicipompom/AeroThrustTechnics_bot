# Рекомендуемая структура проекта

```text
aerotrust_bot/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── bot/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── integrations/
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── admin/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── infra/
│   ├── nginx/
│   │   └── default.conf
│   ├── docker/
│   └── scripts/
├── docs/
│   ├── 01_product_brief.md
│   ├── 02_tech_spec_mvp.md
│   ├── 03_architecture_and_stack.md
│   ├── 05_codex_first_prompt.md
│   └── 06_project_structure.md
├── docker-compose.yml
├── .env.example
├── README.md
└── .gitignore
```

## Комментарии
- `backend/app/bot` — handlers, keyboards, FSM
- `backend/app/api` — admin/API endpoints
- `backend/app/services` — бизнес-логика
- `backend/app/models` — ORM models
- `admin/` — веб-панель
- `infra/` — конфиги nginx, скрипты деплоя
