import bcrypt
import jwt
import os
from datetime import timedelta , datetime,timezone
from sqlalchemy.orm import Session
from models import User , Auth
from fastapi import HTTPException

SECRET_KEY= os.environ.get("SECRET_KEY")
ACCESS_TOKEN_EXPIRY_MINUTES=60
## hashes the password
def hash_password(password:str) -> str:
    return bcrypt.hashpw(password.encode(),bcrypt.gensalt()).decode()
# compares entered password to hashed password  
def verify_password(password:str,hashed:str) -> bool:
    return bcrypt.checkpw(password.encode(),hashed.encode())
def create_access_token(user_id:int) -> str:
    payload = {
        "sub":user_id,
        "iat":datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc)+timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES)
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