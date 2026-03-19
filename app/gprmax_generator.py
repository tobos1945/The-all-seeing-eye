from jinja2 import Environment, FileSystemLoader
from app.config_schema import SimulationConfig
from sqlalchemy.orm import Session
from app import models
import os
import math

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates", "gprmax")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def generate_script(config: SimulationConfig, db: Session) -> str:
    """
    Генерация скрипта gprMax на основе конфигурации и данных из БД
    """
    soil_type = db.query(models.SoilType).get(config.soil_layers[0].soil_type_id)
    if not soil_type:
        raise ValueError(f"Soil type id {config.soil_layers[0].soil_type_id} not found")
    
    antenna = db.query(models.Antenna).get(config.gpr_config.antenna_id)
    if not antenna:
        raise ValueError(f"Antenna id {config.gpr_config.antenna_id} not found")
    
    pulse = db.query(models.PulseType).get(config.gpr_config.pulse_id)
    if not pulse:
        raise ValueError(f"Pulse id {config.gpr_config.pulse_id} not found")

    soil_params = soil_type.parameters
    soil_material = {
        "name": f"soil_{soil_type.id}",
        "epsilon": soil_params.get("epsilon", 5.0),
        "sigma": soil_params.get("sigma", 0.001),
        "mu": 1.0,
        "mag_loss": 0.0
    }

    objects = []
    materials_dict = {soil_material["name"]: soil_material}

    for target_obj in config.targets:
        target_type = db.query(models.TargetType).get(target_obj.target_type_id)
        if not target_type:
            raise ValueError(f"Target type id {target_obj.target_type_id} not found")
        material = db.query(models.Material).get(target_type.material_id)
        if not material:
            raise ValueError(f"Material id {target_type.material_id} not found")

        obj_material_name = f"mat_{target_type.id}"
        obj_params = material.parameters
        obj_material = {
            "name": obj_material_name,
            "epsilon": obj_params.get("epsilon", 4.0),
            "sigma": obj_params.get("sigma", 0.0),
            "mu": 1.0,
            "mag_loss": 0.0
        }
        materials_dict[obj_material_name] = obj_material

        shape = target_type.shape.lower()
        dims = target_type.dimensions or {}
        pos = target_obj.position
        rot = target_obj.rotation

        if shape == "disk":
            diameter = dims.get("diameter", 0.1)
            thickness = dims.get("thickness", 0.05)
            radius = diameter / 2.0

            # Определяем ось цилиндра на основе углов поворота
            # По умолчанию ось Z (диск плашмя)
            ax, ay, az = 0, 0, 1
            
            # Проверяем, есть ли rotation и его атрибуты
            if rot:
                if hasattr(rot, 'x') and abs(rot.x) == 90:
                    ax, ay, az = 1, 0, 0
                elif hasattr(rot, 'y') and abs(rot.y) == 90:
                    ax, ay, az = 0, 1, 0

            half = thickness / 2.0
            obj = {
                "type": "cylinder",
                "x1": pos.x - half * ax,
                "y1": pos.y - half * ay,
                "z1": pos.z - half * az,
                "x2": pos.x + half * ax,
                "y2": pos.y + half * ay,
                "z2": pos.z + half * az,
                "radius": radius,
                "material_name": obj_material_name
            }
            objects.append(obj)

        elif shape == "box":
            length = dims.get("length", 0.1)
            width = dims.get("width", 0.05)
            height = dims.get("height", 0.05)

            # Упрощённый поворот вокруг Z (кратно 90°)
            rot_z = 0
            if rot and hasattr(rot, 'z'):
                rot_z = rot.z % 360
            
            if rot_z in [90, 270]:
                length, width = width, length

            half_l, half_w, half_h = length/2, width/2, height/2
            obj = {
                "type": "box",
                "x1": pos.x - half_l,
                "y1": pos.y - half_w,
                "z1": pos.z - half_h,
                "x2": pos.x + half_l,
                "y2": pos.y + half_w,
                "z2": pos.z + half_h,
                "material_name": obj_material_name
            }
            objects.append(obj)

        else:
            raise ValueError(f"Unsupported shape: {shape}")

    materials = list(materials_dict.values())

    mov = config.movement
    start = mov.start_point
    end = mov.end_point or start
    step = mov.step_size
    num_steps = int(abs(end.x - start.x) / step) + 1

    soil_layer = config.soil_layers[0]
    soil_layer_bottom = soil_layer.position.z - soil_layer.thickness / 2
    soil_layer_top = soil_layer.position.z + soil_layer.thickness / 2

    antenna_params = antenna.parameters
    
    template_vars = {
        "title": config.name,
        "domain": config.domain.size.dict(),
        "dx_dy_dz": config.gpr_config.discretization.dict(),
        "time_window": config.gpr_config.time_window,
        "materials": materials,
        "waveform": {
            "type": pulse.waveform,
            "amplitude": pulse.parameters.get("amplitude", 1.0),
            "freq": pulse.parameters.get("center_freq", 1.1e9),
            "name": f"wave_{pulse.id}"
        },
        "src_steps": {"x": step, "y": 0, "z": 0},
        "rx_steps": {"x": step, "y": 0, "z": 0},
        "num_steps": num_steps,
        "objects": objects,
        "soil_material_name": soil_material["name"],
        "soil_layer_bottom": soil_layer_bottom,
        "soil_layer_top": soil_layer_top,
    }
    
    # Настройка антенны
    if "PlastRam" in antenna.name:
        template_vars["antenna"] = {
            "type": "dipole",
            "polarization": antenna_params.get("polarization", "z"),
            "tx_position": {"x": start.x, "y": start.y, "z": start.z},
            "rx_position": {"x": start.x + 0.05, "y": start.y, "z": start.z},
        }
    else:
        template_vars["antenna"] = {
            "type": "dipole",
            "polarization": "z",
            "tx_position": {"x": start.x, "y": start.y, "z": start.z},
            "rx_position": {"x": start.x + 0.05, "y": start.y, "z": start.z},
        }

    # Выбор шаблона
    template = env.get_template("bscan_bowtie_template.in")
    return template.render(template_vars)