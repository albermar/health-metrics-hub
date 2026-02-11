# System for analyzing health habits and physical performance.

Using daily metrics (steps, calories in/out, weight, measurements, and sleep), the system computes fitness KPIs, trends, and adherence metrics, and displays them in a dashboard

- *Backend*: it will receive data (via CSV), process it, compute KPIs using pandas, store it persistently in a PostgreSQL database, and expose endpoints for data retrieval.
- *Visual dashboard*: it will display metrics, KPIs, and time-series insights through a clear and interactive interface, enabling users to visualize the evolution of their performance and health habits.

- Backend built with FastAPI, following Clean Architecture (domain, business, infra, api, interfaces, etc.)
- POST endpoint to upload a CSV with fitness metrics (steps, kcal, weight, sleep, etc.)
- ETL and KPI computation (deficit, adherence, trends, rolling averages, and any additional meaningful indicators)
- Persistent storage in PostgreSQL using SQLAlchemy (ORM/models) and Alembic (schema migrations/changes)
- Docker + docker-compose to run the backend and PostgreSQL as connected services
- Backend deployed on Render, with environment variables for the API key and database connection
- Dashboard built with Streamlit, deployed on Hugging Face Spaces, consuming the public API hosted on Render

## Clean Architecture

### Domain

Defines what the system does (not how).

* Core business entities: DailyInput, DailyKPI
* Interfaces
    * Ports Repository: DailyMetricsRepository, DailyKPIRepository
    * Ports File storage: InputFileStorage 

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


---



# Health Metrics Hub — Backend System

Health Metrics Hub is a backend system that ingests daily health and fitness data via CSV, computes derived KPIs and trends, stores them persistently (both inputs and KPIs), and exposes a clean API for analytics and visualization.

The project focuses on data ingestion, domain-driven business logic, and backend architecture, handling real-world concerns such as missing data, rolling windows, and idempotent updates. It is designed as a portfolio-grade backend project rather than a UI-centric application.

## Key Features
- CSV ingestion of daily health and fitness metrics
- Idempotent upsert of daily records (re-uploads overwrite existing days)
- ETL pipeline with validation and normalization
- KPI computation:
    - energy balance and rolling 7-day averages
    - steps adherence
    - weight and waist trends
- Handling of missing days and incomplete data
- Persistent storage using PostgreSQL
- Read-only Streamlit dashboard consuming the public API
- Fully tested domain logic, use cases, and API endpoints

## Tech Stack

- Backend API: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy 2.0
- Schema migrations: Alembic
- Data ingestion: CSV parsing with Python standard library
- Dashboard: Streamlit (read-only, API consumer)
- Local infrastructure: Docker & Docker Compose (PostgreSQL)
- Testing: pytest (unit, use-case, and API tests)
- Configuration: environment variables via python-dotenv

## Architecture Overview

The project follows Clean Architecture, keeping business logic independent from frameworks, databases, and delivery mechanisms.

**Domain**

Core entities representing daily metrics and computed KPIs

Interfaces defining repository and storage contracts

**Use Cases**

Application workflows such as CSV ingestion and KPI retrieval

All business rules and KPI computations live here

Fully testable without FastAPI or PostgreSQL

**Infrastructure**

PostgreSQL repositories implemented with SQLAlchemy

CSV parser and file storage implementations

Alembic migrations for schema evolution

**API**

FastAPI routers and controllers

Pydantic DTOs for input/output

Dependency injection to wire use cases and repositories

**Visualization**

Streamlit dashboard consuming the API

Read-only client with no business logic

## Api endpoints

### Upload daily metrics (CSV)
```
POST /api/upload-csv
```

Accepts a CSV file containing daily health and fitness metrics

Re-uploading a CSV overwrites existing records for the same dates (idempotent upsert)

Returns an ingestion report with processing details

### Retrieve computed KPIs
```
GET /api/kpis?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
```

Returns computed KPIs for the specified date range

Includes rolling averages and trend metrics

Missing days are handled internally by the computation logic

## Running Locally

### Prerequisites

Python 3.11+

Docker & Docker Compose

### 0. Clone the repository
```
git clone https://github.com/albermar/health-metrics-hub.git
cd health-metrics-hub
```

### 1. Create and activate a virtual environment

From the repository root:

```
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\activate      # Windows
```

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Configure PostgreSQL (Docker)

PostgreSQL runs locally using Docker Compose.
```
cd app/infrastructure/db/local_postgres_up
cp .env.example .env
```

This .env file is used by Docker Compose to initialize the PostgreSQL container.

Env vars example for docker compose:

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=health_metrics
```


### 4. Start PostgreSQL
```
cd app/infrastructure/db/local_postgres_up
docker compose up -d
```


PostgreSQL will be available at localhost:5433.

### 5. Configure application environment

From the repository root:
```
cp .env.example .env
```

This file is used by FastAPI, Alembic, and Streamlit.

Env vars example:
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=health_metrics
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
```

### 6. Run database migrations
```
alembic upgrade head
```

### 7. Start the API
```
uvicorn app.api.main:app --reload
```

The API will be available at http://localhost:8000

Swagger UI is available at http://localhost:8000/docs

### 8. Upload a sample CSV

A sample CSV file is provided in sample_data/.

From the repository root:

```curl
curl -X POST http://localhost:8000/api/upload-csv \
  -F "file=@sample_data/sample_metrics.csv"
```

This uploads the file from your local machine to the API for processing.

### 9. Start the dashboard
```
streamlit run app/dashboard/streamlit_app.py
```

The dashboard consumes the API and displays computed KPIs.

