import json
from typing import Dict, Any
from pathlib import Path
from app.config_schema import ConfigFile

class ConfigValidator:
    @staticmethod
    def validate_config(config_data: Dict[str, Any]) -> ConfigFile:
        try:
            config = ConfigFile(**config_data)
            return config
        except Exception as e:
            raise ValueError(f"Configuration validation error: {str(e)}")
        
    @staticmethod
    def load_from_file(file_path: Path) -> ConfigFile:
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return ConfigValidator.validate_config(config_data)
    
    @staticmethod
    def create_template() -> Dict[str, Any]:
        template = {
            "version": "1.0",
            "metadata": {
                "author": "Your Name",
                "created": "2024-01-01",
                "description": "GPR simulation configuration"
            },
            "simulation": {
                "name": "example_simulation",
                "description": "Example GPR simulation with multiple targets",
                
                "domain": {
                    "size": {"x": 2.0, "y": 2.0, "z": 1.0},
                    "pml_layers": 10,
                    "background_soil_id": 1
                },
                
                "gpr_config": {
                    "antenna_id": 1,
                    "pulse_id": 1,
                    "frequency_range": [100e6, 1000e6],
                    "time_window": 30e-9,
                    "discretization": {"x": 0.005, "y": 0.005, "z": 0.005}
                },
                
                "movement": {
                    "type": "linear",
                    "start_point": {"x": 0.1, "y": 1.0, "z": 0.05},
                    "end_point": {"x": 1.9, "y": 1.0, "z": 0.05},
                    "step_size": 0.02,
                    "speed": 0.5
                },
                
                "output": {
                    "scan_types": ["A-scan", "B-scan"],
                    "output_format": "h5",
                    "output_directory": "./results",
                    "save_intermediate": False
                },
                
                "soil_layers": [
                    {
                        "soil_type_id": 1,
                        "thickness": 0.5,
                        "position": {"x": 1.0, "y": 1.0, "z": 0.5},
                        "boundary_params": {"roughness": 0.01, "humidity": 0.1}
                    }
                ],
                
                "targets": [
                    {
                        "target_type_id": 1,
                        "position": {"x": 1.0, "y": 1.0, "z": 0.3},
                        "rotation": {"x": 0, "y": 0, "z": 0},
                        "material_id": 2
                    }
                ],
                
                "custom_parameters": {
                    "additional_flag": True,
                    "precision": "high"
                }
            }
        }
        return template