# FastAPI Chat Backend

This is a FastAPI-based backend for a WebSocket-enabled chat application, structured with SQLAlchemy, Alembic for migrations, and modular routers.

---

## Tech Stack

* **FastAPI**
* **SQLAlchemy**
* **Alembic**
* **MySQL** (or your DB of choice)
* **WebSockets**
* **JWT Auth**

---

## Setup Instructions (Local)

### 1. Clone the repository

```bash
git clone fastapi_chat_backend
cd fastapi_chat_backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=mysql+mysqlconnector://<user>:<password>@<host>/<dbname>
SECRET_KEY=<your-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## Database Setup

### 1. Initialize Alembic (only once)

```bash
alembic init alembic
```

### 2. Generate migration script

```bash
alembic revision --autogenerate -m "Initial migration"
```

### 3. Apply migrations

```bash
alembic upgrade head
```

---

## Run the Server

```bash
uvicorn main:app --reload
```

Server will start at: `http://127.0.0.1:8000`

---

## Project Structure (Summary)

```
.
├── alembic/                  # DB migrations
├── proj_websockets/          # WebSocket logic
├── routers/                  # API route handlers
├── models.py                 # SQLAlchemy models
├── schemas.py                # Pydantic schemas
├── auth.py                   # JWT auth
├── crud.py                   # DB interaction logic
├── main.py                   # FastAPI app entrypoint
└── .env                      # Environment variables
```

---

## ✅ API Docs

`http://127.0.0.1:8000/docs` – Swagger UI
`http://127.0.0.1:8000/redoc` – ReDoc

---

## Docker Setup

### 1. Create a `Dockerfile`:

```Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### 2. Create a `.dockerignore` (optional but recommended):

```
venv/
__pycache__/
*.pyc
.env
```

---

### 3. Build the Docker image:

```bash
docker build -t fastapi-chat-backend .
```

### 4. Run the Docker container:

```bash
docker run -d -p 8000:8000 --env-file .env fastapi-chat-backend
```

Now access the app at: `http://localhost:8000`

---

### Tip for MySQL with Docker Compose?

Let me know if you want a `docker-compose.yml` to spin up the FastAPI app *with* a MySQL container!

