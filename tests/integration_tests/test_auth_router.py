def test_sign_up_and_sign_in_flow(client):
    # 1. Sign up new student
    signup_payload = {
        "email": "newstudent@campus.edu",
        "password": "SecurePassword123!",
        "role": "student",
    }
    resp = client.post("/api/v1/auth/sign-up", json=signup_payload)
    assert resp.status_code == 201
    user_data = resp.json()
    assert user_data["email"] == "newstudent@campus.edu"
    assert user_data["role"] == "student"
    assert user_data["is_active"] is True
    assert "hashed_password" not in user_data

    # 2. Duplicate sign up fails with 409
    dup_resp = client.post("/api/v1/auth/sign-up", json=signup_payload)
    assert dup_resp.status_code == 409

    # 3. Sign in with correct password
    signin_payload = {
        "email": "newstudent@campus.edu",
        "password": "SecurePassword123!",
    }
    signin_resp = client.post("/api/v1/auth/sign-in", json=signin_payload)
    assert signin_resp.status_code == 200
    token_data = signin_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["user"]["email"] == "newstudent@campus.edu"
    token = token_data["access_token"]

    # 4. Sign in with wrong password fails with 401
    wrong_resp = client.post(
        "/api/v1/auth/sign-in",
        json={"email": "newstudent@campus.edu", "password": "WrongPassword!"},
    )
    assert wrong_resp.status_code == 401

    # 5. Get current user profile via /auth/me
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "newstudent@campus.edu"
