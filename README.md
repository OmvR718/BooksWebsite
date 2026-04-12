# BooksWebsite

Backend API for a book-sharing service: users sign up, authenticate with JWTs, upload book files, and download or browse metadata for visible books. Built with **FastAPI**, **SQLAlchemy**, **Pydantic**, and **PostgreSQL**.

## Features

- **Users**: registration (`/signup`), login with access and refresh tokens (`/login`), profile read/update/delete
- **Books**: multipart upload with metadata, optional extra files per book, public metadata and file download for books marked visible
- **Integrity**: SHA-256 checksums stored per file; downloads are verified against the database before streaming
- **Auth**: Bearer JWT for protected routes; multipart uploads support pasting the token in Swagger’s form field

## Tech stack

| Layer        | Choice                                      |
| ------------ | ------------------------------------------- |
| API          | FastAPI                                     |
| Validation   | Pydantic v2 (`EmailStr`, response models)   |
| ORM / DB     | SQLAlchemy 2.x, PostgreSQL via **pg8000**     |
| Passwords    | bcrypt                                      |
| Tokens       | JWT (HS256) via PyJWT                       |

Tables live in the PostgreSQL schema **`app_schema`**; the app creates the schema and tables on startup (`db.py`).

## Prerequisites

- Python 3.11+ (3.12 works with the current codebase)
- A running **PostgreSQL** instance and a database you can connect to

## Quick start

### 1. Clone and create a virtual environment

```bash
cd BooksWebsite
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # macOS / Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the database

Edit [`db.py`](db.py) and set `URL.create(...)` to match your PostgreSQL host, database name, username, and password.

> **Security:** Avoid committing real credentials. Prefer environment variables or a secrets manager and wire them into `URL.create` in your own deployment.

### 4. Environment variables

| Variable            | Required | Description |
| ------------------- | -------- | ----------- |
| `SECRET_KEY`        | **Yes**  | Secret used to sign JWT access tokens (use a long random string in production). |
| `BOOKS_UPLOAD_DIR`  | No       | Directory for uploaded files (default: `uploads` under the project root, resolved to an absolute path). |

Example (PowerShell):

```powershell
$env:SECRET_KEY = "change-me-to-a-long-random-string"
$env:BOOKS_UPLOAD_DIR = "F:\BooksWebsite\uploads"
```

### 5. Run the API

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- **Interactive docs (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
- **OpenAPI JSON:** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

## API overview

All paths are relative to the app root (no global `/api` prefix).

### Authentication and users

| Method | Path            | Auth | Description |
| ------ | --------------- | ---- | ----------- |
| `POST` | `/signup`       | No   | Create account (JSON body: username, email, password). |
| `POST` | `/login`        | No   | Returns `access_token`, `refresh_token`, `token_type`. |
| `GET`  | `/get_user`     | No   | Query: `user_id`. |
| `PUT`  | `/update_user`  | No   | JSON body; **email** required to identify the user; optional new email/password. |
| `DELETE` | `/delete_user` | No | Query: `user_id`. |

Protected routes expect: `Authorization: Bearer <access_token>`. For file upload endpoints, Swagger allows an `access_token` form field as an alternative.

### Books and files

| Method | Path | Auth | Description |
| ------ | ---- | ---- | ----------- |
| `POST` | `/upload_book` | Yes (multipart) | Form: title, description, author_name, book_file. |
| `POST` | `/books/{book_id}/files` | Yes (uploader) | Add another file to an existing book. |
| `GET`  | `/books/{book_id}` | No | Book metadata and file list (hidden books return 403). |
| `GET`  | `/books/{book_id}/file` | No | Stream primary (or chosen) file; optional query `file_id`. |
| `DELETE` | `/books/{book_id}` | Yes (uploader) | Delete book, DB file rows, and upload folder. |
| `GET`  | `/files/{file_id}` | No | File metadata if parent book is visible. |
| `GET`  | `/files/{file_id}/download` | No | Download with checksum verification. |
| `DELETE` | `/files/{file_id}` | Yes (uploader) | Remove one file record and delete the file on disk. |

## Project layout

```
BooksWebsite/
├── main.py           # FastAPI app, router includes
├── db.py             # Engine, session, schema bootstrap
├── models.py         # SQLAlchemy models (users, books, files, auths)
├── schema.py         # Pydantic request/response models
├── crud.py           # Database operations
├── utils.py          # Auth helpers, password hashing, upload root, JWT
├── routers/
│   ├── users.py      # Signup, login, user CRUD-style routes
│   ├── books.py      # Upload, book metadata, book file download/delete
│   └── files.py      # File metadata, download, delete by file id
├── requirements.txt
└── README.md
```

## License

This project is licensed under the Apache License 2.0 — see [`LICENSE`](LICENSE).
