# Project 2: System for analyzing health habits and physical performance.

Based on daily metrics such as steps, calories consumed and burned, weight, body measurements, and sleep, the system will compute key fitness KPIs, trends, adherence levels and maybe other metrics.

## main components:

- Backend: it will receive data (via CSV), process it, compute KPIs using pandas, store it persistently in a PostgreSQL database, and expose endpoints for data retrieval.
- Visual dashboard: it will display metrics, KPIs, and time-series insights through a clear and interactive interface, enabling users to visualize the evolution of their performance and health habits.

## Main skills:

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

