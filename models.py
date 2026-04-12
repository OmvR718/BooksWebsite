from sqlalchemy.orm import declarative_base,relationship
from sqlalchemy import Integer , Column , String,DateTime,Boolean,ForeignKey
from datetime import datetime , timezone,timedelta
Base = declarative_base()

## defines the user table with its columns
 
class User(Base):
    __tablename__="users"
    __table_args__={"schema":"app_schema"}
    id = Column(Integer,primary_key=True)
    username=Column(String,unique=True,nullable=False)
    email=Column(String,unique=True)
    password=Column(String,nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean,default=True)
    
## defines books tables with its columns
class Book(Base):
    __tablename__="books"
    __table_args__={"schema":"app_schema"}
    id = Column(Integer,primary_key=True)
    title=Column(String,unique=True,nullable=False)
    description=Column(String,nullable=False)
    author_name=Column(String,nullable=False)
    uploader=Column(Integer,ForeignKey("app_schema.users.id"),nullable=False)
    owner=relationship("User",back_populates="books") ## defines the 1:M mapping between users and books 
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    visibilty=Column(Boolean,default=True)
    
## defines the 1:M mapping between users and books
# kept outside the function to avoid circular refrences
User.books=relationship("Book",back_populates="owner")

class File(Base):
    __tablename__="files"
    __table_args__={"schema":"app_schema"}
    id=Column(Integer,primary_key=True)
    file_url=Column(String(255),nullable=False)
    book_id=Column(Integer,ForeignKey("app_schema.books.id"),nullable=False,index=True)
    book=relationship("Book",back_populates="files")
    file_type=Column(String,nullable=False)
    checksum=Column(String(64),nullable=False)
    uploaded_at=Column(DateTime, default=lambda: datetime.now(timezone.utc))
#same as before kept to avoid circular refrences
Book.files = relationship(
    "File",
    back_populates="book",
    cascade="all, delete-orphan",
)
#defines the authentication/session table where the backend of the client can use to validate users
class Auth(Base):
    __tablename__="auths"
    __table_args__={"schema":"app_schema"}
    s_id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("app_schema.users.id"),nullable=False,index=True)
    user=relationship("User",back_populates="auths")
    refresh_token=Column(String(255),nullable=False,index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, default=lambda: datetime.now(timezone.utc)+timedelta(days=7))
    ip_address=Column(String)
    user_agent=Column(String,nullable=True)
## kept to avoid circular refrence 
User.auths=relationship("Auth",back_populates="user")