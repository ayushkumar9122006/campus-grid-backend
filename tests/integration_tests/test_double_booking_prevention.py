from datetime import datetime, timedelta, timezone


def test_single_quantity_resource_double_booking_prevention(client, student_auth_headers, student2_auth_headers):
    # Oscilloscope Rig B2 has total_quantity = 1
    res_list = client.get("/api/v1/resources", headers=student_auth_headers).json()["items"]
    rig = [r for r in res_list if "Oscilloscope" in r["name"]][0]
    assert rig["total_quantity"] == 1

    base_time = datetime.now(timezone.utc) + timedelta(days=10)
    t0 = base_time
    t1 = base_time + timedelta(hours=2)
    t2 = base_time + timedelta(hours=4)
    t3 = base_time + timedelta(hours=6)
    t4 = base_time + timedelta(hours=8)
    t5 = base_time + timedelta(hours=10)

    # 1. Student 1 books interval [t1, t3] -> SUCCEEDS
    primary_booking = client.post(
        "/api/v1/bookings",
        json={
            "resource_id": rig["id"],
            "start_time": t1.isoformat(),
            "end_time": t3.isoformat(),
        },
        headers=student_auth_headers,
    )
    assert primary_booking.status_code == 201

    # 2. Overlapping Attempt A: Exact same interval [t1, t3] -> MUST FAIL 409
    overlap_exact = client.post(
        "/api/v1/bookings",
        json={
            "resource_id": rig["id"],
            "start_time": t1.isoformat(),
            "end_time": t3.isoformat(),
        },
        headers=student2_auth_headers,
    )
    assert overlap_exact.status_code == 409
    assert "Double-booking prevented" in overlap_exact.json()["detail"]

    # 3. Overlapping Attempt B: Starts before, ends inside [t0, t2] -> MUST FAIL 409
    overlap_left = client.post(
        "/api/v1/bookings",
        json={
            "resource_id": rig["id"],
            "start_time": t0.isoformat(),
            "end_time": t2.isoformat(),
        },
        headers=student2_auth_headers,
    )
    assert overlap_left.status_code == 409
    assert "Double-booking prevented" in overlap_left.json()["detail"]

    # 4. Overlapping Attempt C: Starts inside, ends after [t2, t4] -> MUST FAIL 409
    overlap_right = client.post(
        "/api/v1/bookings",
        json={
            "resource_id": rig["id"],
            "start_time": t2.isoformat(),
            "end_time": t4.isoformat(),
        },
        headers=student2_auth_headers,
    )
    assert overlap_right.status_code == 409
    assert "Double-booking prevented" in overlap_right.json()["detail"]

    # 5. Overlapping Attempt D: Completely enveloped inside [t1 + 30m, t3 - 30m] -> MUST FAIL 409
    overlap_inner = client.post(
        "/api/v1/bookings",
        json={
            "resource_id": rig["id"],
            "start_time": (t1 + timedelta(minutes=30)).isoformat(),
            "end_time": (t3 - timedelta(minutes=30)).isoformat(),
        },
        headers=student2_auth_headers,
    )
    assert overlap_inner.status_code == 409

    # 6. Non-overlapping Adjacent Before: [t0, t1] -> MUST SUCCEED
    before_resp = client.post(
        "/api/v1/bookings",
        json={
            "resource_id": rig["id"],
            "start_time": t0.isoformat(),
            "end_time": t1.isoformat(),
        },
        headers=student2_auth_headers,
    )
    assert before_resp.status_code == 201

    # 7. Non-overlapping Adjacent After: [t3, t4] -> MUST SUCCEED
    after_resp = client.post(
        "/api/v1/bookings",
        json={
            "resource_id": rig["id"],
            "start_time": t3.isoformat(),
            "end_time": t4.isoformat(),
        },
        headers=student2_auth_headers,
    )
    assert after_resp.status_code == 201


def test_multi_quantity_resource_capacity_limits(client, student_auth_headers, student2_auth_headers, faculty_auth_headers):
    # Sony FX3 Cinema Camera Kit has total_quantity = 2
    res_list = client.get("/api/v1/resources", headers=student_auth_headers).json()["items"]
    camera = [r for r in res_list if "Sony FX3" in r["name"]][0]
    assert camera["total_quantity"] == 2

    base_time = datetime.now(timezone.utc) + timedelta(days=20)
    slot_start = base_time + timedelta(hours=14)
    slot_end = base_time + timedelta(hours=18)

    # 1. Student 1 books 1st camera -> SUCCEEDS
    b1 = client.post(
        "/api/v1/bookings",
        json={
            "resource_id": camera["id"],
            "start_time": slot_start.isoformat(),
            "end_time": slot_end.isoformat(),
        },
        headers=student_auth_headers,
    )
    assert b1.status_code == 201

    # 2. Student 2 books 2nd camera for overlapping interval -> SUCCEEDS
    b2 = client.post(
        "/api/v1/bookings",
        json={
            "resource_id": camera["id"],
            "start_time": (slot_start + timedelta(hours=1)).isoformat(),
            "end_time": (slot_end - timedelta(hours=1)).isoformat(),
        },
        headers=student2_auth_headers,
    )
    assert b2.status_code == 201

    # 3. Third booking during same time interval exceeds quantity limit (2/2) -> MUST FAIL 409
    b3_fail = client.post(
        "/api/v1/bookings",
        json={
            "resource_id": camera["id"],
            "start_time": (slot_start + timedelta(hours=2)).isoformat(),
            "end_time": (slot_end - timedelta(minutes=30)).isoformat(),
        },
        headers=faculty_auth_headers,
    )
    assert b3_fail.status_code == 409
    assert "Double-booking prevented" in b3_fail.json()["detail"]

    # 4. If Student 1 cancels their booking, slot frees up -> 3rd attempt SUCCEEDS
    cancel_resp = client.post(f"/api/v1/bookings/{b1.json()['id']}/cancel", headers=student_auth_headers)
    assert cancel_resp.status_code == 200

    b3_retry = client.post(
        "/api/v1/bookings",
        json={
            "resource_id": camera["id"],
            "start_time": (slot_start + timedelta(hours=2)).isoformat(),
            "end_time": (slot_end - timedelta(minutes=30)).isoformat(),
        },
        headers=faculty_auth_headers,
    )
    assert b3_retry.status_code == 201


def test_maintenance_resource_rejected(client, student_auth_headers):
    # Electron Microscope Beta is in maintenance
    res_list = client.get("/api/v1/resources", headers=student_auth_headers).json()["items"]
    microscope = [r for r in res_list if "Electron Microscope" in r["name"]][0]
    assert microscope["status"] == "maintenance"

    base_time = datetime.now(timezone.utc) + timedelta(days=12)
    resp = client.post(
        "/api/v1/bookings",
        json={
            "resource_id": microscope["id"],
            "start_time": base_time.isoformat(),
            "end_time": (base_time + timedelta(hours=2)).isoformat(),
        },
        headers=student_auth_headers,
    )
    assert resp.status_code == 400
    assert "unavailable for reservations" in resp.json()["detail"]
