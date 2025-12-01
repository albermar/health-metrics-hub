# System for analyzing health habits and physical performance.

Based on daily metrics such as steps, calories consumed and burned, weight, body measurements, and sleep, the system will compute key fitness KPIs, trends, adherence levels and maybe other metrics and show it in a dashboard

- *Backend*: it will receive data (via CSV), process it, compute KPIs using pandas, store it persistently in a PostgreSQL database, and expose endpoints for data retrieval.
- *Visual dashboard*: it will display metrics, KPIs, and time-series insights through a clear and interactive interface, enabling users to visualize the evolution of their performance and health habits.

- Backend built with FastAPI, following Clean Architecture (domain, business, infra, api, interfaces, etc.)
- POST endpoint to upload a CSV with fitness metrics (steps, kcal, weight, sleep, etc.), protected with an API key
- ETL and KPI computation using pandas (deficit, adherence, trends, rolling averages, and any additional meaningful indicators)
- Persistent storage in PostgreSQL using SQLAlchemy (ORM/models) and Alembic (schema migrations/changes)
- Logging with loguru (requests, ETL processes, errors, execution times)
- Docker + docker-compose to run the backend and PostgreSQL as connected services
- Backend deployed on Render, with environment variables for the API key and database connection
- Dashboard built with Streamlit, deployed on Hugging Face Spaces, consuming the public API hosted on Render
- CI setup with GitHub Actions (automated test execution on every push/pull request)
- Work across multiple environments (laptop, desktop, iPad, GitHub Codespaces) to practice consistent Git workflows and terminal-based Git operations

## Clean Architecture

### Domain

Defines what the system does (not how).

Core business entities: DailyInput, DailyKPI
Interfaces 
    Repository Ports: DailyMetricsRepository, DailyKPIRepository
    File storage: InputFileStorage 

### Business

Implements the application workflows and KPI logic
Depends on *Domain* and it's abstract references, not on concrete DB or file system

- Use cases and services
    - upload_csv
    - get_kpis (for a given date range)
- ETL logic
    - CSV --> DataFrame --> List[DailyInput]
    - computationKPI --> List[DailyKPI]
- Some rules
    - How to handle duplicated date rows
    - How to handle missing values, rolling windows, etc.

### Infrastructure

This is where the app talks to the outside world: PostgreSQL, filesystem, etc.

- Database setup & models
    - SQLAlchemy models
    - DB engine and session management
- Repository implementations (adapters):
    - PostgresDailyMetricsRepository → implements DailyMetricsRepository
    - PostgresDailyKpiRepository → implements DailyKpiRepository
- File storage implementations:
    - LocalInputFileStorage implementing InputFileStorage
        - save raw uploads into input_files/
        - move processed files to input_files/processed/
        - move invalid files to input_files/unprocessable/
- Migrations (alembic)

### API layer

Turns http requests into calls to use cases and return DataTransferObject (DTOs) as JSON

- FastAPI application main.py
- Schemas: pydantic for input / output
- Routers & Endpoints
    - POST /upload_csv (receives CSV, checks Authentication KEY, calls use case upload_csv)
    - GET /kpis (sends KPIs for a given date range)




