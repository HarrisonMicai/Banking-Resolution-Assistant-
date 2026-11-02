# FastAPI Application - Banking Complaint Resolution Assistant

This project implements a production-aware Python API backend for the Banking Complaint Resolution Assistant, adhering to a clean, layered architecture (`app/`).

## Prerequisites
- **Python 3.10+**
- **PostgreSQL** instance running locally or remotely

## Project Directory Structure
```text
app/
 ├ main.py
 ├ core/
 │   ├ config.py
 │   └ dependencies/
 │       └ dependencies.py
 ├ api/
 │   └ routers/
 │       ├ health.py
 │       ├ customers.py
 │       └ complaints.py
 ├ schemas/
 ├ services/
 ├ repositories/
 ├ models/
 └ tests/


 # Activate Virtual Environment:

# Windows (PowerShell):

Bash
.venv\Scripts\activate


# macOS / Linux:

Bash
source .venv/bin/activate

# Install Dependencies:

Bash
pip install fastapi uvicorn pydantic-settings psycopg2-binary python-dotenv


# Run FASTAPI in env:

uvicorn app.main:app --reload