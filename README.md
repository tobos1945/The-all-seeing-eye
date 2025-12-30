# The-all-seeing-eye
**The all-seeing eye**

## Что нужно сделать до
- Установить Python 3.8+
- Установить PostgreSQL
- Установить следующие библиотеки: fastapi, uvicorn, sqlalchemy, pydantic, python-dotenv, psycopg2-binary
- Сколнируйте репозиторий

## Настройка базы данных
### Установите и запустите PostgreSQL

Если базы данных нет, создайте её через следующие команды:
CREATE DATABASE gpr_database;
CREATE USER gpr_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE gpr_database TO gpr_user;

В файле .env изменить/добавить строчку DATABASE_URL=postgresql://username:password@localhost/{gpr_database}

## Запуск сервера
Запустите файл main.py (для этого в консоли можно использовать "python main.py")
Тогда сервер запуститься на  http://localhost::8000

## Работа с БД
Документация по адресу http://localhost:8000/docs - Swagger UI

### В консоле можно испольнять запросы: 
- проверить состояние сервера curl http://localhost:8000/health/
- статистика БД curl "http://localhost:8000/statistics/"
- посмотреть типы почв curl "http://localhost:8000/soil-types/"
- для массового добавления нужно создать JSON файл (пример есть в проекте "example_config.json")
  после выполнить команду curl -X POST "http://localhost:8000/bulk-upload/" -F "file=@example_config.json"

### Также можно работать через саму документацию (Swagger UI):
1) открыть http://localhost:8000/docs
2) нажать, например, на "POST /soil-types/"
3) нажать "Try it out"
4) Ввести данные и нажать "Exucute"