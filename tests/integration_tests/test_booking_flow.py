from datetime import datetime, timedelta, timezone


def test_student_and_faculty_booking_lifecycle(
    client,
    student_auth_headers,
    student2_auth_headers,
    faculty_auth_headers,
):
    # Retrieve available resources
    res_list = client.get("/api/v1/resources", headers=student_auth_headers).json()["items"]
    sony_camera = [r for r in res_list if "Sony FX3" in r["name"]][0]

    now = datetime.now(timezone.utc)
    start_time = now + timedelta(days=1, hours=10)
    end_time = now + timedelta(days=1, hours=14)

    # 1. Student 1 books Sony FX3
    book_payload = {
        "resource_id": sony_camera["id"],
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
    }
    b1_resp = client.post("/api/v1/bookings", json=book_payload, headers=student_auth_headers)
    assert b1_resp.status_code == 201
    b1_data = b1_resp.json()
    assert b1_data["status"] == "pending"  # Student bookings start as pending
    b1_id = b1_data["id"]

    # 2. Student 2 cannot inspect Student 1's booking
    forbidden_resp = client.get(f"/api/v1/bookings/{b1_id}", headers=student2_auth_headers)
    assert forbidden_resp.status_code == 403
    assert "Access to this booking record is restricted to the booking owner" in forbidden_resp.json()["detail"]

    # 3. Faculty CAN inspect Student 1's booking
    fac_view_resp = client.get(f"/api/v1/bookings/{b1_id}", headers=faculty_auth_headers)
    assert fac_view_resp.status_code == 200

    # 4. Student 1 CANNOT approve their own booking
    student_approve = client.post(f"/api/v1/bookings/{b1_id}/approve", headers=student_auth_headers)
    assert student_approve.status_code == 403

    # 5. Faculty APPROVES Student 1's booking
    fac_approve = client.post(f"/api/v1/bookings/{b1_id}/approve", headers=faculty_auth_headers)
    assert fac_approve.status_code == 200
    assert fac_approve.json()["status"] == "approved"

    # 6. Student returns the equipment upon check-in
    return_resp = client.post(f"/api/v1/bookings/{b1_id}/return", headers=student_auth_headers)
    assert return_resp.status_code == 200
    assert return_resp.json()["status"] == "returned"


def test_faculty_auto_approved_booking(client, faculty_auth_headers):
    res_list = client.get("/api/v1/resources", headers=faculty_auth_headers).json()["items"]
    arena = [r for r in res_list if "Robotics Arena" in r["name"]][0]

    now = datetime.now(timezone.utc)
    start_time = now + timedelta(days=2, hours=9)
    end_time = now + timedelta(days=2, hours=12)

    payload = {
        "resource_id": arena["id"],
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
    }
    resp = client.post("/api/v1/bookings", json=payload, headers=faculty_auth_headers)
    assert resp.status_code == 201
    assert resp.json()["status"] == "approved"  # Faculty reservations are pre-approved


def test_student_booking_visibility_isolation(client, student_auth_headers, student2_auth_headers):
    res_list = client.get("/api/v1/resources", headers=student_auth_headers).json()["items"]
    rig = [r for r in res_list if "Oscilloscope" in r["name"]][0]

    now = datetime.now(timezone.utc)
    # Student 2 creates a booking
    payload = {
        "resource_id": rig["id"],
        "start_time": (now + timedelta(days=5, hours=10)).isoformat(),
        "end_time": (now + timedelta(days=5, hours=12)).isoformat(),
    }
    b2_resp = client.post("/api/v1/bookings", json=payload, headers=student2_auth_headers)
    assert b2_resp.status_code == 201

    # Student 1 lists bookings: Must NOT see Student 2's booking!
    s1_bookings = client.get("/api/v1/bookings", headers=student_auth_headers).json()["items"]
    for b in s1_bookings:
        assert b["user_id"] != b2_resp.json()["user_id"]
