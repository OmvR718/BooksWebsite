from schema import UserCreate,UserRead,UserUpdate
from models import User
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
