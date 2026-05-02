# check_configurations.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import func
from app.database import SessionLocal
from app import models

def main():
    db = SessionLocal()
    try:
        # Общая статистика
        total_scripts = db.query(models.Script).count()
        generated = db.query(models.Script).filter(
            models.Script.status == "generated"
        ).count()
        completed = db.query(models.Script).filter(
            models.Script.status == "completed"
        ).count()
        failed = db.query(models.Script).filter(
            models.Script.status == "failed"
        ).count()
        
        print("=" * 60)
        print(" Статистика скриптов в БД")
        print("=" * 60)
        print(f"Всего скриптов: {total_scripts}")
        print(f"  • Сгенерировано: {generated}")
        print(f"  • Выполнено: {completed}")
        print(f"  • Ошибки: {failed}")
        
        # Группировка по грунтам (из имени)
        print("\n Распределение по грунтам:")
        soil_query = db.query(
            func.split_part(models.Script.name, '_', 2).label('soil'),
            func.count().label('count')
        ).filter(
            models.Script.name.like('sim_%')
        ).group_by('soil').all()
        
        for soil, count in soil_query:
            print(f"  • {soil}: {count}")
        
        # Группировка по глубинам
        print("\n Распределение по глубинам:")
        scripts = db.query(models.Script).filter(
            models.Script.name.like('sim_%')
        ).limit(1000).all()
        
        depth_count = {}
        for script in scripts:
            for part in script.name.split('_'):
                if 'cm' in part:
                    depth = part.replace('cm', '')
                    depth_count[depth] = depth_count.get(depth, 0) + 1
        
        for depth in sorted(depth_count.keys()):
            print(f"  • {depth} см: {depth_count[depth]}")
        
        # Показать несколько примеров
        print("\n Примеры сгенерированных скриптов:")
        examples = db.query(models.Script).filter(
            models.Script.status == "generated"
        ).limit(5).all()
        
        for script in examples:
            print(f"\n  ID={script.id}: {script.name}")
            print(f"    Статус: {script.status}")
            print(f"    Создан: {script.created_at}")
            print(f"    Размер скрипта: {len(script.script_content)} символов")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()