# Working Windows 10
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\activate
.\.venv\Scripts\activate
uvicorn app.api.main:app --reload
streamlit run app/dashboard/streamlit_app.py

# Bitacora
- Define the architecture
- Create folder basic folder skeleton
- Define entity models (DailyMetricsInput and DailyKPIsOutput)
- Define the storage and DB interfaces (ports)
- Build the API skeleton (both endpoints)
- add .gitignore (forgot)
- Start learning postgres:
    - install docker for windows amd64
    - Launch postgres server in a docker with docker compose up -d using .yml config file
    - connect, insert and read in drill 02 using psycopg with SQL strings
    - same but using SQLAlchemy Core (Not ORM) in drill 03
    - same but using SQLAlchemy ORM models DeclarativeBase etc, write using objects and read
- Code the Repository implementations (classes inherited from ports)
- Design the POST endpoint top-down. Endpoint, use case, implementations, helpers. Wiring first.