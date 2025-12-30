from app.database import engine, Base
from app import models
import sys

print("⚠️  УДАЛЯЕМ ВСЕ ТАБЛИЦЫ И ПЕРЕСОЗДАЕМ БАЗУ ДАННЫХ...")
print("Это удалит все существующие данные!")
print("Продолжить? (y/n): ")

choice = input().lower()
if choice != 'y':
    print("Отменено.")
    sys.exit(0)

# Удаляем все таблицы
Base.metadata.drop_all(bind=engine)
print("✓ Таблицы удалены")

# Создаем заново с обновленной структурой
Base.metadata.create_all(bind=engine)
print("✓ Таблицы созданы заново")
print("✅ База данных обновлена!")
