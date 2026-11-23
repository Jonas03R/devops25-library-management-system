import pytest

from app.library import (
    BookUnavailableError,
    LibraryItemNotFoundError,
    LibraryService,
    LoanAlreadyReturnedError,
)
from app.service import add, divide


def test_add():
    assert add(2, 3) == 5


def test_divide():
    assert divide(10, 2) == 5


def test_divide_by_zero():
    with pytest.raises(ValueError):
        divide(10, 0)


def test_library_search_matches_title_and_author_without_case_sensitivity():
    library = LibraryService()
    library.add_book("The Hobbit", "J.R.R. Tolkien")
    library.add_book("Dune", "Frank Herbert")

    assert [book.title for book in library.list_books(query="TOLKIEN")] == ["The Hobbit"]
    assert [book.title for book in library.list_books(query="du")] == ["Dune"]


def test_library_rejects_missing_or_already_borrowed_books():
    library = LibraryService()
    user = library.add_user("Ada Lovelace", "ada@example.test")
    book = library.add_book("The Hobbit", "J.R.R. Tolkien")

    with pytest.raises(LibraryItemNotFoundError, match="Book not found"):
        library.borrow_book(99, user.id)

    library.borrow_book(book.id, user.id)
    with pytest.raises(BookUnavailableError):
        library.borrow_book(book.id, user.id)


def test_returned_book_becomes_available_and_cannot_be_returned_twice():
    library = LibraryService()
    user = library.add_user("Ada Lovelace", "ada@example.test")
    book = library.add_book("The Hobbit", "J.R.R. Tolkien")
    loan = library.borrow_book(book.id, user.id)
    assert library.list_books(available_only=True) == []

    library.return_book(loan.id)

    assert library.list_books(available_only=True) == [book]
    with pytest.raises(LoanAlreadyReturnedError):
        library.return_book(loan.id)
