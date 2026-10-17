from datetime import timedelta
from campus_grid.core.security import (
    create_access_token,
    decode_jwt,
    get_password_hash,
    verify_password,
)


def test_password_hashing():
    pwd = "SecureCampusPassword2026!"
    hashed = get_password_hash(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_lifecycle():
    subject = {"sub": "42", "email": "test@campus.edu", "role": "faculty"}
    token, exp = create_access_token(subject, expires_delta=timedelta(minutes=15))
    assert token is not None
    assert exp is not None

    decoded = decode_jwt(token)
    assert decoded is not None
    assert decoded["sub"] == "42"
    assert decoded["email"] == "test@campus.edu"
    assert decoded["role"] == "faculty"


def test_jwt_expired():
    subject = {"sub": "42", "email": "test@campus.edu", "role": "faculty"}
    # Token expired 5 minutes ago
    token, _ = create_access_token(subject, expires_delta=timedelta(minutes=-5))
    decoded = decode_jwt(token)
    assert decoded is None
