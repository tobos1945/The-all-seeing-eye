from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, Path, APIRouter
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import json
import csv
import io

from app import models, schemas
from app.database import get_db

app = FastAPI(title="GPR Database API", version="1.0.0")
router = APIRouter()

# Здесь собраны все API-запросы для работы с базой данных — создание, чтение, обновление и удаление записей


# SoilType -------------------------------------------------------------------

@router.post("/soil-types/", response_model=schemas.SoilTypeResponse)
def create_soil_type(soil_type: schemas.SoilTypeCreate, db: Session = Depends(get_db)):
    existing = db.query(models.SoilType).filter(
        models.SoilType.name == soil_type.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Soil type with this name already exists")
    
    db_soil_type = models.SoilType(**soil_type.dict())
    db.add(db_soil_type)
    db.commit()
    db.refresh(db_soil_type)
    return db_soil_type

@router.get("/soil-types/", response_model=List[schemas.SoilTypeResponse])
def get_soil_types(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.SoilType)
    
    if name:
        query = query.filter(models.SoilType.name.ilike(f"%{name}%"))
    
    soil_types = query.offset(skip).limit(limit).all()
    return soil_types

@router.get("/soil-types/{soil_type_id}", response_model=schemas.SoilTypeResponse)
def get_soil_type(
    soil_type_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
):
    soil_type = db.query(models.SoilType).filter(models.SoilType.id == soil_type_id).first()
    if not soil_type:
        raise HTTPException(status_code=404, detail="Soil type not found")
    return soil_type

@router.put("/soil-types/{soil_type_id}", response_model=schemas.SoilTypeResponse)
def update_soil_type(
    soil_type_id: int,
    soil_type_update: schemas.SoilTypeCreate,
    db: Session = Depends(get_db)
):
    db_soil_type = db.query(models.SoilType).filter(models.SoilType.id == soil_type_id).first()
    if not db_soil_type:
        raise HTTPException(status_code=404, detail="Soil type not found")
    
    if soil_type_update.name != db_soil_type.name:
        existing = db.query(models.SoilType).filter(
            models.SoilType.name == soil_type_update.name,
            models.SoilType.id != soil_type_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Soil type with this name already exists")
    
    for key, value in soil_type_update.dict().items():
        setattr(db_soil_type, key, value)
    
    db.commit()
    db.refresh(db_soil_type)
    return db_soil_type

@router.delete("/soil-types/{soil_type_id}")
def delete_soil_type(
    soil_type_id: int,
    db: Session = Depends(get_db)
):
    db_soil_type = db.query(models.SoilType).filter(models.SoilType.id == soil_type_id).first()
    if not db_soil_type:
        raise HTTPException(status_code=404, detail="Soil type not found")
    
    boundaries = db.query(models.SoilBoundary).filter(
        models.SoilBoundary.soil_type_id == soil_type_id
    ).first()
    if boundaries:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete soil type: it is used in soil boundaries"
        )
    
    portraits = db.query(models.ObjectPortrait).filter(
        models.ObjectPortrait.soil_type_id == soil_type_id
    ).first()
    if portraits:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete soil type: it is used in object portraits"
        )
    
    db.delete(db_soil_type)
    db.commit()
    return {"message": "Soil type deleted successfully"}


# Material --------------------------------------------------------


@router.post("/materials/", response_model=schemas.MaterialResponse)
def create_material(material: schemas.MaterialCreate, db: Session = Depends(get_db)):
    if material.material_id:
        parent_material = db.query(models.Material).filter(
            models.Material.id == material.material_id
        ).first()
        if not parent_material:
            raise HTTPException(status_code=400, detail="Parent material not found")
    
    db_material = models.Material(**material.dict())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material

@router.get("/materials/", response_model=List[schemas.MaterialResponse])
def get_materials(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Material)
    
    if name:
        query = query.filter(models.Material.name.ilike(f"%{name}%"))
    
    if parent_id:
        query = query.filter(models.Material.material_id == parent_id)
    else:
        query = query.filter(models.Material.material_id == None)
    
    materials = query.offset(skip).limit(limit).all()
    return materials

@router.get("/materials/{material_id}", response_model=schemas.MaterialResponse)
def get_material(material_id: int, db: Session = Depends(get_db)):
    material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material

@router.put("/materials/{material_id}", response_model=schemas.MaterialResponse)
def update_material(
    material_id: int,
    material_update: schemas.MaterialCreate,
    db: Session = Depends(get_db)
):
    db_material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not db_material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    if material_update.material_id:
        parent_material = db.query(models.Material).filter(
            models.Material.id == material_update.material_id
        ).first()
        if not parent_material:
            raise HTTPException(status_code=400, detail="Parent material not found")
        
        if material_update.material_id == material_id:
            raise HTTPException(status_code=400, detail="Material cannot reference itself")
    
    for key, value in material_update.dict().items():
        setattr(db_material, key, value)
    
    db.commit()
    db.refresh(db_material)
    return db_material

@router.delete("/materials/{material_id}")
def delete_material(material_id: int, db: Session = Depends(get_db)):
    db_material = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not db_material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    target_types = db.query(models.TargetType).filter(
        models.TargetType.material_id == material_id
    ).first()
    if target_types:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete material: it is used in target types"
        )
    
    child_materials = db.query(models.Material).filter(
        models.Material.material_id == material_id
    ).first()
    if child_materials:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete material: it has child materials"
        )
    
    db.delete(db_material)
    db.commit()
    return {"message": "Material deleted successfully"}

# TargetType ------------------------------------------------------------

@router.post("/target-types/", response_model=schemas.TargetTypeResponse)
def create_target_type(target_type: schemas.TargetTypeCreate, db: Session = Depends(get_db)):
    material = db.query(models.Material).filter(
        models.Material.id == target_type.material_id
    ).first()
    if not material:
        raise HTTPException(status_code=400, detail="Material not found")
    
    db_target_type = models.TargetType(**target_type.dict())
    db.add(db_target_type)
    db.commit()
    db.refresh(db_target_type)
    return db_target_type

@router.get("/target-types/", response_model=List[schemas.TargetTypeResponse])
def get_target_types(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    shape: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.TargetType).options(joinedload(models.TargetType.material))
    
    if name:
        query = query.filter(models.TargetType.name.ilike(f"%{name}%"))
    
    if shape:
        query = query.filter(models.TargetType.shape == shape)
    
    target_types = query.offset(skip).limit(limit).all()
    return target_types

@router.get("/target-types/{target_type_id}", response_model=schemas.TargetTypeResponse)
def get_target_type(target_type_id: int, db: Session = Depends(get_db)):
    target_type = db.query(models.TargetType).options(
        joinedload(models.TargetType.material)
    ).filter(models.TargetType.id == target_type_id).first()
    
    if not target_type:
        raise HTTPException(status_code=404, detail="Target type not found")
    return target_type

@router.put("/target-types/{target_type_id}", response_model=schemas.TargetTypeResponse)
def update_target_type(
    target_type_id: int,
    target_type_update: schemas.TargetTypeCreate,
    db: Session = Depends(get_db)
):
    db_target_type = db.query(models.TargetType).filter(
        models.TargetType.id == target_type_id
    ).first()
    
    if not db_target_type:
        raise HTTPException(status_code=404, detail="Target type not found")
    
    if target_type_update.material_id:
        material = db.query(models.Material).filter(
            models.Material.id == target_type_update.material_id
        ).first()
        if not material:
            raise HTTPException(status_code=400, detail="Material not found")

    for key, value in target_type_update.dict().items():
        setattr(db_target_type, key, value)
    
    db.commit()
    db.refresh(db_target_type)
    return db_target_type

@router.delete("/target-types/{target_type_id}")
def delete_target_type(target_type_id: int, db: Session = Depends(get_db)):
    db_target_type = db.query(models.TargetType).filter(
        models.TargetType.id == target_type_id
    ).first()
    
    if not db_target_type:
        raise HTTPException(status_code=404, detail="Target type not found")

    portraits = db.query(models.ObjectPortrait).filter(
        models.ObjectPortrait.target_type_id == target_type_id
    ).first()
    if portraits:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete target type: it is used in object portraits"
        )
    
    db.delete(db_target_type)
    db.commit()
    return {"message": "Target type deleted successfully"}

# Antenna -------------------------------------------------------------

@router.post("/antennas/", response_model=schemas.AntennaResponse)
def create_antenna(antenna: schemas.AntennaCreate, db: Session = Depends(get_db)):
    db_antenna = models.Antenna(**antenna.dict())
    db.add(db_antenna)
    db.commit()
    db.refresh(db_antenna)
    return db_antenna

@router.get("/antennas/", response_model=List[schemas.AntennaResponse])
def get_antennas(
    skip: int = 0,
    limit: int = 100,
    manufacturer: Optional[str] = None,
    min_frequency: Optional[float] = None,
    max_frequency: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Antenna)
    
    if manufacturer:
        query = query.filter(models.Antenna.manufacturer.ilike(f"%{manufacturer}%"))
    
    if min_frequency:
        query = query.filter(models.Antenna.frequency >= min_frequency)
    
    if max_frequency:
        query = query.filter(models.Antenna.frequency <= max_frequency)
    
    antennas = query.offset(skip).limit(limit).all()
    return antennas

@router.get("/antennas/{antenna_id}", response_model=schemas.AntennaResponse)
def get_antenna(antenna_id: int, db: Session = Depends(get_db)):
    antenna = db.query(models.Antenna).filter(models.Antenna.id == antenna_id).first()
    if not antenna:
        raise HTTPException(status_code=404, detail="Antenna not found")
    return antenna

@router.put("/antennas/{antenna_id}", response_model=schemas.AntennaResponse)
def update_antenna(
    antenna_id: int,
    antenna_update: schemas.AntennaCreate,
    db: Session = Depends(get_db)
):
    db_antenna = db.query(models.Antenna).filter(models.Antenna.id == antenna_id).first()
    if not db_antenna:
        raise HTTPException(status_code=404, detail="Antenna not found")
    
    for key, value in antenna_update.dict().items():
        setattr(db_antenna, key, value)
    
    db.commit()
    db.refresh(db_antenna)
    return db_antenna

@router.delete("/antennas/{antenna_id}")
def delete_antenna(antenna_id: int, db: Session = Depends(get_db)):
    db_antenna = db.query(models.Antenna).filter(models.Antenna.id == antenna_id).first()
    if not db_antenna:
        raise HTTPException(status_code=404, detail="Antenna not found")
    
    portraits = db.query(models.ObjectPortrait).filter(
        models.ObjectPortrait.antenna_id == antenna_id
    ).first()
    if portraits:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete antenna: it is used in object portraits"
        )
    
    db.delete(db_antenna)
    db.commit()
    return {"message": "Antenna deleted successfully"}

# PulseType ---------------------------------------------------------------

@router.post("/pulse-types/", response_model=schemas.PulseTypeResponse)
def create_pulse_type(pulse_type: schemas.PulseTypeCreate, db: Session = Depends(get_db)):
    db_pulse_type = models.PulseType(**pulse_type.dict())
    db.add(db_pulse_type)
    db.commit()
    db.refresh(db_pulse_type)
    return db_pulse_type

@router.get("/pulse-types/", response_model=List[schemas.PulseTypeResponse])
def get_pulse_types(
    skip: int = 0,
    limit: int = 100,
    waveform: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.PulseType)
    
    if waveform:
        query = query.filter(models.PulseType.waveform == waveform)
    
    pulse_types = query.offset(skip).limit(limit).all()
    return pulse_types

@router.get("/pulse-types/{pulse_type_id}", response_model=schemas.PulseTypeResponse)
def get_pulse_type(pulse_type_id: int, db: Session = Depends(get_db)):
    pulse_type = db.query(models.PulseType).filter(
        models.PulseType.id == pulse_type_id
    ).first()
    if not pulse_type:
        raise HTTPException(status_code=404, detail="Pulse type not found")
    return pulse_type

@router.put("/pulse-types/{pulse_type_id}", response_model=schemas.PulseTypeResponse)
def update_pulse_type(
    pulse_type_id: int,
    pulse_type_update: schemas.PulseTypeCreate,
    db: Session = Depends(get_db)
):
    db_pulse_type = db.query(models.PulseType).filter(
        models.PulseType.id == pulse_type_id
    ).first()
    if not db_pulse_type:
        raise HTTPException(status_code=404, detail="Pulse type not found")
    
    for key, value in pulse_type_update.dict().items():
        setattr(db_pulse_type, key, value)
    
    db.commit()
    db.refresh(db_pulse_type)
    return db_pulse_type

@router.delete("/pulse-types/{pulse_type_id}")
def delete_pulse_type(pulse_type_id: int, db: Session = Depends(get_db)):
    db_pulse_type = db.query(models.PulseType).filter(
        models.PulseType.id == pulse_type_id
    ).first()
    if not db_pulse_type:
        raise HTTPException(status_code=404, detail="Pulse type not found")

    portraits = db.query(models.ObjectPortrait).filter(
        models.ObjectPortrait.pulse_id == pulse_type_id
    ).first()
    if portraits:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete pulse type: it is used in object portraits"
        )
    
    db.delete(db_pulse_type)
    db.commit()
    return {"message": "Pulse type deleted successfully"}

# SoilBoundary ------------------------------------------------------------------

@router.post("/soil-boundaries/", response_model=schemas.SoilBoundaryResponse)
def create_soil_boundary(
    soil_boundary: schemas.SoilBoundaryCreate, 
    db: Session = Depends(get_db)
):
    soil_type = db.query(models.SoilType).filter(
        models.SoilType.id == soil_boundary.soil_type_id
    ).first()
    if not soil_type:
        raise HTTPException(status_code=400, detail="Soil type not found")
    
    db_soil_boundary = models.SoilBoundary(**soil_boundary.dict())
    db.add(db_soil_boundary)
    db.commit()
    db.refresh(db_soil_boundary)
    return db_soil_boundary

@router.get("/soil-boundaries/", response_model=List[schemas.SoilBoundaryResponse])
def get_soil_boundaries(
    skip: int = 0,
    limit: int = 100,
    soil_type_id: Optional[int] = None,
    min_angle: Optional[float] = None,
    max_angle: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.SoilBoundary).options(
        joinedload(models.SoilBoundary.soil_type)
    )
    
    if soil_type_id:
        query = query.filter(models.SoilBoundary.soil_type_id == soil_type_id)
    
    if min_angle:
        query = query.filter(models.SoilBoundary.angle >= min_angle)
    
    if max_angle:
        query = query.filter(models.SoilBoundary.angle <= max_angle)
    
    soil_boundaries = query.offset(skip).limit(limit).all()
    return soil_boundaries

@router.get("/soil-boundaries/{boundary_id}", response_model=schemas.SoilBoundaryResponse)
def get_soil_boundary(boundary_id: int, db: Session = Depends(get_db)):
    soil_boundary = db.query(models.SoilBoundary).options(
        joinedload(models.SoilBoundary.soil_type)
    ).filter(models.SoilBoundary.id == boundary_id).first()
    
    if not soil_boundary:
        raise HTTPException(status_code=404, detail="Soil boundary not found")
    return soil_boundary

@router.put("/soil-boundaries/{boundary_id}", response_model=schemas.SoilBoundaryResponse)
def update_soil_boundary(
    boundary_id: int,
    soil_boundary_update: schemas.SoilBoundaryCreate,
    db: Session = Depends(get_db)
):
    db_soil_boundary = db.query(models.SoilBoundary).filter(
        models.SoilBoundary.id == boundary_id
    ).first()
    
    if not db_soil_boundary:
        raise HTTPException(status_code=404, detail="Soil boundary not found")
    
    if soil_boundary_update.soil_type_id:
        soil_type = db.query(models.SoilType).filter(
            models.SoilType.id == soil_boundary_update.soil_type_id
        ).first()
        if not soil_type:
            raise HTTPException(status_code=400, detail="Soil type not found")
    
    for key, value in soil_boundary_update.dict().items():
        setattr(db_soil_boundary, key, value)
    
    db.commit()
    db.refresh(db_soil_boundary)
    return db_soil_boundary

@router.delete("/soil-boundaries/{boundary_id}")
def delete_soil_boundary(boundary_id: int, db: Session = Depends(get_db)):
    db_soil_boundary = db.query(models.SoilBoundary).filter(
        models.SoilBoundary.id == boundary_id
    ).first()
    
    if not db_soil_boundary:
        raise HTTPException(status_code=404, detail="Soil boundary not found")
    
    db.delete(db_soil_boundary)
    db.commit()
    return {"message": "Soil boundary deleted successfully"}

# ObjectPortrait

@router.post("/object-portraits/", response_model=schemas.ObjectPortraitResponse)
def create_object_portrait(
    portrait: schemas.ObjectPortraitCreate, 
    db: Session = Depends(get_db)
):
    checks = [
        (models.TargetType, portrait.target_type_id, "Target type"),
        (models.SoilType, portrait.soil_type_id, "Soil type"),
        (models.Antenna, portrait.antenna_id, "Antenna"),
        (models.PulseType, portrait.pulse_id, "Pulse type"),
    ]
    
    for model, id_value, name in checks:
        if not db.query(model).filter(model.id == id_value).first():
            raise HTTPException(status_code=400, detail=f"{name} not found")
    
    db_portrait = models.ObjectPortrait(**portrait.dict())
    db.add(db_portrait)
    db.commit()
    db.refresh(db_portrait)
    return db_portrait

@router.get("/object-portraits/", response_model=List[schemas.ObjectPortraitResponse])
def get_object_portraits(
    skip: int = 0,
    limit: int = 100,
    target_type_id: Optional[int] = None,
    soil_type_id: Optional[int] = None,
    antenna_id: Optional[int] = None,
    pulse_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.ObjectPortrait).options(
        joinedload(models.ObjectPortrait.target_type),
        joinedload(models.ObjectPortrait.soil_type),
        joinedload(models.ObjectPortrait.antenna),
        joinedload(models.ObjectPortrait.pulse)
    )
    
    if target_type_id:
        query = query.filter(models.ObjectPortrait.target_type_id == target_type_id)
    
    if soil_type_id:
        query = query.filter(models.ObjectPortrait.soil_type_id == soil_type_id)
    
    if antenna_id:
        query = query.filter(models.ObjectPortrait.antenna_id == antenna_id)
    
    if pulse_id:
        query = query.filter(models.ObjectPortrait.pulse_id == pulse_id)
    
    portraits = query.offset(skip).limit(limit).all()
    return portraits

@router.get("/object-portraits/{portrait_id}", response_model=schemas.ObjectPortraitResponse)
def get_object_portrait(portrait_id: int, db: Session = Depends(get_db)):
    portrait = db.query(models.ObjectPortrait).options(
        joinedload(models.ObjectPortrait.target_type),
        joinedload(models.ObjectPortrait.soil_type),
        joinedload(models.ObjectPortrait.antenna),
        joinedload(models.ObjectPortrait.pulse)
    ).filter(models.ObjectPortrait.id == portrait_id).first()
    
    if not portrait:
        raise HTTPException(status_code=404, detail="Object portrait not found")
    return portrait

@router.put("/object-portraits/{portrait_id}", response_model=schemas.ObjectPortraitResponse)
def update_object_portrait(
    portrait_id: int,
    portrait_update: schemas.ObjectPortraitCreate,
    db: Session = Depends(get_db)
):
    db_portrait = db.query(models.ObjectPortrait).filter(
        models.ObjectPortrait.id == portrait_id
    ).first()
    
    if not db_portrait:
        raise HTTPException(status_code=404, detail="Object portrait not found")
    
    checks = [
        (models.TargetType, portrait_update.target_type_id, "Target type"),
        (models.SoilType, portrait_update.soil_type_id, "Soil type"),
        (models.Antenna, portrait_update.antenna_id, "Antenna"),
        (models.PulseType, portrait_update.pulse_id, "Pulse type"),
    ]
    
    for model, id_value, name in checks:
        if id_value != getattr(db_portrait, f"{name.lower().replace(' ', '_')}_id"):
            if not db.query(model).filter(model.id == id_value).first():
                raise HTTPException(status_code=400, detail=f"{name} not found")
    
    for key, value in portrait_update.dict().items():
        setattr(db_portrait, key, value)
    
    db.commit()
    db.refresh(db_portrait)
    return db_portrait

@router.delete("/object-portraits/{portrait_id}")
def delete_object_portrait(portrait_id: int, db: Session = Depends(get_db)):
    db_portrait = db.query(models.ObjectPortrait).filter(
        models.ObjectPortrait.id == portrait_id
    ).first()
    
    if not db_portrait:
        raise HTTPException(status_code=404, detail="Object portrait not found")
    
    
    db.delete(db_portrait)
    db.commit()
    return {"message": "Object portrait deleted successfully"}

# bulk-upload (для всех сущностей) ----------------------------------------------------------

@router.post("/bulk-upload/")
async def bulk_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read()
        data = json.loads(content)
        bulk_data = schemas.BulkUpload(**data)
        
        results = {}
        
        if bulk_data.soil_types:
            for soil_type in bulk_data.soil_types:
                db_soil_type = models.SoilType(**soil_type.dict())
                db.add(db_soil_type)
            db.commit()
            results["soil_types"] = f"Added {len(bulk_data.soil_types)} soil types"
        
        if bulk_data.materials:
            for material in bulk_data.materials:
                if material.material_id:
                    parent = db.query(models.Material).filter(
                        models.Material.id == material.material_id
                    ).first()
                    if not parent:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Parent material {material.material_id} not found"
                        )
                
                db_material = models.Material(**material.dict())
                db.add(db_material)
            db.commit()
            results["materials"] = f"Added {len(bulk_data.materials)} materials"

        if bulk_data.target_types:
            for target_type in bulk_data.target_types:
                if target_type.material_id:
                    material = db.query(models.Material).filter(
                        models.Material.id == target_type.material_id
                    ).first()
                    if not material:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Material {target_type.material_id} not found"
                        )
                
                db_target_type = models.TargetType(**target_type.dict())
                db.add(db_target_type)
            db.commit()
            results["target_types"] = f"Added {len(bulk_data.target_types)} target types"

        if bulk_data.antennas:
            for antenna in bulk_data.antennas:
                db_antenna = models.Antenna(**antenna.dict())
                db.add(db_antenna)
            db.commit()
            results["antennas"] = f"Added {len(bulk_data.antennas)} antennas"

        if bulk_data.pulse_types:
            for pulse_type in bulk_data.pulse_types:
                db_pulse_type = models.PulseType(**pulse_type.dict())
                db.add(db_pulse_type)
            db.commit()
            results["pulse_types"] = f"Added {len(bulk_data.pulse_types)} pulse types"

        if bulk_data.soil_boundaries:
            for boundary in bulk_data.soil_boundaries:
                soil_type = db.query(models.SoilType).filter(
                    models.SoilType.id == boundary.soil_type_id
                ).first()
                if not soil_type:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Soil type {boundary.soil_type_id} not found"
                    )
                
                db_boundary = models.SoilBoundary(**boundary.dict())
                db.add(db_boundary)
            db.commit()
            results["soil_boundaries"] = f"Added {len(bulk_data.soil_boundaries)} soil boundaries"

        if bulk_data.object_portraits:
            for portrait in bulk_data.object_portraits:
                checks = [
                    (models.TargetType, portrait.target_type_id, "Target type"),
                    (models.SoilType, portrait.soil_type_id, "Soil type"),
                    (models.Antenna, portrait.antenna_id, "Antenna"),
                    (models.PulseType, portrait.pulse_id, "Pulse type"),
                ]
                
                for model, id_value, name in checks:
                    if not db.query(model).filter(model.id == id_value).first():
                        raise HTTPException(
                            status_code=400, 
                            detail=f"{name} {id_value} not found"
                        )
                
                db_portrait = models.ObjectPortrait(**portrait.dict())
                db.add(db_portrait)
            db.commit()
            results["object_portraits"] = f"Added {len(bulk_data.object_portraits)} object portraits"
        
        return {
            "message": "Bulk upload completed successfully",
            "results": results,
            "total_records": sum(len(lst) for lst in [
                bulk_data.soil_types or [],
                bulk_data.materials or [],
                bulk_data.target_types or [],
                bulk_data.antennas or [],
                bulk_data.pulse_types or [],
                bulk_data.soil_boundaries or [],
                bulk_data.object_portraits or []
            ])
        }
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# CVS Добавление ---------------------------------------------------------------

@router.post("/import-csv/")
async def import_csv(
    file: UploadFile = File(...), 
    entity_type: str = Query(..., pattern="^(soil_types|materials|target_types|antennas|pulse_types|soil_boundaries|object_portraits)$"),
    db: Session = Depends(get_db)
):
    import csv
    import io
    
    content = await file.read()
    csv_content = io.StringIO(content.decode('utf-8'))
    csv_reader = csv.DictReader(csv_content)
    
    records_added = 0
    errors = []
    
    for row_num, row in enumerate(csv_reader, 1):
        try:
            json_fields = ['parameters', 'simulation_params']
            for field in json_fields:
                if field in row and row[field]:
                    try:
                        row[field] = json.loads(row[field])
                    except json.JSONDecodeError:
                        raise ValueError(f"Invalid JSON in field '{field}'")
            
            for key, value in row.items():
                if value == '':
                    row[key] = None
                elif key in ['id', 'material_id', 'soil_type_id', 'target_type_id', 
                           'antenna_id', 'pulse_id'] and value:
                    row[key] = int(value)
                elif key in ['angle', 'roughness', 'humidity', 'frequency'] and value:
                    row[key] = float(value)

            if entity_type == "soil_types":
                db_item = models.SoilType(**row)
            elif entity_type == "materials":
                db_item = models.Material(**row)
            elif entity_type == "target_types":
                db_item = models.TargetType(**row)
            elif entity_type == "antennas":
                db_item = models.Antenna(**row)
            elif entity_type == "pulse_types":
                db_item = models.PulseType(**row)
            elif entity_type == "soil_boundaries":
                db_item = models.SoilBoundary(**row)
            elif entity_type == "object_portraits":
                db_item = models.ObjectPortrait(**row)
            
            db.add(db_item)
            records_added += 1
            
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
            continue
    
    db.commit()
    
    return {
        "message": f"Imported {records_added} {entity_type} from CSV",
        "errors": errors if errors else "No errors",
        "successful": records_added,
        "failed": len(errors)
    }

# Эндпоинты для статистики и поиска ----------------------------------

@router.get("/statistics/")
def get_statistics(db: Session = Depends(get_db)):
    """Получение статистики по всем сущностям"""
    stats = {
        "soil_types": db.query(models.SoilType).count(),
        "materials": db.query(models.Material).count(),
        "target_types": db.query(models.TargetType).count(),
        "antennas": db.query(models.Antenna).count(),
        "pulse_types": db.query(models.PulseType).count(),
        "soil_boundaries": db.query(models.SoilBoundary).count(),
        "object_portraits": db.query(models.ObjectPortrait).count(),
    }
    
    return {
        "message": "Database statistics",
        "statistics": stats,
        "total": sum(stats.values())
    }

@router.get("/search/")
def search_entities(
    query: str = Query(..., min_length=2),
    db: Session = Depends(get_db)
):
    """Поиск по всем сущностям"""
    results = {}

    soil_results = db.query(models.SoilType).filter(
        models.SoilType.name.ilike(f"%{query}%") |
        models.SoilType.description.ilike(f"%{query}%")
    ).limit(10).all()
    if soil_results:
        results["soil_types"] = [
            {"id": s.id, "name": s.name, "description": s.description[:100] if s.description else ""}
            for s in soil_results
        ]

    material_results = db.query(models.Material).filter(
        models.Material.name.ilike(f"%{query}%")
    ).limit(10).all()
    if material_results:
        results["materials"] = [
            {"id": m.id, "name": m.name}
            for m in material_results
        ]

    target_results = db.query(models.TargetType).filter(
        models.TargetType.name.ilike(f"%{query}%")
    ).limit(10).all()
    if target_results:
        results["target_types"] = [
            {"id": t.id, "name": t.name, "shape": t.shape}
            for t in target_results
        ]
    
    return {
        "query": query,
        "results": results,
        "total_results": sum(len(r) for r in results.values())
    }

# Health check и корневой эндпоинт ------------------------------

@router.get("/")
def read_root():
    return {
        "message": "GPR Database API",
        "version": "1.0.0",
        "endpoints": {
            "soil_types": "/soil-types/",
            "materials": "/materials/",
            "target_types": "/target-types/",
            "antennas": "/antennas/",
            "pulse_types": "/pulse-types/",
            "soil_boundaries": "/soil-boundaries/",
            "object_portraits": "/object-portraits/",
            "bulk_upload": "/bulk-upload/",
            "import_csv": "/import-csv/",
            "statistics": "/statistics/",
            "search": "/search/",
            "health": "/health/"
        }
    }

@router.get("/health/")
def health_check(db: Session = Depends(get_db)):
    """Проверка работоспособности API и БД"""
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))

        tables = [
            "soil_types", "materials", "target_types", 
            "antennas", "pulse_types", "soil_boundaries", "object_portraits"
        ]
        
        counts = {}
        for table in tables:
            count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            counts[table] = count
        
        return {
            "status": "healthy",
            "database": "connected",
            "table_counts": counts
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")