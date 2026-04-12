from fastapi import APIRouter,Depends,HTTPException,Request
from sqlalchemy.orm import Session
from db import get_db
from models import User
from schema import UserCreate,UserLogin,UserUpdate,UserRead
from crud import create_user, read_user, update_user as update_user_in_db, delete_user as delete_user_in_db
from utils import (
    verify_user,
    create_access_token,
    create_session,
    get_userid_from_email,
)
import secrets
from datetime import timezone,datetime,timedelta
ACCESS_TOKEN_EXPIRY_MINUTES=60

router = APIRouter()
@router.post("/signup")
def signup(user:UserCreate,db:Session=Depends(get_db)):
    #Check if user already exists
    existing_user = db.query(User).filter(User.email==user.email).first()
    if existing_user:
        raise HTTPException(status_code=400,detail='User Already Has an Account')
    #add new user in db 
    new_user = create_user(db,user)
    return {"id":new_user.id,"email":new_user.email}

@router.post("/login")
def login(user:UserLogin,request:Request,db:Session=Depends(get_db)):
    #1-Verify Credentials
    user_obj = verify_user(db,user.email,user.password)
    #2 Generate Tokens
    access_token=create_access_token(user_obj.id)
    refersh_token=secrets.token_urlsafe(32)
    #3 extract info 
    ip = request.headers.get("X-Forwarded-For",request.client.host)
    user_agent = request.headers.get("user-agent")
    
    #4 store data of a session 
    create_session(db,
                   user_id=user_obj.id,
                   refresh_token=refersh_token,
                   ip_address=ip,
                   user_agent=user_agent
                   ,datetime=datetime.now(timezone.utc).timestamp(),
                   expires_at=(datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES))
                   )
    return {
        "access_token":access_token,
        "refresh_token":refersh_token,
        "token_type":"bearer"
    }
    
@router.get("/get_user")
def user_search(user_id:int,db:Session=Depends(get_db)):
    user_obj=read_user(db,user_id)
    if user_obj is None:
        raise HTTPException(status_code=404,detail="User Not Found")
    return user_obj

@router.delete('/delete_user')
def delete_user_route(user_id:int,db:Session=Depends(get_db)):
    if not delete_user_in_db(db,user_id):
        raise HTTPException(status_code=404,detail="User Not Found")
    return {"ok": True}

@router.put("/update_user")
def update_user_route(user:UserUpdate,db:Session=Depends(get_db)):
    if user.email is None:
        raise HTTPException(status_code=400,detail="email is required to identify the user")
    user_id = get_userid_from_email(db, user.email)
    if user_id is None:
        raise HTTPException(status_code=404,detail="User Not Found")
    updated = update_user_in_db(db, user, user_id)
    if updated is None:
        raise HTTPException(status_code=404,detail="User Not Found")
    return {"email": updated.email, "username": updated.username}


