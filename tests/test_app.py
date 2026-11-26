import copy

import pytest
from fastapi.testclient import TestClient

import src.app as api


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "activities", copy.deepcopy(api.activities))
    with TestClient(api.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data_and_disables_caching(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["Chess Club"] == {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    }


def test_signup_adds_student_to_activity(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new-student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new-student@mergington.edu for Chess Club"
    }
    assert "new-student@mergington.edu" in client.get(
        "/activities"
    ).json()["Chess Club"]["participants"]


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_student(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up"}


def test_unregister_removes_student_from_activity(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Removed michael@mergington.edu from Chess Club"
    }
    assert "michael@mergington.edu" not in client.get(
        "/activities"
    ).json()["Chess Club"]["participants"]


@pytest.mark.parametrize(
    ("activity_name", "email", "expected_detail"),
    [
        ("Unknown Club", "student@mergington.edu", "Activity not found"),
        (
            "Chess Club",
            "not-signed-up@mergington.edu",
            "Student is not signed up for this activity",
        ),
    ],
)
def test_unregister_returns_not_found_for_unknown_activity_or_student(
    client, activity_name, email, expected_detail
):
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": expected_detail}
