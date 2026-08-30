#!/bin/sh

# Останавливаем выполнение при любой ошибке
set -e

echo "=== Применяем миграции Alembic ==="
uv run alembic upgrade head

echo "=== Запускаем Telegram-бота ==="
exec "$@"