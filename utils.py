import bcrypt
import jwt
from jwt.exceptions import PyJWTError
import os
from datetime import timedelta , datetime,timezone
from sqlalchemy.orm import Session
from models import User, Auth, Book
from typing import Optional
from fastapi import Depends, Form, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import secrets
import time
from db import get_db

SECRET_KEY= os.environ.get("SECRET_KEY")
ACCESS_TOKEN_EXPIRY_MINUTES=60
http_bearer = HTTPBearer()
http_bearer_optional = HTTPBearer(auto_error=False)


def normalize_bearer_token(raw: str) -> str:
    t = (raw or "").strip()
    if t.lower().startswith("bearer "):
        t = t[7:].strip()
    return t


def get_user_from_access_token(db: Session, token: str) -> User:
    token = normalize_bearer_token(token)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid Token")
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid Token")

        user_id = int(user_id)

    except HTTPException:
        raise
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid Token")
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid Token")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="User Not Found")

    return user


## hashes the password
def hash_password(password:str) -> str:
    return bcrypt.hashpw(password.encode(),bcrypt.gensalt()).decode()
# compares entered password to hashed password  
def verify_password(password:str,hashed:str) -> bool:
    return bcrypt.checkpw(password.encode(),hashed.encode())
def create_access_token(user_id:int) -> str:
    payload = {
        "sub": str(user_id),
        "iat":datetime.now(timezone.utc).timestamp(),
        "exp": (datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES))
        }
    return jwt.encode(payload,SECRET_KEY,algorithm="HS256")
def verify_token(token:str)->dict:
    return jwt.decode(token,SECRET_KEY,algorithms=["HS256"])
# creates the session 
def create_session(db:Session,user_id:int,refresh_token:str,expires_at,datetime
,ip_address:str = None , user_agent:str = None):
    db_session = Auth(
        user_id = user_id,
        refresh_token = refresh_token,
        ip_address = ip_address,
        user_agent = user_agent
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session
# deletes the session
def delete_session(db:Session,user_id:int):
    db_auth=db.query(Auth).filter(Auth.user_id==user_id).delete()
    db.commit()
    return
def verify_user(db:Session,email:str,password:str):
    user=db.query(User).filter(User.email==email).first()
    if not user or not verify_password(password,user.password):
        raise HTTPException(status_code=401,detail="Invalid Credintials")
    return user
def refresh_jwt(db:Session,refresh_token:str)-> str:
    session = db.query(Auth).filter(Auth.refresh_token==refresh_token).first()
    if not session:
        raise Exception("Invalid Refresh Token")
    if session.expires_at < datetime.now(timezone.utc):
        raise("Refresh Token Expired")
    
    new_token = create_access_token(session.user_id)
    return new_token

def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
):
    return get_user_from_access_token(db, credentials.credentials)

#Used to authorize the user that uploaded the book vecuase user id is a foregin key in book
# as uploader so it must know which book is which 
def get_current_user_multipart(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer_optional),
    access_token: Optional[str] = Form(
        None,
        description="Paste the JWT from /login here when using Swagger UI file upload (Authorization header is often omitted for multipart).",
    ),
):
    token = None
    if credentials is not None:
        token = credentials.credentials
    if not token and access_token:
        token = access_token
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Click Authorize, or paste access_token from /login into the form field below.",
        )
    return get_user_from_access_token(db, token)

def get_userid_from_email(db: Session, user_email: str) -> int | None:
    row = db.query(User).filter(User.email == user_email).first()
    if row is None:
        return None
    return row.id
def get_bookid_from_title(db: Session, book_title: str) -> int | None:
    row = db.query(Book).filter(Book.title == book_title).first()
    if row is None:
        return None
    return row.id