# Server-Driven HRMS (FastAPI + RBAC + Dynamic Views)

Backend-first HRMS prototype with:
- dynamic model registry
- generic CRUD APIs
- hook system (global/module/model scope)
- RBAC (user/group/model actions)
- field-level access control
- server-driven JSON views loaded from module manifests

## 1. Prerequisites

- Python 3.12+ (3.14 also works in this repo)
- PostgreSQL
- `pip`
- (optional) virtualenv

## 2. Install Dependencies

> Note: the project currently uses `requirment.txt` (spelling in repo).

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirment.txt
```

## 3. Environment Configuration (`.env`)

Create/update `.env` in project root:

```env
POSTGRES_USER=nofoobar
POSTGRES_PASSWORD=supersecret
POSTGRES_SERVER=localhost
POSTGRES_PORT=5433
POSTGRES_DB=TEST

LOGGING_LEVEL=INFO
ENV=staging

JWT_SECRET=replace_with_a_strong_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Required Variables
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_SERVER`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `JWT_SECRET`

## 4. Database Setup

Run migrations:

```powershell
alembic upgrade head
```

If Alembic reports multiple heads:

```powershell
alembic heads
alembic merge -m "merge heads" <head_1> <head_2>
alembic upgrade head
```

## 5. Run the API

```powershell
uvicorn main:app --reload
```

Open docs:
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`

## 6. First Login (Bootstrap Admin)

Create first admin once:

`POST /api/auth/bootstrap-admin`

```json
{
  "name": "Admin",
  "email": "admin@local.dev",
  "password": "Admin@12345"
}
```

Then login:

`POST /api/auth/login`

```json
{
  "email": "admin@local.dev",
  "password": "Admin@12345"
}
```

Use token:

`Authorization: Bearer <access_token>`

## 7. RBAC + Access Control Flow

Typical admin flow:

1. Create groups: `POST /api/access/groups`
2. Assign users to groups: `POST /api/access/groups/{group_id}/users/{user_id}`
3. List permissions: `GET /api/access/permissions`
4. Assign permission to group: `POST /api/access/groups/{group_id}/permissions/{permission_id}`
5. Add field rules: `POST /api/access/field-rules`
6. Check effective permissions: `GET /api/access/users/{user_id}/effective-permissions`

## 8. User Creation and Password Safety

For `ir_user` create/update:
- send `password` in payload
- system hashes and stores it in `password_hash`

Example:

```json
{
  "name": "Test User",
  "email": "user@local.dev",
  "password": "user@1234",
  "is_active": true
}
```

## 9. Server-Driven Views

Views are loaded from module manifest `data` entries pointing to JSON files.

Example manifest:

```python
{
    "name": "Employees",
    "depends": ["base"],
    "data": [
        "views/employee_form.json"
    ]
}
```

Example view file path:

`modules/employees/views/employee_form.json`

On startup, these files are synced into `ir_view`.

Resolve view for current user:

`GET /api/views/{model}?type=form`

Behavior:
- if view exists and user can access it -> returns JSON view
- if no view exists for model/type -> returns `404`
- field-level rules are applied before response (hidden/read-only fields)

## 10. Project Structure (High Level)

- `api/` - FastAPI routers
- `core/` - registry, hooks, CRUD engine, auth, permissions, sync services
- `modules/` - modular business domains (models, hooks, views, manifests)
- `alembic/` - migrations

## 11. Common Troubleshooting

### Invalid token
- Ensure exact header: `Authorization: Bearer <token>`
- Re-login after changing `JWT_SECRET`

### `UnknownHashError` on login
- User has plain text in `password_hash`
- Update user through API using `password` field so hash is generated

### Views not appearing in `ir_view`
- Ensure manifest `data` is a list
- Ensure JSON file path is correct
- Restart app so startup sync runs

