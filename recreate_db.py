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

# Заполняем начальными данными
from app.seed import seed_database
from app.database import SessionLocal

db = SessionLocal()
try:
    seed_database(db)
    print("✓ База данных заполнена начальными данными")
except Exception as e:
    print(f"❌ Ошибка при заполнении БД: {e}")
finally:
    db.close()

print("✅ База данных обновлена!")