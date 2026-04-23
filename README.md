# Profile API

A REST API that serves pre-seeded demographic profiles with filtering, sorting, pagination, and natural language search.

Built with **FastAPI**, **SQLAlchemy**, **Alembic**, and **PostgreSQL**.

---

## Tech Stack

| Layer      | Technology     |
|------------|----------------|
| Framework  | FastAPI        |
| ORM        | SQLAlchemy 2.x |
| Migrations | Alembic        |
| Database   | PostgreSQL     |
| Runtime    | Python 3.13+   |
| Server     | Uvicorn        |

---

## Getting Started

### Prerequisites

- Python 3.13+
- PostgreSQL database
- `uv` (recommended) or `pip`

### Installation

```bash
git clone <your-repo-url>
cd <project-folder>

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
DB_URL=postgresql://user:password@localhost:5432/dbname
```

### Database Setup

```bash
alembic upgrade head
```

### Running the Server

```bash
uvicorn app.main:app --reload
```

Server runs at `http://localhost:8000`.
Interactive docs at `http://localhost:8000/docs`.

---

## Docker

```bash
docker build -t profile-api .
docker run -p 8000:8000 --env-file .env profile-api
```

---

## API Reference

### GET /api/profiles

Returns all profiles. Supports filtering, sorting, and pagination via query parameters.

**Filter Parameters**

| Parameter               | Type   | Example  | Description                          |
|-------------------------|--------|----------|--------------------------------------|
| `gender`                | string | `male`   | Filter by gender (case-insensitive)  |
| `age_group`             | string | `adult`  | `child`, `teenager`, `adult`, `senior` |
| `country_id`            | string | `NG`     | ISO 3166-1 alpha-2 (case-insensitive)|
| `min_age`               | int    | `18`     | Minimum age (inclusive)              |
| `max_age`               | int    | `40`     | Maximum age (inclusive)              |
| `min_gender_probability`| float  | `0.8`    | Minimum gender confidence            |
| `min_country_probability`| float | `0.5`    | Minimum country confidence           |

**Sorting Parameters**

| Parameter | Values                                    | Default |
|-----------|-------------------------------------------|---------|
| `sort_by` | `age`, `created_at`, `gender_probability` | none    |
| `order`   | `asc`, `desc`                             | `asc`   |

**Pagination Parameters**

| Parameter | Type | Default | Max |
|-----------|------|---------|-----|
| `page`    | int  | `1`     | —   |
| `limit`   | int  | `10`    | `50`|

**Example**
```
GET /api/profiles?gender=female&country_id=KE&age_group=adult&sort_by=age&order=desc&page=1&limit=20
```

**200 OK**
```json
{
  "status": "success",
  "page": 1,
  "limit": 20,
  "total": 4,
  "data": [
    {
      "id": "...",
      "name": "Zanele Mnguni",
      "gender": "female",
      "gender_probability": 0.68,
      "age": 30,
      "age_group": "adult",
      "country_id": "KE",
      "country_name": "Kenya",
      "country_probability": 0.85,
      "created_at": "2026-04-23T06:00:00+00:00"
    }
  ]
}
```

---

### GET /api/profiles/search

Natural language search. Pass a plain-English query via `?q=` and the API parses it into filters.

**Parameters**

| Parameter | Type   | Required | Description              |
|-----------|--------|----------|--------------------------|
| `q`       | string | yes      | Plain-English query      |
| `page`    | int    | no       | Default `1`              |
| `limit`   | int    | no       | Default `10`, max `50`   |

**Example**
```
GET /api/profiles/search?q=young males from nigeria&page=1&limit=10
```

**200 OK** — same shape as `/api/profiles`

**400 — uninterpretable query**
```json
{ "status": "error", "message": "Unable to interpret query" }
```

---

### POST /api/profiles/seed

Seeds the database from `seed_profiles.json`. Safe to call once on a fresh database.

**201 Created**
```json
{ "status": "success", "message": "Users seeded successfully" }
```

---

## Error Responses

All errors follow this structure:

```json
{ "status": "error", "message": "<description>" }
```

| Status | Scenario                        |
|--------|---------------------------------|
| 400    | Missing/empty parameter         |
| 404    | Profile not found               |
| 422    | Invalid parameter type          |
| 500    | Server or database failure      |

---

## Natural Language Parsing

`GET /api/profiles/search?q=<query>` accepts plain-English queries and converts them into the same filters used by `GET /api/profiles`. The parser is fully rule-based — no AI or LLMs are involved.

### How It Works

The parser runs these steps in order:

1. Lowercase and normalise the query
2. Extract country (longest-match against a keyword table)
3. Strip noise/filler words (`find`, `show me`, `all`, `who are`, etc.)
4. Extract numeric age ranges from patterns
5. If no numeric range found, check for age descriptor words (`young`, `middle-aged`, etc.)
6. Extract age group keywords (`teenager`, `elderly`, etc.)
7. Extract gender keywords; if both genders are mentioned, no gender filter is applied
8. Return `None` if no filters were resolved → responds with `"Unable to interpret query"`

### Supported Keywords

#### Gender

| Keywords | Maps to |
|----------|---------|
| `male`, `males`, `man`, `men`, `boy`, `boys`, `guy`, `guys`, `lad`, `lads`, `gentleman` | `gender=male` |
| `female`, `females`, `woman`, `women`, `girl`, `girls`, `lady`, `ladies`, `gal`, `gals` | `gender=female` |
| `male and female`, `both genders`, `everyone`, `people`, `individuals`, `persons` | no gender filter |

#### Age Groups

| Keywords | Maps to |
|----------|---------|
| `child`, `children`, `kid`, `kids`, `infant`, `infants` | `age_group=child` |
| `toddler`, `toddlers` | `age_group=child` |
| `teenager`, `teenagers`, `teen`, `teens`, `adolescent`, `adolescents` | `age_group=teenager` |
| `adult`, `adults`, `grown up`, `grown-up` | `age_group=adult` |
| `senior`, `seniors`, `elderly`, `elder`, `elders`, `old`, `aged` | `age_group=senior` |

#### Age Range Descriptors (parsing only — not stored age groups)

| Keywords | Maps to |
|----------|---------|
| `young`, `youth`, `youths`, `youthful`, `juvenile` | `min_age=16, max_age=24` |
| `middle-aged`, `middle age` | `min_age=35, max_age=55` |
| `newborn`, `newborns` | `min_age=0, max_age=1` |
| `school-age`, `school age` | `min_age=5, max_age=12` |

#### Numeric Age Patterns

| Pattern | Example | Maps to |
|---------|---------|---------|
| `above N` / `over N` / `older than N` / `at least N` | `above 30` | `min_age=30` |
| `below N` / `under N` / `younger than N` / `at most N` | `under 18` | `max_age=18` |
| `between N and M` / `N to M` | `between 20 and 40` | `min_age=20, max_age=40` |
| `N-M` (bare range) | `25-35` | `min_age=25, max_age=35` |
| `aged N` | `aged 45` | `min_age=45, max_age=45` |

#### Countries

Country names, adjective forms, and common demonyms are all supported:

| Recognised forms | `country_id` |
|-----------------|--------------|
| `nigeria`, `nigerian` | `NG` |
| `kenya`, `kenyan` | `KE` |
| `south africa`, `south african` | `ZA` |
| `united kingdom`, `uk`, `britain`, `british`, `england` | `GB` |
| `united states`, `usa`, `america`, `american` | `US` |
| `ethiopia`, `ethiopian` | `ET` |
| `ghana`, `ghanaian` | `GH` |
| `tanzania`, `tanzanian` | `TZ` |
| `uganda`, `ugandan` | `UG` |
| `dr congo`, `drc`, `democratic republic of congo` | `CD` |
| `ivory coast`, `ivorian`, `côte d'ivoire` | `CI` |

Full list covers 40+ African and international countries including demonyms (e.g. `somali`, `moroccan`, `burkinabe`, `motswana`).

### Example Query Mappings

| Query | Resolved Filters |
|-------|-----------------|
| `young males` | `gender=male, min_age=16, max_age=24` |
| `females above 30` | `gender=female, min_age=30` |
| `people from angola` | `country_id=AO` |
| `adult males from kenya` | `gender=male, age_group=adult, country_id=KE` |
| `male and female teenagers above 17` | `age_group=teenager, min_age=17` |
| `elderly women in ethiopia` | `gender=female, age_group=senior, country_id=ET` |
| `boys between 10 and 15` | `gender=male, min_age=10, max_age=15` |
| `middle-aged nigerian women` | `gender=female, min_age=35, max_age=55, country_id=NG` |
| `seniors from the uk` | `age_group=senior, country_id=GB` |
| `girls under 12` | `gender=female, max_age=12` |
| `young ghanaian men` | `gender=male, min_age=16, max_age=24, country_id=GH` |
| `aged 25` | `min_age=25, max_age=25` |

---

## Limitations

These are known edge cases the parser does not handle:

- **Spelling errors** — `nigerria`, `femal`, `yung` are not recognised. No fuzzy matching.
- **Negation** — `not from kenya`, `non-adults`, `excluding males` are not parsed. Negation is ignored.
- **Multiple countries** — `from kenya or nigeria` only picks up one country (longest match wins).
- **Relative terms without context** — `older people`, `younger generation` are not mapped to numeric ranges. Only the explicit descriptor words listed above are handled.
- **Ordinal/superlative queries** — `the oldest`, `youngest profiles`, `most common gender` are not supported.
- **Non-English input** — the parser only handles English.
- **Conflicting gender signals** — if a query contains both `men` and `women` without an explicit "and/both" phrase, the gender filter is dropped silently rather than returning an error.
- **Age group + age range conflicts** — if a query says `young adults`, both `age_group=adult` and `min_age=16, max_age=24` are applied simultaneously. The database will return the intersection, which may be empty.
- **Probability filters** — `min_gender_probability` and `min_country_probability` are not reachable via natural language search; use `GET /api/profiles` directly for those.
- **Sorting** — the `/search` endpoint does not support `sort_by`/`order`. Use `GET /api/profiles` for sorted results.

---

## Project Structure

```
.
├── app/
│   ├── api/
│   │   ├── controller/profile.py   # Request handlers
│   │   └── router/profile.py       # Route definitions
│   ├── models/
│   │   ├── base.py                 # User model
│   │   └── base_models.py          # Abstract base (id, timestamps)
│   ├── schema/
│   │   └── profile.py              # Pydantic schemas
│   ├── services/
│   │   └── profiles.py             # Business logic
│   ├── utils/
│   │   ├── custom_response.py      # Standardised response helpers
│   │   ├── database.py             # DB engine and session
│   │   ├── query_parser.py         # Natural language parser
│   │   └── settings.py             # Environment config
│   └── main.py                     # FastAPI app entry point
├── alembic/                        # Database migrations
├── seed_profiles.json              # Seed data
├── Dockerfile
├── pyproject.toml
└── requirements.txt
```
