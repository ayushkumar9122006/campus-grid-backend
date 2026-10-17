def test_student_forbidden_from_admin_user_management(client, student_auth_headers):
    # Student attempts to access /users
    resp = client.get("/api/v1/users", headers=student_auth_headers)
    assert resp.status_code == 403
    assert "Operation restricted to roles [admin]" in resp.json()["detail"]


def test_admin_can_access_user_management(client, admin_auth_headers):
    resp = client.get("/api/v1/users", headers=admin_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total_count"] >= 4


def test_student_cannot_create_resource(client, student_auth_headers):
    payload = {
        "name": "Unauthorized Laser Cutter",
        "category": "lab_equipment",
        "total_quantity": 1,
    }
    resp = client.post("/api/v1/resources", json=payload, headers=student_auth_headers)
    assert resp.status_code == 403
    assert "Operation restricted to roles [faculty, admin]" in resp.json()["detail"]


def test_faculty_can_create_resource(client, faculty_auth_headers):
    payload = {
        "name": "Audio Engineering Console Pro",
        "category": "media_gear",
        "total_quantity": 3,
    }
    resp = client.post("/api/v1/resources", json=payload, headers=faculty_auth_headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "Audio Engineering Console Pro"
    assert resp.json()["total_quantity"] == 3


def test_student_cannot_access_audit_logs(client, student_auth_headers):
    resp = client.get("/api/v1/audit-logs", headers=student_auth_headers)
    assert resp.status_code == 403


def test_faculty_can_access_audit_logs(client, faculty_auth_headers):
    resp = client.get("/api/v1/audit-logs", headers=faculty_auth_headers)
    assert resp.status_code == 200
    assert "items" in resp.json()


def test_admin_can_update_user_role(client, admin_auth_headers):
    # Retrieve user list to pick student 1
    users_resp = client.get("/api/v1/users", headers=admin_auth_headers)
    student1 = [u for u in users_resp.json()["items"] if u["email"] == "student1@campus.edu"][0]

    # Promote student to faculty
    patch_resp = client.patch(
        f"/api/v1/users/{student1['id']}",
        json={"role": "faculty"},
        headers=admin_auth_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["role"] == "faculty"
