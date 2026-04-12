from fastapi import FastAPI
from routers import books, files, users

app = FastAPI()

app.include_router(users.router)
app.include_router(books.router)
app.include_router(files.router)