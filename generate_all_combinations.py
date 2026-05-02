# generate_all_combinations.py
import sys
import itertools
import time
from pathlib import Path

print("Скрипт запущен. Импорт модулей...")

sys.path.insert(0, str(Path(__file__).parent))

try:
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app import models
    from app.config_schema import (
        SimulationConfig, SimulationDomain, GPRConfiguration,
        GPRMovement, OutputConfiguration, Coordinate3D,
        SoilLayer, TargetObject
    )
    from app.gprmax_generator import generate_script
    print("Импорты выполнены успешно.")
except Exception as e:
    print(f"Ошибка импорта: {e}")
    sys.exit(1)


def get_ids(db: Session):
    """Получить id нужных сущностей из БД."""
    print("Получение ID из БД...")
    soil_map = {
        "песок": {
            0: db.query(models.SoilType).filter_by(name="песок_сухой").first().id,
            40: db.query(models.SoilType).filter_by(name="песок_средний").first().id,
            80: db.query(models.SoilType).filter_by(name="песок_влажный").first().id,
        },
        "глина": {
            0: db.query(models.SoilType).filter_by(name="глина_сухая").first().id,
            40: db.query(models.SoilType).filter_by(name="глина_средняя").first().id,
            80: db.query(models.SoilType).filter_by(name="глина_влажная").first().id,
        },
        "лёд": {
            0: db.query(models.SoilType).filter_by(name="лёд_сухой").first().id,
            40: db.query(models.SoilType).filter_by(name="лёд_средний").first().id,
            80: db.query(models.SoilType).filter_by(name="лёд_влажный").first().id,
        },
    }

    antenna_id = db.query(models.Antenna).filter_by(
        name="PlastRam (1 sect)"
    ).first().id

    pulse_id = db.query(models.PulseType).filter_by(
        name="ricker_1.1GHz"
    ).first().id

    target_types = {
        ("disk", "металл"): db.query(models.TargetType).filter_by(
            name="диск_металлический").first().id,
        ("disk", "камень"): db.query(models.TargetType).filter_by(
            name="диск_каменный").first().id,
        ("disk", "пластик"): db.query(models.TargetType).filter_by(
            name="диск_пластиковый").first().id,
        ("box", "металл"): db.query(models.TargetType).filter_by(
            name="брусок_металлический").first().id,
        ("box", "камень"): db.query(models.TargetType).filter_by(
            name="брусок_каменный").first().id,
        ("box", "пластик"): db.query(models.TargetType).filter_by(
            name="брусок_пластиковый").first().id,
    }

    return soil_map, antenna_id, pulse_id, target_types


def build_config(soil_type_id, target_type_id, depth_m,
                 orientation_params, name_suffix, db,
                 antenna_id, pulse_id):
    domain_z = max(2.0, depth_m + 1.0)
    domain_size = Coordinate3D(x=1.4, y=0.5, z=domain_z)
    discret = Coordinate3D(x=0.005, y=0.005, z=0.005)

    start = Coordinate3D(x=0.1, y=0.25, z=0.2)
    end   = Coordinate3D(x=1.3, y=0.25, z=0.2)
    step  = 0.04

    soil_thickness = domain_z - 0.5
    soil_center_z = soil_thickness / 2

    soil_layer = SoilLayer(
        soil_type_id=soil_type_id,
        thickness=soil_thickness,
        position=Coordinate3D(x=0.5, y=0.25, z=soil_center_z),
        boundary_params=None
    )

    target_pos = Coordinate3D(x=0.5, y=0.25, z=depth_m)

    rotation = orientation_params.get("rotation", Coordinate3D(x=0, y=0, z=0))
    target = TargetObject(
        target_type_id=target_type_id,
        position=target_pos,
        rotation=rotation,
        custom_parameters=orientation_params.get("custom_params")
    )

    config = SimulationConfig(
        name=f"sim_{name_suffix}",
        description=f"Auto-generated",
        domain=SimulationDomain(
            size=domain_size,
            pml_layers=8,
            background_soil_id=soil_type_id
        ),
        gpr_config=GPRConfiguration(
            antenna_id=antenna_id,
            pulse_id=pulse_id,
            frequency_range=[0.71e9, 2.6e9],
            time_window=50e-9,
            discretization=discret
        ),
        movement=GPRMovement(
            type="linear",
            start_point=start,
            end_point=end,
            step_size=step
        ),
        output=OutputConfiguration(
            scan_types=["A-scan", "B-scan"],
            output_format="h5",
            output_directory="./results",
            save_intermediate=False
        ),
        soil_layers=[soil_layer],
        targets=[target]
    )
    return config


def main():
    print("\n=== Запуск генерации ===")
    db = SessionLocal()
    try:
        soil_map, antenna_id, pulse_id, target_types = get_ids(db)

        soil_types = ["песок", "глина", "лёд"]
        humidities = [0, 40, 80]
        depths = [0.0, 0.5, 1.0]
        materials = ["металл", "камень", "пластик"]
        shapes = ["disk", "box"]

        orientations = {
            "disk": [
                {"name": "flat", "rotation": (0, 0, 0)},
                {"name": "tilt45", "rotation": (45, 0, 0)},
                {"name": "on_edge", "rotation": (90, 0, 0)},
                {"name": "edge_along", "rotation": (90, 0, 0), "mov_dir": "along"},
                {"name": "edge_across", "rotation": (90, 0, 90), "mov_dir": "across"},
                {"name": "edge_45deg", "rotation": (90, 0, 45), "mov_dir": "45deg"},
            ],
            "box": [
                {"name": "flat", "rotation": (0, 0, 0)},
                {"name": "on_edge", "rotation": (0, 90, 0)},
                {"name": "on_end", "rotation": (90, 0, 0)},
                {"name": "edge_along", "rotation": (0, 90, 0), "mov_dir": "along"},
                {"name": "edge_across", "rotation": (0, 90, 90), "mov_dir": "across"},
                {"name": "edge_45deg", "rotation": (0, 90, 45), "mov_dir": "45deg"},
                {"name": "rot45_xy", "rotation": (45, 45, 0)},
                {"name": "rot45_xz", "rotation": (45, 0, 45)},
                {"name": "rot45_yz", "rotation": (0, 45, 45)},
            ]
        }

        total = 0
        for soil_name, hum, shape, material, depth in itertools.product(
                soil_types, humidities, shapes, materials, depths):
            for orient in orientations[shape]:
                total += 1

        print(f"Всего комбинаций: {total}")
        saved = 0
        for soil_name, hum, shape, material, depth in itertools.product(
                soil_types, humidities, shapes, materials, depths):
            soil_id = soil_map[soil_name][hum]
            target_id = target_types[(shape, material)]
            for orient in orientations[shape]:
                rot = Coordinate3D(x=orient["rotation"][0], y=orient["rotation"][1], z=orient["rotation"][2])
                suffix = f"{soil_name}_{hum}pct_{shape}_{material}_d{depth*100:.0f}cm_{orient['name']}"
                try:
                    config = build_config(soil_id, target_id, depth, {"rotation": rot}, suffix, db, antenna_id, pulse_id)
                    script_content = generate_script(config, db)
                    db_script = models.Script(
                        name=config.name,
                        description=config.description,
                        config_json=config.model_dump(),
                        script_content=script_content,
                        status="generated"
                    )
                    db.add(db_script)
                    db.commit()
                    saved += 1
                    print(f" {saved}/{total} - {suffix}")
                except Exception as e:
                    print(f" {suffix}: {e}")
                    db.rollback()
        print("Генерация завершена.")
    finally:
        db.close()


if __name__ == "__main__":
    main()