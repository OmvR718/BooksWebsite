from schema import UserCreate,UserUpdate,BookRead,BookCreate,FileRead
from models import User,Book,File
from sqlalchemy.orm import Session
from utils import hash_password
## Function that creates the user in the databse 
def create_user(db:Session,user:UserCreate):
    hashed_password=hash_password(user.password)
    db_user = User(
                   email=user.email,
                   username=user.username,
                   password=hashed_password
                   
                   )
    db.add(db_user) # --> here we add the user to the data base 
    db.commit() # --> here we commit it to the database
    db.refresh(db_user)
    return db_user
# as name suggests updates the user in the database using the fact that pydantic classes
# are serialized as python dicts 
def update_user(db: Session, user_update: UserUpdate, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        return None
    update_data = user_update.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if k == "password" and v is not None:
            v = hash_password(v)
        setattr(db_user, k, v)
    db.commit()
    db.refresh(db_user)
    return db_user
#as name suggest reads user from database
def read_user(db:Session,user_id:int):
    db_user = db.query(User).filter(User.id==user_id).first()
    if not db_user:
        return None
    
    return db_user
def delete_user(db: Session, user_id: int) -> bool:
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        return False
    db.delete(db_user)
    db.commit()
    return True
#Now we come to the part of Book functions
def create_book(db: Session, title: str, description: str, 
        author_name: str,uploader_id: int,visibilty: bool = True):
    db_book = Book(
        title=title,
        description=description,
        author_name=author_name,
        uploader=uploader_id 
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book
def read_book(db:Session,book_id:int):
    db_book=db.query(Book).filter(Book.id==book_id).first()
    if not db_book:
        return None
    return db_book
def create_file_record(
    db: Session,
    book_id: int,
    file_url: str,
    file_type: str,
    checksum: str,
):
    db_file = File(
        book_id=book_id,
        file_url=file_url,
        file_type=file_type,
        checksum=checksum,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def get_file_for_book(db: Session, book_id: int):
    return db.query(File).filter(File.book_id == book_id).first()


def read_file(db: Session, file_id: int):
    return db.query(File).filter(File.id == file_id).first()

## here we write the functions which use the join between two tables they are not many since
## we didn't define alot of reltionships 
def user_uploaded_books(db:Session,user_id:int):
    return db.query(Book).filter(Book.uploader==user_id).all()
## returns 1 file per book
def file_book(db:Session,book_id):
    return db.query(File).filter(File.book_id==book_id).first()