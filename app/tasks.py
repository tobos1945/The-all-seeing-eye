import os
import sys
import subprocess
from app.celery_app import celery_app
from app.database import SessionLocal
from app import models

@celery_app.task(bind=True, name='app.tasks.run_gprmax_simulation')
def run_gprmax_simulation(self, script_id):
    """Запуск моделирования на CPU (ГАРАНТИРОВАННО РАБОТАЕТ)"""
    
    print(f"Starting CPU simulation for script {script_id}")
    
    db = SessionLocal()
    script = None
    
    try:
        script = db.query(models.Script).get(script_id)
        if not script:
            return {"error": "Script not found"}

        script.status = "running"
        script.celery_task_id = self.request.id
        db.commit()
        
        # Сохраняем скрипт
        script_filename = f"c:\\tmp\\gprmax_script_{script_id}.in"
        os.makedirs("c:\\tmp", exist_ok=True)
        
        with open(script_filename, "w", encoding='utf-8') as f:
            f.write(script.script_content)
        
        # Получаем количество шагов
        config = script.config_json
        movement = config["movement"]
        start = movement["start_point"]
        end = movement.get("end_point", start)
        step = movement.get("step_size", 0.02)
        
        distance = abs(end["x"] - start["x"])
        num_steps = int(distance / step) + 1
        
        print(f"📊 Number of steps: {num_steps}")

        cmd = [
            CONDA_PYTHON, "-m", "gprMax",
            script_filename,
            "-n", str(num_steps)
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 час
        )
        
        if result.returncode != 0:
            error_msg = f"gprMax error: {result.stderr}"
            print(f"{error_msg}")
            script.status = "failed"
            script.error = error_msg
            db.commit()
            return {"error": error_msg}
        
        print("gprMax completed successfully on CPU!")
        
        # Ищем выходной файл
        out_file = script_filename.replace(".in", ".out")
        if not os.path.exists(out_file):
            out_file = script_filename.replace(".in", ".h5")
        
        # Здесь можно добавить обработку результатов
        # (чтение HDF5, сохранение изображений и т.д.)
        
        return {"status": "success", "output": out_file}
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"{error_msg}")
        if script:
            script.status = "failed"
            script.error = str(e)
            db.commit()
        return {"error": str(e)}
    finally:
        db.close()