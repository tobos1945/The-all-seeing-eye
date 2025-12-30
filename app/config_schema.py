from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum

# В этом файле описаны правила для конфигурации моделирования георадара.
# Как должны выглядеть слои почвы, цели, настройки антенны и результаты.

class Coordinate3D(BaseModel):
    x: float
    y: float
    z: float

class SoilLayer(BaseModel):
    soil_type_id: int
    thickness: float
    position: Coordinate3D
    boundary_params: Optional[Dict[str, float]] = None

class TargetObject(BaseModel):
    target_type_id: int
    position: Coordinate3D
    rotation: Optional[Coordinate3D] = None
    material_id: Optional[int] = None
    custom_parameters: Optional[Dict[str, Any]] = None

class GPRMovement(BaseModel):
    type: str = Field("linear", regex = "^(linear|grid|custom)$")
    start_point: Coordinate3D
    end_point: Optional[Coordinate3D] = None
    step_size: float = 0.1
    trajectory: Optional[List[Coordinate3D]] = None
    speed: Optional[float] = None

class GPRConfiguration(BaseModel):
    antenna_id: int
    pulse_id: int
    frequency_range: Optional[List[float]] = None
    time_window: float
    discretization: Coordinate3D

class SimulationDomain(BaseModel):
    size: Coordinate3D
    pml_layers: int = 10
    background_soil_id: int

class OutputConfiguration(BaseModel):
    scan_types: List[str] = Field(["A-scan"], regex = "^(A-scan|B-scan|C-scan)$")
    output_format: str = Field("h5", regex = "^(h5|out|both)$")
    output_directory: Optional[str] = "./results"
    save_intermediate: bool = False

class SimulationConfig(BaseModel):
    name: str
    description: Optional[str] = None

    domain: SimulationDomain
    gpr_config: GPRConfiguration
    movement: GPRMovement
    output: OutputConfiguration

    soil_layers: List[SoilLayer]
    targets: List[TargetObject]

    custom_parameters: Optional[Dict[str, Any]] = {}

    @validator('soil_layers')
    def validate_soil_layers(cls, v):
        if not v:
            raise ValueError("At least one soil layer must be specified")
        return v
    
    @validator('gpr_config')
    def validate_frequency(cls, v, values):
        if v.frequency_range:
            if len(v.frequency_range) != 2:
                raise ValueError("Frequency range must have exactly 2 values [min, max]")
            if v.frequency_range[0] >= v.frequency_range[1]:
                raise ValueError("Minimum frequency must be less than maximum frequency")
            return v
        
class ConfigFile(BaseModel):
    version: str = "1.0"
    simulation: SimulationConfig
    metadata: Optional[Dict[str, Any]] = None