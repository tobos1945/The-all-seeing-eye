from fastapi import FastAPI
from app.database import engine, Base
from app import models
from app.api import router


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="GPR Database API",
    version="0.0.1",
    description="API для управления базой данных георадарных моделей и конфигураций"
)

app.include_router(router)

@app.get("/")
def read_root():
    return {
        "message": "GPR Database API",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "health": "/health",
            "statistics": "/stats",
            "soil_types": "/soil-types/",
            "config_validation": "/validate-config/",
            "config_template": "/config-template/"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)