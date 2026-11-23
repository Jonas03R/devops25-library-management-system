import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.library import LibraryService

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_library(monkeypatch):
    monkeypatch.setattr("app.main.library", LibraryService())


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_add_endpoint():
    response = client.get("/api/add?a=2&b=3")
    assert response.status_code == 200
    assert response.json()["result"] == 5


def test_catalogue_search_returns_matching_books():
    client.post("/api/books", json={"title": "The Hobbit", "author": "J.R.R. Tolkien"})
    client.post("/api/books", json={"title": "Dune", "author": "Frank Herbert"})

    response = client.get("/api/books", params={"q": "hobbit"})

    assert response.status_code == 200
    assert [book["title"] for book in response.json()] == ["The Hobbit"]


def test_cannot_borrow_a_missing_or_already_borrowed_book():
    user = client.post(
        "/api/users", json={"name": "Ada Lovelace", "email": "ada@example.test"}
    ).json()
    book = client.post(
        "/api/books", json={"title": "The Hobbit", "author": "J.R.R. Tolkien"}
    ).json()

    missing = client.post("/api/loans", json={"book_id": 99, "user_id": user["id"]})
    unknown_user = client.post("/api/loans", json={"book_id": book["id"], "user_id": 99})
    first_loan = client.post(
        "/api/loans", json={"book_id": book["id"], "user_id": user["id"]}
    )
    second_loan = client.post(
        "/api/loans", json={"book_id": book["id"], "user_id": user["id"]}
    )

    assert missing.status_code == 404
    assert unknown_user.status_code == 404
    assert first_loan.status_code == 201
    assert second_loan.status_code == 409


def test_returned_book_is_available_again():
    user = client.post(
        "/api/users", json={"name": "Ada Lovelace", "email": "ada@example.test"}
    ).json()
    book = client.post(
        "/api/books", json={"title": "The Hobbit", "author": "J.R.R. Tolkien"}
    ).json()
    loan = client.post(
        "/api/loans", json={"book_id": book["id"], "user_id": user["id"]}
    ).json()

    returned = client.post(f"/api/loans/{loan['id']}/return")

    assert returned.status_code == 200
    assert returned.json()["returned"] is True
    assert [item["title"] for item in client.get("/api/books/available").json()] == [
        "The Hobbit"
    ]
