# CampusGrid: Enterprise Asset & Facility Reservation Engine

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.7%2B-E92063?style=flat&logo=pydantic)](https://docs.pydantic.dev/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0%2B-D71F00?style=flat&logo=sqlalchemy)](https://docs.sqlalchemy.org/)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=flat&logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=flat&logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)](#)

CampusGrid is a production-grade, enterprise-ready reservation and inventory management backend built for universities and research institutions. It coordinates access to high-demand campus assets, including engineering lab hardware, media production gear, and specialized campus facilities.

---

## 🏛️ System Architecture

CampusGrid is built following **Clean Architecture** principles, enforcing strict separation of concerns, repository-service decoupling, and dependency injection.

```
                    ┌────────────────────────────────────────────────────────┐
                    │               Client Applications / Web UI            │
                    └───────────────────────────┬────────────────────────────┘
                                                │  HTTP / REST (JSON)
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ Presentation Layer (campus_grid.api.v1)                                                 │
│  - FastAPI APIRouters: /auth, /users, /resources, /bookings, /audit-logs                │
│  - Strict Role-Based Access Control (RBAC) Dependency Injectors                         │
│  - Pydantic v2 Strict Serialization & Custom Invariant Validators                       │
└───────────────────────────────────────────────┬─────────────────────────────────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ Business Logic / Service Layer (campus_grid.services)                                   │
│  - AuthService: Credential hashing (Bcrypt) & JWT session issuance                      │
│  - BookingService: Transactional Double-Booking Prevention & Capacity Guard             │
│  - ResourceService: Catalog lifecycle & inventory tracking                             │
│  - UserService: Identity governance & role promotion                                    │
│  - AuditLogService: Immutable system event logging                                      │
└───────────────────────────────────────────────┬─────────────────────────────────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ Data Access / Repository Layer (campus_grid.repository)                                 │
│  - BaseRepository[T]: Generic CRUD, offset pagination, filtering                        │
│  - BookingRepository: Interval overlap queries & capacity counting                      │
│  - ResourceRepository: Pessimistic locking (with_for_update)                            │
│  - UserRepository & AuditLogRepository                                                  │
└───────────────────────────────────────────────┬─────────────────────────────────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ Domain Models & Persistence Layer (campus_grid.model & campus_grid.core)                │
│  - SQLAlchemy 2.0 DeclarativeBase (Mapped, mapped_column, typed relationships)          │
│  - PostgreSQL 16 (Production/Staging) / SQLite In-Memory (Automated Testing)             │
│  - Alembic Database Schema Migrations                                                   │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Enterprise Features

### 1. Transactional Double-Booking Prevention Engine
Booking high-value hardware and rooms under concurrent demand requires strict consistency:
- **Pessimistic Concurrency Control:** When a reservation request arrives, `BookingService` acquires a row-level lock (`with_for_update()`) on the target resource.
- **Interval Overlap Verification:** Checks all active reservations (`pending`, `approved`) where `(start_time < requested_end) AND (end_time > requested_start)`.
- **Quantity Limits Enforcement:** If concurrent overlapping bookings meet or exceed the resource's `total_quantity`, the reservation is rejected with `HTTP 409 Conflict`.
- **Atomic Audit Trail:** The reservation and corresponding `AuditLog` entry are written and committed within the exact same database transaction.

### 2. Role-Based Access Control (RBAC)
Role policies are enforced declaratively via FastAPI dependency injection:
- **Student (`student`):**
  - Can view available resources catalog.
  - Can create reservations for themselves (created in `pending` status).
  - Can view, cancel, and return only their own bookings.
  - Explicitly forbidden from viewing user lists, managing catalog assets, approving bookings, or reading audit logs (`403 Forbidden`).
- **Faculty (`faculty`):**
  - Can create and manage campus resources.
  - Can review and approve/reject pending student reservations.
  - Auto-approved bookings for curriculum and research needs.
  - Can inspect audit logs and reservation history.
- **Administrator (`admin`):**
  - Complete control across all system entities.
  - Can update user roles, toggle account statuses, delete resources, and audit all platform operations.

### 3. Pydantic v2 Strict Request & Response Schemas
- Uses `model_config = ConfigDict(from_attributes=True)`.
- Custom `@field_validator` ensures email normalization and password complexity (minimum 8 characters).
- Custom `@model_validator(mode="after")` enforces cross-field business logic:
  - `end_time > start_time` with a minimum duration of 5 minutes and maximum of 30 days.
  - `available_quantity <= total_quantity`.

---

## 📋 Full API Route Reference Table

| HTTP Method | Route Endpoint | Minimum Role | Request Body | Description |
|:---|:---|:---|:---|:---|
| **GET** | `/` | Public | None | API metadata and documentation link |
| **GET** | `/health` | Public | None | Health check endpoint |
| **POST** | `/api/v1/auth/sign-up` | Public | `UserRegister` | Register a new user (student/faculty/admin) |
| **POST** | `/api/v1/auth/sign-in` | Public | `UserLogin` | Authenticate and obtain Bearer JWT token |
| **GET** | `/api/v1/auth/me` | Authenticated | None | Retrieve authenticated user profile |
| **GET** | `/api/v1/users` | Admin | None (Query params) | List users with pagination |
| **GET** | `/api/v1/users/{id}` | Admin | None | Get specific user account profile |
| **PATCH** | `/api/v1/users/{id}` | Admin | `UserRoleUpdate` | Update user role or active status |
| **GET** | `/api/v1/resources` | Authenticated | None (Query params) | List resources with category/status filters |
| **GET** | `/api/v1/resources/{id}` | Authenticated | None | Get detailed resource specifications |
| **POST** | `/api/v1/resources` | Faculty / Admin | `ResourceCreate` | Create a new asset or facility entry |
| **PUT** | `/api/v1/resources/{id}` | Faculty / Admin | `ResourceUpdate` | Update asset quantity or operational status |
| **DELETE** | `/api/v1/resources/{id}` | Faculty / Admin | None | Decommission/remove an asset |
| **POST** | `/api/v1/bookings` | Authenticated | `BookingCreate` | Reserve asset (Double-booking protected) |
| **GET** | `/api/v1/bookings` | Authenticated | None (Query params) | List bookings (Student sees self, Faculty/Admin see all) |
| **GET** | `/api/v1/bookings/my` | Authenticated | None (Query params) | Retrieve current user's reservations |
| **GET** | `/api/v1/bookings/{id}` | Authenticated | None | Get booking details (Owner or Faculty/Admin) |
| **POST** | `/api/v1/bookings/{id}/approve` | Faculty / Admin | None | Approve a pending booking |
| **POST** | `/api/v1/bookings/{id}/cancel` | Authenticated | None | Cancel reservation (Owner or Faculty/Admin) |
| **POST** | `/api/v1/bookings/{id}/return` | Authenticated | None | Mark equipment returned (Owner or Faculty/Admin) |
| **GET** | `/api/v1/audit-logs` | Faculty / Admin | None (Query params) | Query immutable audit log events |

---

## 🛠️ Environment Setup & Local Installation

### Prerequisites
- Python 3.11 or 3.12
- PostgreSQL 14+ (or SQLite for development)
- Docker & Docker Compose (optional)

### 1. Clone & Set Up Virtual Environment
```bash
# Navigate to project directory
cd CampusGrid

# Create virtual environment
python3.12 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate   # On Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy the template configuration file:
```bash
cp .env.example .env
```
Edit `.env` to match your local setup:
```dotenv
ENV=dev
PROJECT_NAME=CampusGrid
SECRET_KEY=generate-a-strong-32-character-secret-key-here
DB=sqlite
# For PostgreSQL:
# DB=postgresql
# DB_USER=campusgrid
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=campusgrid_dev
```

### 3. Apply Database Migrations
```bash
alembic upgrade head
```

### 4. Run the Development Server
```bash
uvicorn campus_grid.main:app --reload --host 0.0.0.0 --port 8000
```
Access the interactive documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🐳 Docker Compose & Container Deployment

### Local Multi-Container Stack (FastAPI + PostgreSQL 16)
```bash
# Build and launch containers in background
docker compose up --build -d

# Check service status and healthchecks
docker compose ps

# View application logs
docker compose logs -f api

# Stop and remove containers
docker compose down
```

---

## ☁️ Cloud Deployment Guide (Render, Railway, Supabase)

CampusGrid is container-native and designed for frictionless zero-downtime deployment:

### 1. Railway / Render Deployment
1. **Repository:** Push your repository to GitHub and link it to your Railway or Render account.
2. **Build Settings:**
   - **Environment:** Docker (uses the root `Dockerfile` automatically)
   - **Start Command:** Automatically runs `sh -c "exec uvicorn campus_grid.main:app --host 0.0.0.0 --port ${PORT:-8000}"`
3. **Environment Variables:**
   - `ENV`: `prod`
   - `SECRET_KEY`: `<generate-a-strong-32-character-secret>`
   - `DATABASE_URL`: Injected automatically when linking a managed PostgreSQL database (e.g. Railway PostgreSQL or Supabase). CampusGrid auto-normalizes `postgres://` to `postgresql://`.

### 2. Supabase / Managed PostgreSQL Integration
1. Obtain your PostgreSQL Transaction Connection String from the **Supabase Dashboard** (`Settings -> Database`).
2. Set the connection string in your deployment environment:
   ```dotenv
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```
3. Run migrations during release phase or pre-deploy step:
   ```bash
   alembic upgrade head
   ```

---

## 🧪 Testing Suite

CampusGrid includes a comprehensive unit and integration test suite:
- **Schema Validation Tests:** Temporal ordering, duration limits, inventory boundaries.
- **Security Tests:** Bcrypt password verification, JWT expiration and tampering guards.
- **RBAC Tests:** Privilege boundaries for students, faculty, and administrators.
- **Double-Booking Tests:** Concurrency slot overlaps, capacity tracking, maintenance status lockouts.

Run the test suite:
```bash
# Run all tests with verbose output
pytest -v

# Run with test coverage report
pytest --cov=campus_grid tests/
```

---

## 📄 License
Proprietary & Confidential - CampusGrid Systems. All rights reserved.
