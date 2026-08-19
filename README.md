# N100 Financial Platform

## Project Overview

This project processes financial datasets, stores them in a SQLite database, and exposes REST APIs using FastAPI.

## Features

- ETL pipeline
- SQLite database
- FastAPI backend
- Swagger API documentation

## Installation

```bash
pip install -r requirements.txt
```

## Run ETL

```bash
python src/etl/loader.py
python src/etl/database.py
```

## Run API

```bash
uvicorn src.api.main:app --reload
```

## Swagger Docs

Open:

```
http://127.0.0.1:8000/docs
``
## 🔗 Project Links

- **GitHub Repository:** https://github.com/sayanvines286-cloud/n100-financial-platform
- **Live Streamlit App:** https://n100-financial-platform-myvmjum7vmufrdw59qjbzi.streamlit.app/