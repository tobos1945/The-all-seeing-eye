from app.database import engine, Base
from app import models
import sys
from sqlalchemy import inspect, text

print("⚠️  УДАЛЯЕМ ВСЕ ТАБЛИЦЫ И ПЕРЕСОЗДАЕМ БАЗУ ДАННЫХ...")
print("Это удалит все существующие данные!")
print("Продолжить? (y/n): ")

choice = input().lower()
if choice != 'y':
    print("Отменено.")
    sys.exit(0)

# Получаем список всех таблиц
inspector = inspect(engine)
tables = inspector.get_table_names()

if tables:
    print(f"Найдены таблицы: {', '.join(tables)}")
    
    # ВАЖНО: Сначала отключаем проверку внешних ключей
    with engine.connect() as conn:
        # Для PostgreSQL
        if 'postgresql' in str(engine.url):
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
            conn.commit()
            print("✓ Схема public пересоздана (все таблицы удалены)")
        else:
            # Для других БД (SQLite, MySQL)
            Base.metadata.drop_all(bind=engine)
            print("✓ Таблицы удалены через SQLAlchemy")
else:
    print("ℹ️  Таблиц не найдено, создаем новые...")

# Создаем таблицы заново
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
    import traceback
    traceback.print_exc()
finally:
    db.close()

print("✅ База данных обновлена!")