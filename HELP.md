# Working Windows 10
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\activate
.\.venv\Scripts\activate
uvicorn app.api.main:app --reload

# Bitacora
- Define the architecture
- Create folder basic folder skeleton
- Define entity models (DailyMetricsInput and DailyKPIsOutput)
- Define the storage and DB interfaces (ports)
- Build the API skeleton (both endpoints)
- add .gitignore (forgot)
- Start learning postgres:
    - install docker for windows amd64