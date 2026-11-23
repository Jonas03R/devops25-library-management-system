from dataclasses import dataclass
from threading import Lock


@dataclass
class Book:
    id: int
    title: str
    author: str
    isbn: str | None
    available: bool = True


@dataclass
class User:
    id: int
    name: str
    email: str


@dataclass
class Loan:
    id: int
    book_id: int
    user_id: int
    returned: bool = False


class LibraryError(Exception):
    status_code = 400


class LibraryItemNotFoundError(LibraryError):
    status_code = 404


class BookUnavailableError(LibraryError):
    status_code = 409


class LoanAlreadyReturnedError(LibraryError):
    status_code = 409


class LibraryService:
    def __init__(self) -> None:
        self._books: dict[int, Book] = {}
        self._users: dict[int, User] = {}
        self._loans: dict[int, Loan] = {}
        self._next_book_id = 1
        self._next_user_id = 1
        self._next_loan_id = 1
        self._lock = Lock()

    def add_book(self, title: str, author: str, isbn: str | None = None) -> Book:
        with self._lock:
            book = Book(self._next_book_id, title, author, isbn)
            self._books[book.id] = book
            self._next_book_id += 1
            return book

    def list_books(self, query: str | None = None, available_only: bool = False) -> list[Book]:
        normalized_query = query.casefold().strip() if query else None
        with self._lock:
            return [
                book
                for book in self._books.values()
                if (not available_only or book.available)
                and (
                    normalized_query is None
                    or normalized_query in book.title.casefold()
                    or normalized_query in book.author.casefold()
                )
            ]

    def add_user(self, name: str, email: str) -> User:
        with self._lock:
            user = User(self._next_user_id, name, email)
            self._users[user.id] = user
            self._next_user_id += 1
            return user

    def list_users(self) -> list[User]:
        with self._lock:
            return list(self._users.values())

    def borrow_book(self, book_id: int, user_id: int) -> Loan:
        with self._lock:
            book = self._books.get(book_id)
            if book is None:
                raise LibraryItemNotFoundError("Book not found")
            if user_id not in self._users:
                raise LibraryItemNotFoundError("User not found")
            if not book.available:
                raise BookUnavailableError("Book is already on loan")

            loan = Loan(self._next_loan_id, book_id, user_id)
            self._loans[loan.id] = loan
            self._next_loan_id += 1
            book.available = False
            return loan

    def return_book(self, loan_id: int) -> Loan:
        with self._lock:
            loan = self._loans.get(loan_id)
            if loan is None:
                raise LibraryItemNotFoundError("Loan not found")
            if loan.returned:
                raise LoanAlreadyReturnedError("Loan has already been returned")

            loan.returned = True
            self._books[loan.book_id].available = True
            return loan
