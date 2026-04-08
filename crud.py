from schema import UserCreate,UserUpdate,BookRead,BookCreate,FileRead
from models import User,Book,File
from sqlalchemy.orm import Session
## Function that creates the user in the databse 
def create_user(db:Session,user:UserCreate):
    db_user = User(**user.model_dump())# --> unpacking the dictionary to key value arguments 
    # like {'name':'john','age': 17} becomes User('name' = 'john','age'= 17) we instansiate 
    # the object with values inside dictionary into the object it matches into 
    # names in the db 
    db.add(db_user) # --> here we add the user to the data base 
    db.commit() # --> here we commit it to the database
    db.refresh(db_user)
    return db_user
# as name suggests updates the user in the databse using the fact that pydantic classes
# are serialized as python dicts 
def update_user(db:Session,user_update:UserUpdate,user_id:int):
    db_user = db.query(User).filter(User.id==user_id).first()
    update_data = user_update.model_dump(exclude_unset=True)
    for k , v in update_data.items():
        setattr(db_user,k,v)
    db.commit()
    db.refresh(db_user)
    return db_user
#as name suggest reads user from database
def read_user(db:Session,user_id:int):
    db_user = db.query(User).filter(User.id==user_id).first()
    return db_user
def delete_user(db:Session,user_id:int):
    db_user=db.query(User).filter(User.id==user_id)
    if not db_user:
        return None
    db.delete(db_user)
    db.refresh()
    return
#Now we come to the part of Book functions
def create_book(db:Session,book:BookCreate):
    db_book = Book(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book
def read_book(db:Session,book_id:int):
    db_book=db.query(Book).filter(Book.id==book_id).first()
    return db_book
def create_file(db:Session):
    pass ## here we use the util functions that create the file information

def read_file(db:Session,file_id:int):
    db_file=db.query(File).filter(File.id==file_id)
    return db_file

## here we write the functions which use the join between two tables they are not many since
## we didn't define alot of realtionships 
def user_uploaded_books(db:Session,,user_id:int):
    return db.query(Book).filter(Book.uploader==user_id).all()
## returns 1 file per book
def file_book(db:Session,book_id):
    return db.query(File).filter(File.book_id==book_id).first()