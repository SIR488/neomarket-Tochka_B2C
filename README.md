# NeoMarket B2C Backend

## Быстрый старт (Docker)

1. **Сборка и запуск:**
   ```bash
   docker-compose up --build
   ```

2. **Документация API:**
   Откройте в браузере: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

3. **Проверка работоспособности:**
   ```bash
   curl http://localhost:8000/health
   ```

## Архитектура
- `app/api/v1/`: Эндпоинты и схемы (Schemas)
- `app/application/`: Бизнес-логика (Services)
- `app/domain/`: (В процессе) Доменные модели
- `app/infrastructure/`: Реализация БД и Репозиториев
- `app/core/`: Конфигурация приложения
