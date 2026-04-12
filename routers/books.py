import hashlib
import mimetypes
import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from crud import (
    create_book,
    create_file_record,
    delete_book_and_files,
    get_file_for_book,
    list_files_for_book,
    read_book as read_book_in_db,
)
from db import get_db
from models import User
from schema import BookRead, FileRead
from utils import (
    BOOKS_UPLOAD_ROOT,
    get_current_user,
    get_current_user_multipart,
    verify_file_sha256,
)

router = APIRouter()


def _require_visible_book(book):
    if not book.visibilty:
        raise HTTPException(status_code=403, detail="Book Not Available")


def _book_to_read(book, files_list) -> BookRead:
    pydantic_files = [FileRead.model_validate(f) for f in files_list]
    first = files_list[0] if files_list else None
    return BookRead(
        id=book.id,
        title=book.title,
        description=book.description,
        author_name=book.author_name,
        uploader=book.uploader,
        visibilty=book.visibilty,
        created_at=book.created_at,
        updated_at=book.updated_at,
        file_path=first.file_url if first else None,
        file_type=first.file_type if first else None,
        files=pydantic_files,
    )


def _save_uploaded_file(book_id: int, book_file: UploadFile) -> tuple[str, str, str]:
    folder_path = os.path.join(BOOKS_UPLOAD_ROOT, str(book_id))
    os.makedirs(folder_path, exist_ok=True)
    safe_name = os.path.basename(book_file.filename or "upload.bin")
    if not safe_name or safe_name in (".", ".."):
        safe_name = "upload.bin"
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    file_location = os.path.join(folder_path, unique_name)
    content = book_file.file.read()
    with open(file_location, "wb") as f:
        f.write(content)
    checksum = hashlib.sha256(content).hexdigest()
    ext = os.path.splitext(safe_name)[1].lstrip(".").lower() or "bin"
    return file_location, ext, checksum


@router.post("/upload_book")
def book_upload(
    title: str = Form(...),
    description: str = Form(...),
    author_name: str = Form(...),
    book_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_multipart),
):
    new_book = create_book(
        db,
        title,
        description,
        author_name,
        current_user.id,
    )
    file_location, ext, checksum = _save_uploaded_file(new_book.id, book_file)
    create_file_record(db, new_book.id, file_location, ext, checksum)
    return {
        "book_id": new_book.id,
        "file_path": file_location,
    }


@router.post("/books/{book_id}/files")
def add_book_file(
    book_id: int,
    book_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_multipart),
):
    book = read_book_in_db(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book Not Found")
    if book.uploader != current_user.id:
        raise HTTPException(status_code=403, detail="Only the uploader can add files")
    file_location, ext, checksum = _save_uploaded_file(book_id, book_file)
    row = create_file_record(db, book_id, file_location, ext, checksum)
    return FileRead.model_validate(row)


@router.delete("/books/{book_id}")
def remove_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = read_book_in_db(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book Not Found")
    if book.uploader != current_user.id:
        raise HTTPException(status_code=403, detail="Only the uploader can delete this book")
    if not delete_book_and_files(db, book_id, BOOKS_UPLOAD_ROOT):
        raise HTTPException(status_code=404, detail="Book Not Found")
    return {"ok": True}


@router.get("/books/{book_id}", response_model=BookRead)
def get_book_metadata(book_id: int, db: Session = Depends(get_db)):
    book = read_book_in_db(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book Not Found")
    _require_visible_book(book)
    files = list_files_for_book(db, book_id)
    return _book_to_read(book, files)


@router.get("/books/{book_id}/file")
def get_book_file(
    book_id: int,
    file_id: int | None = None,
    db: Session = Depends(get_db),
):
    book = read_book_in_db(db, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book Not Found")
    _require_visible_book(book)
    db_file = get_file_for_book(db, book_id, file_id)
    if db_file is None:
        raise HTTPException(
            status_code=404,
            detail="No file registered for this book (check file_id if you passed one)",
        )
    path = db_file.file_url
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File missing on server")
    if not verify_file_sha256(path, db_file.checksum):
        raise HTTPException(
            status_code=409,
            detail="File on disk does not match stored checksum",
        )
    media = mimetypes.guess_type(path)[0] or "application/octet-stream"
    filename = os.path.basename(path)
    return FileResponse(
        path,
        media_type=media,
        filename=filename,
        content_disposition_type="inline",
    )
