from __future__ import annotations
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import date, datetime, time, timedelta
from typing import List , Optional
# here we define the logic of how data is viewed inputted or outputted
# from the api into the database or vice versa example is user create we expect the user
# to be able to sign up and input these data the username the email and the password
class UserCreate(BaseModel):
    username:str
    password:str
    email:EmailStr
#here we define what can the user see even if he didn't input it himself like
# the date and time the account was created is the user active the user id etc... 
class UserRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    username:str
    email:str
    created_at:datetime
    updated_at:datetime
    is_active:bool
    books:List["BookRead"] = []
    
class UserUpdate(BaseModel):
    email:Optional[EmailStr] = None
    password:Optional[str] = None

class UserLogin(BaseModel):
    email:EmailStr
    password:str
    
class BookCreate(BaseModel):
    title:str
    description:str
    author_name:str
    visibilty:bool


class FileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    book_id: int
    file_url: str
    file_type: str
    checksum: str
    uploaded_at: datetime


class BookRead(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int
    title:str
    description:str
    author_name:str
    uploader:int
    visibilty:bool
    created_at:datetime
    updated_at:datetime
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    files: List[FileRead] = Field(default_factory=list)
