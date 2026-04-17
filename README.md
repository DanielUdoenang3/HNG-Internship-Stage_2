# Profile API

A REST API that accepts a name, enriches it with data from three external APIs (Genderize, Agify, Nationalize), classifies the result, and persists it to a PostgreSQL database.

Built with **FastAPI**, **SQLAlchemy**, **Alembic**, and **PostgreSQL**.

---

## Features

- Create a profile by name — fetches gender, age, and nationality data automatically
- Deduplication — submitting the same name returns the existing record
- Age group classification: `child`, `teenager`, `adult`, `senior`
- Nationality resolved to the highest-probability country
- Filter profiles by `gender`, `country_id`, and `age_group`
- Full CRUD: create, read (single + list), delete
- CORS enabled (`Access-Control-Allow-Origin: *`)
- UUID v7 primary keys
- UTC ISO 8601 timestamps

---

## Tech Stack

| Layer      | Technology              |
|------------|-------------------------|
| Framework  | FastAPI                 |
| ORM        | SQLAlchemy 2.x          |
| Migrations | Alembic                 |
| Database   | PostgreSQL               |
| HTTP Client| httpx                   |
| Runtime    | Python 3.13+            |
| Server     | Uvicorn                 |

---

## External APIs

| API         | URL                              | Data Provided              |
|-------------|----------------------------------|----------------------------|
| Genderize   | https://api.genderize.io         | gender, probability, count |
| Agify       | https://api.agify.io             | predicted age              |
| Nationalize | https://api.nationalize.io       | country probabilities      |

No API keys required.

---

## Getting Started

### Prerequisites

- Python 3.13+
- PostgreSQL database
- `uv` or `pip` for package management

### Installation

```bash
# Clone the repo
git clone <your-repo-url>
cd <project-folder>

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
DB_URL=postgresql://user:password@localhost:5432/dbname
GENDERIZE_URL=https://api.genderize.io
AGIFY_URL=https://api.agify.io
NATIONALIZE_URL=https://api.nationalize.io
```

### Database Setup

```bash
alembic upgrade head
```

### Running the Server

```bash
# Development (with auto-reload)
make run

# Local with migrations
make dev

# Production
make prod
```

Or directly:

```bash
uvicorn app.main:app --reload
```

Server runs at `http://localhost:8000`

---

## Docker

```bash
docker build -t profile-api .
docker run -p 8000:8000 --env-file .env profile-api
```

---

## API Reference

### Base URL

```
/api/profiles
```

---

### POST /api/profiles

Create a new profile. If the name already exists, returns the existing record.

**Request Body**
```json
{ "name": "ella" }
```

**201 Created**
```json
{
  "status": "success",
  "data": {
    "id": "b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12",
    "name": "ella",
    "gender": "female",
    "gender_probability": 0.99,
    "sample_size": 1234,
    "age": 46,
    "age_group": "adult",
    "country_id": "DK",
    "country_probability": 0.85,
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```

**200 OK — duplicate name**
```json
{
  "status": "success",
  "message": "Profile already exists",
  "data": { "...existing profile..." }
}
```

---

### GET /api/profiles

Get all profiles. Supports optional query filters.

**Query Parameters**

| Parameter    | Type   | Example      | Notes              |
|--------------|--------|--------------|--------------------|
| `gender`     | string | `male`       | case-insensitive   |
| `country_id` | string | `NG`         | case-insensitive   |
| `age_group`  | string | `adult`      | case-insensitive   |

**Example**
```
GET /api/profiles?gender=male&country_id=NG
```

**200 OK**
```json
{
  "status": "success",
  "count": 2,
  "data": [
    {
      "id": "id-1",
      "name": "emmanuel",
      "gender": "male",
      "age": 25,
      "age_group": "adult",
      "country_id": "NG"
    }
  ]
}
```

---

### GET /api/profiles/{id}

Get a single profile by ID.

**200 OK**
```json
{
  "status": "success",
  "data": {
    "id": "b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12",
    "name": "emmanuel",
    "gender": "male",
    "gender_probability": 0.99,
    "sample_size": 1234,
    "age": 25,
    "age_group": "adult",
    "country_id": "NG",
    "country_probability": 0.85,
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```

---

### DELETE /api/profiles/{id}

Delete a profile by ID.

**204 No Content** — on success  
**404 Not Found** — if ID does not exist

---

## Classification Rules

### Age Group (from Agify)

| Age Range | Group      |
|-----------|------------|
| 0 – 12    | child      |
| 13 – 19   | teenager   |
| 20 – 59   | adult      |
| 60+       | senior     |

### Nationality

The country with the highest probability from the Nationalize response is used.

---

## Error Responses

All errors follow this structure:

```json
{
  "status": "error",
  "message": "<description>"
}
```

| Status | Scenario                                      |
|--------|-----------------------------------------------|
| 400    | Missing or empty name                         |
| 404    | Profile not found                             |
| 422    | Invalid request body type                     |
| 502    | External API returned an invalid response     |
| 500    | Upstream or server failure                    |

### 502 Format (External API failures)

```json
{
  "status": "502",
  "message": "Genderize returned an invalid response"
}
```

Applies to: `Genderize`, `Agify`, `Nationalize`

**Edge cases that trigger 502 (profile is not stored):**
- Genderize returns `gender: null` or `count: 0`
- Agify returns `age: null`
- Nationalize returns no country data

---

## Project Structure

```
.
├── app/
│   ├── api/
│   │   ├── controller/
│   │   │   └── profile.py       # Request handlers
│   │   └── router/
│   │       └── profile.py       # Route definitions
│   ├── models/
│   │   ├── base.py              # User model
│   │   └── base_models.py       # Abstract base with id, timestamps
│   ├── schema/
│   │   └── profile.py           # Pydantic request schemas
│   ├── services/
│   │   └── profiles.py          # Business logic
│   ├── utils/
│   │   ├── custom_response.py   # Standardized response helpers
│   │   ├── database.py          # DB engine and session
│   │   └── settings.py          # Environment config
│   └── main.py                  # FastAPI app entry point
├── alembic/                     # Database migrations
├── Dockerfile
├── Makefile
├── pyproject.toml
└── requirements.txt
```

---

## Interactive Docs

Once the server is running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
