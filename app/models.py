from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class SoilType(Base):
    __tablename__ = "soil_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=False)

class Material(Base):
    __tablename__ = "materials"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    shape = Column(String)
    drawing = Column(Text)
    material_id = Column(Integer, ForeignKey("materials.id"))
    parameters = Column(JSON, nullable=True)

    material = relationship("Material")

class TargetType(Base):
    __tablename__ = "target_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    shape = Column(String)
    drawing = Column(Text)
    material_id = Column(Integer, ForeignKey("materials.id"))
    
    material = relationship("Material")

class Antenna(Base):
    __tablename__ = "antennas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    frequency = Column(Float)
    manufacturer = Column(String)
    parameters = Column(JSON)

class PulseType(Base):
    __tablename__ = "pulse_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    waveform = Column(String)
    parameters = Column(JSON)

class SoilBoundary(Base):
    __tablename__ = "soil_boundaries"

    id = Column(Integer, primary_key=True, index=True)
    angle = Column(Float)
    roughness = Column(Float)
    humidity = Column(Float)
    soil_type_id = Column(Integer, ForeignKey("soil_types.id"))

    soil_type = relationship("SoilType")

class ObjectPortrait(Base):
    __tablename__ = "object_portraits"

    id = Column(Integer, primary_key=True, index=True)
    target_type_id = Column(Integer, ForeignKey("target_types.id"))
    soil_type_id = Column(Integer,ForeignKey("soil_types.id"))
    antenna_id = Column(Integer,ForeignKey("antennas.id"))
    pulse_id = Column(Integer,ForeignKey("pulse_types.id"))

    simulation_params = Column(JSON)
    result_file_path = Column(String)

    target_type = relationship("TargetType")
    soil_type = relationship("SoilType")
    antenna = relationship("Antenna")
    pulse = relationship("PulseType")