from app.database import engine, Base
from app import models

from app.models import (
    SoilType,
    Material,
    TargetType,
    Antenna,
    PulseType,
    SoilBoundary,
    ObjectPortrait
)

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы успешно")