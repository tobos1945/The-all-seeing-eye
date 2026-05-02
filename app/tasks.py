import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path

from app.celery_app import celery_app
from app.database import SessionLocal
from app import models

CONDA_PYTHON = sys.executable 

# Базовая директория для хранения всех результатов
RESULTS_BASE_DIR = Path("./results").absolute()

@celery_app.task(bind=True, name='app.tasks.run_gprmax_simulation')
def run_gprmax_simulation(self, script_id):
    """
    Запуск моделирования gprMax.
    После выполнения файлы сохраняются в ./results/{script_id}/
    и путь записывается в БД.
    """
    print(f" Запуск моделирования для script_id={script_id}")
    db = SessionLocal()
    script = None

    try:
        script = db.query(models.Script).get(script_id)
        if not script:
            return {"error": "Script not found"}

        # Обновляем статус
        script.status = "running"
        script.celery_task_id = self.request.id
        db.commit()

        # Создаём временную директорию для работы gprMax
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            script_filename = tmp_path / f"gprmax_script_{script_id}.in"

            with open(script_filename, "w", encoding="utf-8") as f:
                f.write(script.script_content)

            config = script.config_json
            movement = config["movement"]
            start = movement["start_point"]
            end = movement.get("end_point", start)
            step = movement.get("step_size", 0.02)
            distance = abs(end["x"] - start["x"])
            num_steps = int(distance / step) + 1 if step > 0 else 1

            # Формируем команду
            cmd = [
                CONDA_PYTHON, "-m", "gprMax",
                str(script_filename),
                "-n", str(num_steps),
                "-gpu"
            ]
            print(f" Выполняется: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,   
                cwd=str(tmp_path)      # важно, чтобы выходные файлы были в tmpdir
            )

            if result.returncode != 0:
                error_msg = f"gprMax error (code {result.returncode}): {result.stderr}"
                print(f"{error_msg}")
                script.status = "failed"
                script.error = error_msg
                db.commit()
                return {"error": error_msg}

            print("gprMax завершился успешно")

            # Ищем выходной файл (может быть .out или .h5)
            output_files = list(tmp_path.glob(f"*{script_id}*.out")) + \
                           list(tmp_path.glob(f"*{script_id}*.h5"))
            if not output_files:
                base = script_filename.stem
                output_files = list(tmp_path.glob(f"{base}*.out")) + \
                               list(tmp_path.glob(f"{base}*.h5"))

            if not output_files:
                raise FileNotFoundError("Выходной файл не найден после моделирования")

            main_output = None
            for f in output_files:
                if f.suffix == ".h5":
                    main_output = f
                    break
            if main_output is None:
                main_output = output_files[0]

            # Создаём постоянную папку для результатов этого скрипта
            result_dir = RESULTS_BASE_DIR / str(script_id)
            result_dir.mkdir(parents=True, exist_ok=True)

            # Копируем все сгенерированные файлы
            saved_files = []
            for f in output_files:
                dest = result_dir / f.name
                shutil.copy2(f, dest)
                saved_files.append(str(dest))

            script_backup = result_dir / f"script_{script_id}.in"
            shutil.copy2(script_filename, script_backup)

            log_file = result_dir / "gprmax.log"
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("STDOUT:\n" + result.stdout + "\n\nSTDERR:\n" + result.stderr)

            # Обновляем запись в БД
            script.status = "completed"
            script.error = None
            # Если есть связанный ObjectPortrait, записываем путь в него
            if script.result_portrait_id:
                portrait = db.query(models.ObjectPortrait).get(script.result_portrait_id)
                if portrait:
                    portrait.result_file_path = str(main_output.absolute())
            db.commit()

            print(f"Результаты сохранены в: {result_dir}")
            return {
                "status": "success",
                "output_files": saved_files,
                "result_directory": str(result_dir)
            }

    except subprocess.TimeoutExpired:
        error_msg = "Превышено время выполнения (1 час)"
        print(f"{error_msg}")
        if script:
            script.status = "failed"
            script.error = error_msg
            db.commit()
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Непредвиденная ошибка: {str(e)}"
        print(f"{error_msg}")
        if script:
            script.status = "failed"
            script.error = str(e)
            db.commit()
        return {"error": str(e)}
    finally:
        db.close()