import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db, Base

# ตั้งค่าฐานข้อมูลสำหรับการทดสอบ
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Unit Tests

def test_create_and_delete_user():
    # สร้างผู้ใช้
    response = client.post("/users/", params={"username": "testuser", "fullname": "Test User"})
    assert response.status_code == 200
    user_id = response.json()["id"]

    # ตรวจสอบว่าผู้ใช้ถูกสร้างแล้ว
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

    # ลบผู้ใช้
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 200

    # ตรวจสอบว่าผู้ใช้ถูกลบแล้ว
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 404

def test_create_and_delete_book():
    # สร้างหนังสือ
    response = client.post("/books/", params={"title": "Test Book", "firstauthor": "Test Author", "isbn": "1234567890"})
    assert response.status_code == 200
    book_id = response.json()["id"]

    # ตรวจสอบว่าหนังสือถูกสร้างแล้ว
    response = client.get(f"/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Book"

    # ลบหนังสือ
    response = client.delete(f"/books/{book_id}")
    assert response.status_code == 200

    # ตรวจสอบว่าหนังสือถูกลบแล้ว
    response = client.get(f"/books/{book_id}")
    assert response.status_code == 404

# Integration Tests

def test_create_borrowlist():
    # สร้างผู้ใช้
    user_response = client.post("/users/", params={"username": "borrower", "fullname": "Borrower User"})
    user_id = user_response.json()["id"]

    # สร้างหนังสือ
    book_response = client.post("/books/", params={"title": "Borrowed Book", "firstauthor": "Author", "isbn": "0987654321"})
    book_id = book_response.json()["id"]

    # สร้างรายการยืม
    borrow_response = client.post("/borrowlist/", params={"user_id": user_id, "book_id": book_id})
    assert borrow_response.status_code == 200
    assert borrow_response.json()["user_id"] == user_id
    assert borrow_response.json()["book_id"] == book_id

def test_get_user_borrowlist():
    # สร้างผู้ใช้
    user_response = client.post("/users/", params={"username": "borrower2", "fullname": "Borrower User 2"})
    user_id = user_response.json()["id"]

    # สร้างหนังสือ
    book_response = client.post("/books/", params={"title": "Another Book", "firstauthor": "Another Author", "isbn": "1122334455"})
    book_id = book_response.json()["id"]

    # สร้างรายการยืม
    client.post("/borrowlist/", params={"user_id": user_id, "book_id": book_id})

    # ดึงรายการยืมของผู้ใช้
    borrow_list_response = client.get(f"/borrowlist/{user_id}")
    assert borrow_list_response.status_code == 200
    assert len(borrow_list_response.json()) > 0
    assert borrow_list_response.json()[0]["user_id"] == user_id
    assert borrow_list_response.json()[0]["book_id"] == book_id