import pytest
from pydantic import ValidationError
from app.schemas import UserCreate

def test_password_too_short():
    with pytest.raises(ValidationError) as exc:
        UserCreate(email="test@example.com", password="Short1!", org_name="Test")
    assert "8 characters or more" in str(exc.value)

def test_password_no_digits():
    with pytest.raises(ValidationError) as exc:
        UserCreate(email="test@example.com", password="NoDigitsHere!", org_name="Test")
    assert "at least one digit" in str(exc.value)

def test_password_no_uppercase():
    with pytest.raises(ValidationError) as exc:
        UserCreate(email="test@example.com", password="nouppercase1!", org_name="Test")
    assert "at least one uppercase" in str(exc.value)

def test_password_no_lowercase():
    with pytest.raises(ValidationError) as exc:
        UserCreate(email="test@example.com", password="NOLOWERCASE1!", org_name="Test")
    assert "at least one lowercase" in str(exc.value)

def test_password_no_special():
    with pytest.raises(ValidationError) as exc:
        UserCreate(email="test@example.com", password="NoSpecialChar1", org_name="Test")
    assert "at least one special" in str(exc.value)

def test_password_valid():
    user = UserCreate(email="test@example.com", password="StrongPassword1!", org_name="Test")
    assert user.password == "StrongPassword1!"
