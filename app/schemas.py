from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# В этом файле описаны форматы данных для API. 
# Какие поля должны приходить в запросе и как они возвращаются в ответе.

class SoilTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any]

class SoilTypeCreate(SoilTypeBase):
    pass

class SoilTypeResponse(SoilTypeBase):
    id: int

    class Config:
        from_attributes = True

class MaterialBase(BaseModel):
    name: str
    shape: Optional[str] = None
    drawing: Optional[str] = None
    parameters: Dict[str, Any] = {}
    material_id: Optional[int] = None

class MaterialCreate(MaterialBase):
    pass

class MaterialResponse(MaterialBase):
    id: int

    class Config:
        from_attributes = True

class TargetTypeBase(BaseModel):
    name: str
    shape: str
    drawing: Optional[str] = None
    material_id: Optional[int]

class TargetTypeCreate(TargetTypeBase):
    pass

class TargetTypeResponse(TargetTypeBase):
    id: int

    class Config:
        from_attributes = True

class AntennaBase(BaseModel):
    name: str
    frequency: float
    manufacturer: Optional[str] = None
    parameters: Dict[str, Any]

class AntennaCreate(AntennaBase):
    pass

class AntennaResponse(AntennaBase):
    id: int

    class Config:
        from_attributes = True

class PulseTypeBase(BaseModel):
    name: str
    waveform: str
    parameters: Dict[str, Any]

class PulseTypeCreate(PulseTypeBase):
    pass

class PulseTypeResponse(PulseTypeBase):
    id: int

    class Config:
        from_attributes = True

class SoilBoundaryBase(BaseModel):
    angle: float
    roughness: float
    humidity: float
    soil_type_id: int

class SoilBoundaryCreate(SoilBoundaryBase):
    pass

class SoilBoundaryResponse(SoilBoundaryBase):
    id: int

    class Config:
        from_attributes = True

class ObjectPortraitBase(BaseModel):
    target_type_id: int
    soil_type_id: int
    antenna_id: int
    pulse_id: int
    simulation_params: Dict[str, Any]
    result_file_path: str

class ObjectPortraitCreate(ObjectPortraitBase):
    pass

class ObjectPortraitResponse(ObjectPortraitBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class BulkUpload(BaseModel):
    soil_types: Optional[List[SoilTypeCreate]] = None
    materials: Optional[List[MaterialCreate]] = None
    target_types: Optional[List[TargetTypeCreate]] = None
    antennas: Optional[List[AntennaCreate]] = None
    pulse_types: Optional[List[PulseTypeCreate]] = None
    soil_boundaries: Optional[List[SoilBoundaryCreate]] = None
    object_portraits: Optional[List[ObjectPortraitCreate]] = None