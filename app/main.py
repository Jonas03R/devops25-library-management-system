from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.library import LibraryError, LibraryService
from app.service import add, divide

app = FastAPI(title="Library Management System")
library = LibraryService()


class BookCreate(BaseModel):
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    isbn: str | None = None


class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=1)


class BorrowRequest(BaseModel):
    book_id: int = Field(gt=0)
    user_id: int = Field(gt=0)


@app.exception_handler(LibraryError)
async def handle_library_error(_, exc: LibraryError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/add")
def api_add(a: int, b: int):
    return {"result": add(a, b)}


@app.get("/api/divide")
def api_divide(a: float, b: float):
    return {"result": divide(a, b)}


@app.post("/api/books", status_code=201)
def create_book(book: BookCreate):
    return library.add_book(book.title, book.author, book.isbn)


@app.get("/api/books")
def list_books(q: str | None = None, available: bool = False):
    return library.list_books(query=q, available_only=available)


@app.get("/api/books/available")
def list_available_books():
    return library.list_books(available_only=True)


@app.post("/api/users", status_code=201)
def create_user(user: UserCreate):
    return library.add_user(user.name, user.email)


@app.get("/api/users")
def list_users():
    return library.list_users()


@app.post("/api/loans", status_code=201)
def borrow_book(request: BorrowRequest):
    return library.borrow_book(request.book_id, request.user_id)


@app.post("/api/loans/{loan_id}/return")
def return_book(loan_id: int):
    return library.return_book(loan_id)
