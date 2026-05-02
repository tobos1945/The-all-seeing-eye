from sqlalchemy.orm import Session
from app import models

def seed_database(db: Session):
    """Идемпотентное заполнение базы данных начальными данными"""
    
    # Типы грунта
    soil_types_data = [
        {"name": "песок_сухой", "description": "Сухой песок", "parameters": {"epsilon": 4.0, "sigma": 0.0001}},
        {"name": "песок_средний", "description": "Песок 40% влажности", "parameters": {"epsilon": 10.0, "sigma": 0.001}},
        {"name": "песок_влажный", "description": "Песок 80% влажности", "parameters": {"epsilon": 20.0, "sigma": 0.01}},
        {"name": "глина_сухая", "description": "Сухая глина", "parameters": {"epsilon": 5.0, "sigma": 0.001}},
        {"name": "глина_средняя", "description": "Глина 40% влажности", "parameters": {"epsilon": 15.0, "sigma": 0.01}},
        {"name": "глина_влажная", "description": "Глина 80% влажности", "parameters": {"epsilon": 30.0, "sigma": 0.1}},
        {"name": "лёд_сухой", "description": "Пресный лёд", "parameters": {"epsilon": 3.2, "sigma": 0.00001}},
        {"name": "лёд_средний", "description": "Лёд с примесями", "parameters": {"epsilon": 3.5, "sigma": 0.0001}},
        {"name": "лёд_влажный", "description": "Влажный лёд", "parameters": {"epsilon": 4.0, "sigma": 0.001}},
    ]
    
    for item in soil_types_data:
        existing = db.query(models.SoilType).filter_by(name=item["name"]).first()
        if not existing:
            db.add(models.SoilType(**item))
    db.commit()
    print("Типы грунта добавлены")

    # Материалы объектов
    materials_data = [
        {"name": "металл", "parameters": {"epsilon": 1.0, "sigma": 1e7}},
        {"name": "камень", "parameters": {"epsilon": 7.0, "sigma": 0.001}},
        {"name": "пластик", "parameters": {"epsilon": 2.5, "sigma": 0.0}},
    ]
    
    for item in materials_data:
        existing = db.query(models.Material).filter_by(name=item["name"]).first()
        if not existing:
            db.add(models.Material(**item))
    db.commit()
    print("Материалы добавлены")

    metal = db.query(models.Material).filter_by(name="металл").first()
    stone = db.query(models.Material).filter_by(name="камень").first()
    plastic = db.query(models.Material).filter_by(name="пластик").first()

    # Целевые объекты
    target_types_data = [
        # Диски
        {"name": "диск_металлический", "shape": "disk", 
         "dimensions": {"diameter": 0.05, "thickness": 0.05}, "material_id": metal.id},
        {"name": "диск_каменный", "shape": "disk", 
         "dimensions": {"diameter": 0.1, "thickness": 0.05}, "material_id": stone.id},
        {"name": "диск_пластиковый", "shape": "disk", 
         "dimensions": {"diameter": 0.2, "thickness": 0.05}, "material_id": plastic.id},
        # Прямоугольные бруски
        {"name": "брусок_металлический", "shape": "box", 
         "dimensions": {"length": 0.052, "width": 0.042, "height": 0.05}, "material_id": metal.id},
        {"name": "брусок_каменный", "shape": "box", 
         "dimensions": {"length": 0.118, "width": 0.05, "height": 0.05}, "material_id": stone.id},
        {"name": "брусок_пластиковый", "shape": "box", 
         "dimensions": {"length": 0.115, "width": 0.053, "height": 0.05}, "material_id": plastic.id},
    ]
    
    for item in target_types_data:
        existing = db.query(models.TargetType).filter_by(name=item["name"]).first()
        if not existing:
            db.add(models.TargetType(**item))
    db.commit()
    print("Целевые объекты добавлены")

    # Антенна PlastRam (1 секция)
    antenna_data = {
        "name": "PlastRam (1 sect)",
        "frequency": 1.1e9,
        "manufacturer": "TSU / TerraZond",
        "parameters": {
            "type": "bowtie_approximation",
            "frequency_range": [0.71e9, 2.6e9],
            "impedance": 50,
            "polarization": "z",
            "beamwidth_deg": 60,
            "notes": "Based on PlastRam antenna from TerraZond GPR, one section. Designed for SFCW.",
            "source": "TerraZond_Sibercon_Plasram_rus.pdf"
        }
    }
    
    existing = db.query(models.Antenna).filter_by(name=antenna_data["name"]).first()
    if not existing:
        db.add(models.Antenna(**antenna_data))
    db.commit()
    print(" Антенна PlastRam добавлена")

    # Импульс
    pulse_data = {
        "name": "ricker_1.1GHz", 
        "waveform": "ricker", 
        "parameters": {"center_freq": 1.1e9, "amplitude": 10000.0}
    }
    
    existing = db.query(models.PulseType).filter_by(name=pulse_data["name"]).first()
    if not existing:
        db.add(models.PulseType(**pulse_data))
    db.commit()
    print("Тип импульса добавлен")
    
    print(" База данных успешно заполнена!")