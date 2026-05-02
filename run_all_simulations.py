# run_all_simulations.py
import requests
import time
from concurrent.futures import ThreadPoolExecutor

API_URL = "http://localhost:8000/simulate"
TOTAL_SCRIPTS = 1215        # общее количество сгенерированных скриптов
SEND_WORKERS = 20           # количество одновременных HTTP‑запросов (не путать с Celery concurrency)

def send_task(script_id):
    try:
        resp = requests.post(f"{API_URL}/{script_id}", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ {script_id:4d} -> task {data['task_id'][:8]}...")
        else:
            print(f"❌ {script_id:4d} -> HTTP {resp.status_code}: {resp.text[:50]}")
    except Exception as e:
        print(f"⚠️ {script_id:4d} -> {e}")

def main():
    print(f"🚀 Отправка {TOTAL_SCRIPTS} задач в Celery...")
    start = time.time()
    with ThreadPoolExecutor(max_workers=SEND_WORKERS) as executor:
        executor.map(send_task, range(1, TOTAL_SCRIPTS + 1))
    elapsed = time.time() - start
    print(f"\n✅ Все задачи отправлены за {elapsed:.1f} сек.")
    print("📊 Проверить очередь: redis-cli LLEN celery")

if __name__ == "__main__":
    main()