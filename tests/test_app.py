import copy
import pytest
from fastapi.testclient import TestClient

import src.app as app_module
from src.app import app

client = TestClient(app, raise_server_exceptions=True)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state after every test."""
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_all_activities(self):
        # Arrange - no setup needed; default data is restored by fixture

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
        assert len(response.json()) == 9

    def test_activity_has_required_fields(self):
        # Arrange - no setup needed

        # Act
        response = client.get("/activities")

        # Assert
        for activity in response.json().values():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_signup_success(self):
        # Arrange
        email = "new@mergington.edu"
        activity_name = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
        assert email in app_module.activities[activity_name]["participants"]

    def test_signup_unknown_activity_returns_404(self):
        # Arrange
        email = "new@mergington.edu"
        activity_name = "Nonexistent Club"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404

    def test_signup_already_registered_returns_400(self):
        # Arrange
        email = "michael@mergington.edu"  # already in Chess Club
        activity_name = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_signup_full_activity_returns_400(self):
        # Arrange
        activity_name = "Chess Club"
        activity = app_module.activities[activity_name]
        activity["participants"] = [
            f"student{i}@mergington.edu"
            for i in range(activity["max_participants"])
        ]

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "overflow@mergington.edu"},
        )

        # Assert
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_unregister_success(self):
        # Arrange
        email = "michael@mergington.edu"  # already in Chess Club
        activity_name = "Chess Club"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
        assert email not in app_module.activities[activity_name]["participants"]

    def test_unregister_unknown_activity_returns_404(self):
        # Arrange
        email = "michael@mergington.edu"
        activity_name = "Nonexistent Club"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404

    def test_unregister_not_registered_returns_404(self):
        # Arrange
        email = "notregistered@mergington.edu"
        activity_name = "Chess Club"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"].lower()
