# app/gprmax_generator.py
from jinja2 import Environment, FileSystemLoader
from app.config_schema import SimulationConfig
from sqlalchemy.orm import Session
from app import models
import os
import math

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates", "gprmax")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def generate_script(config: SimulationConfig, db: Session) -> str:
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

            ax, ay, az = 0, 0, 1  # default axis Z
            if rot:
                rx = math.radians(rot.x if hasattr(rot, 'x') else 0)
                ry = math.radians(rot.y if hasattr(rot, 'y') else 0)
                rz = math.radians(rot.z if hasattr(rot, 'z') else 0)
                if abs(ry) > 0.001:
                    ax = math.sin(ry)
                    az = math.cos(ry)
                if abs(rx) > 0.001:
                    ay_old = ay
                    az_old = az
                    ay = ay_old * math.cos(rx) - az_old * math.sin(rx)
                    az = ay_old * math.sin(rx) + az_old * math.cos(rx)

            half = thickness / 2.0
            # Вычисляем вертикальный размер вдоль оси Z
            vertical_half = half * abs(az)
            # Корректировка: если нижняя грань уходит в отрицательную область, сдвигаем объект вверх
            z_center = pos.z
            if z_center - vertical_half < 0:
                z_center = vertical_half  # нижняя грань станет точно на z=0
            z1 = z_center - half * az
            z2 = z_center + half * az

            obj = {
                "type": "cylinder",
                "x1": pos.x - half * ax,
                "y1": pos.y - half * ay,
                "z1": z1,
                "x2": pos.x + half * ax,
                "y2": pos.y + half * ay,
                "z2": z2,
                "radius": radius,
                "material_name": obj_material_name
            }
            objects.append(obj)

        elif shape == "box":
            length = dims.get("length", 0.1)
            width = dims.get("width", 0.05)
            height = dims.get("height", 0.05)

            eff_length, eff_width, eff_height = length, width, height
            if rot:
                rx = abs(rot.x if hasattr(rot, 'x') else 0) % 360
                ry = abs(rot.y if hasattr(rot, 'y') else 0) % 360
                rz = abs(rot.z if hasattr(rot, 'z') else 0) % 360
                if rx in [90, 270]:
                    eff_width, eff_height = eff_height, eff_width
                if ry in [90, 270]:
                    eff_length, eff_height = eff_height, eff_length
                if rz in [90, 270]:
                    eff_length, eff_width = eff_width, eff_length
                if rx in [45, 135, 225, 315]:
                    eff_width = (width + height) / math.sqrt(2)
                    eff_height = (width + height) / math.sqrt(2)
                if ry in [45, 135, 225, 315]:
                    eff_length = (length + height) / math.sqrt(2)
                    eff_height = (length + height) / math.sqrt(2)
                if rz in [45, 135, 225, 315]:
                    eff_length = (length + width) / math.sqrt(2)
                    eff_width = (length + width) / math.sqrt(2)

            half_l, half_w, half_h = eff_length/2, eff_width/2, eff_height/2
            # Корректировка Z: нижняя грань должна быть >= 0
            z_center = pos.z
            if z_center - half_h < 0:
                z_center = half_h
            obj = {
                "type": "box",
                "x1": pos.x - half_l,
                "y1": pos.y - half_w,
                "z1": z_center - half_h,
                "x2": pos.x + half_l,
                "y2": pos.y + half_w,
                "z2": z_center + half_h,
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
    num_steps = int(abs(end.x - start.x) / step) + 1 if step > 0 else 1

    soil_layer = config.soil_layers[0]
    soil_layer_bottom = soil_layer.position.z - soil_layer.thickness / 2
    soil_layer_top = soil_layer.position.z + soil_layer.thickness / 2

    # Настройки сетки и домена
    opt_dx = 0.005
    discretization = {"x": opt_dx, "y": opt_dx, "z": opt_dx}

    domain_z = max(2.0, soil_layer_top + 0.5)
    domain = {"x": 1.4, "y": 0.5, "z": round(domain_z, 2)}

    antenna_height = 0.2
    antenna_y = 0.25
    antenna_z = antenna_height
    tx_x = start.x
    rx_x = start.x + 0.05

    # Временное окно
    max_depth = max([abs(obj.get("z1", 0)) for obj in objects] +
                    [abs(obj.get("z2", 0)) for obj in objects] +
                    [abs(soil_layer_bottom)])
    t_air = 2 * antenna_height / 0.3e9
    t_soil = 2 * max_depth / 0.1e9
    t_window = max(120e-9, t_air + t_soil + 30e-9)

    pml_layers = 8

    template_vars = {
        "title": config.name,
        "domain": domain,
        "dx_dy_dz": discretization,
        "time_window": t_window,
        "pml_layers": pml_layers,
        "materials": materials,
        "waveform": {
            "type": pulse.waveform,
            "amplitude": pulse.parameters.get("amplitude", 10000.0),
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
        "antenna": {
            "tx_position": {"x": tx_x, "y": antenna_y, "z": antenna_z},
            "rx_position": {"x": rx_x, "y": antenna_y, "z": antenna_z},
        }
    }

    template = env.get_template("bscan_bowtie_template.in")
    return template.render(template_vars)