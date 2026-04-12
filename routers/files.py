import mimetypes
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from crud import delete_file_record, read_book, read_file
from db import get_db
from models import User
from schema import FileRead
from utils import verify_file_sha256
from utils import get_current_user

router = APIRouter(tags=["files"])


def _require_visible_book(book):
    if book is None:
        raise HTTPException(status_code=404, detail="Book Not Found")
    if not book.visibilty:
        raise HTTPException(status_code=403, detail="Book Not Available")


@router.get("/files/{file_id}", response_model=FileRead)
def get_file_metadata(file_id: int, db: Session = Depends(get_db)):
    row = read_file(db, file_id)
    if row is None:
        raise HTTPException(status_code=404, detail="File Not Found")
    book = read_book(db, row.book_id)
    _require_visible_book(book)
    return FileRead.model_validate(row)


@router.get("/files/{file_id}/download")
def download_file_by_id(file_id: int, db: Session = Depends(get_db)):
    row = read_file(db, file_id)
    if row is None:
        raise HTTPException(status_code=404, detail="File Not Found")
    book = read_book(db, row.book_id)
    _require_visible_book(book)
    path = row.file_url
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File missing on server")
    if not verify_file_sha256(path, row.checksum):
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


@router.delete("/files/{file_id}")
def remove_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = read_file(db, file_id)
    if row is None:
        raise HTTPException(status_code=404, detail="File Not Found")
    book = read_book(db, row.book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book Not Found")
    if book.uploader != current_user.id:
        raise HTTPException(status_code=403, detail="Only the uploader can delete this file")
    if not delete_file_record(db, file_id):
        raise HTTPException(status_code=404, detail="File Not Found")
    return {"ok": True}
