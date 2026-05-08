"""
FastAPI endpoint tests using the AAA (Arrange-Act-Assert) pattern.
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_redirects_to_index(self, client):
        """Test that GET / redirects to /static/index.html"""
        # Arrange
        expected_redirect_url = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_redirect_url


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        # Arrange
        expected_activity_names = [
            "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
            "Soccer Club", "Art Club", "Drama Club", "Debate Club", "Science Club"
        ]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert all(name in data for name in expected_activity_names)

    def test_get_activities_returns_correct_structure(self, client):
        """Test that activities have the expected structure"""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(activity_data.keys())
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)

    def test_get_activities_reflects_participant_changes(self, client):
        """Test that GET /activities reflects signup changes"""
        # Arrange
        activity_name = "Basketball Team"
        email = "newstudent@mergington.edu"

        # Act - Sign up first
        client.post(f"/activities/{activity_name}/signup?email={email}", follow_redirects=False)

        # Assert - Get activities and verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert email in data[activity_name]["participants"]


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success_adds_participant(self, client):
        """Test successful signup adds participant to activity"""
        # Arrange
        activity_name = "Basketball Team"
        email = "newplayer@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            follow_redirects=False
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_signup_activity_not_found(self, client):
        """Test signup fails when activity doesn't exist"""
        # Arrange
        activity_name = "NonExistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            follow_redirects=False
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_already_registered(self, client):
        """Test signup fails when student is already registered"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already registered

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            follow_redirects=False
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student already signed up"

    def test_signup_multiple_activities(self, client):
        """Test same student can sign up for multiple activities"""
        # Arrange
        email = "multiplelover@mergington.edu"
        activities = ["Basketball Team", "Soccer Club"]

        # Act - Sign up for multiple activities
        for activity_name in activities:
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}",
                follow_redirects=False
            )
            assert response.status_code == 200

        # Assert - Verify student is in both activities
        response = client.get("/activities")
        data = response.json()
        for activity_name in activities:
            assert email in data[activity_name]["participants"]


class TestDeleteParticipantEndpoint:
    """Tests for the DELETE /activities/{activity_name}/participants/{email} endpoint."""

    def test_delete_participant_success(self, client):
        """Test successful deletion of participant from activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}",
            follow_redirects=False
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]

    def test_delete_participant_removed_from_list(self, client):
        """Test that deleted participant no longer appears in activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        client.delete(f"/activities/{activity_name}/participants/{email}")

        # Assert - Verify participant is no longer in the activity
        response = client.get("/activities")
        data = response.json()
        assert email not in data[activity_name]["participants"]

    def test_delete_activity_not_found(self, client):
        """Test deletion fails when activity doesn't exist"""
        # Arrange
        activity_name = "NonExistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}",
            follow_redirects=False
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_delete_participant_not_found(self, client):
        """Test deletion fails when participant not in activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "notamember@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}",
            follow_redirects=False
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Participant not found in this activity"

    def test_delete_then_signup_again(self, client):
        """Test that student can sign up again after being removed"""
        # Arrange
        activity_name = "Basketball Team"
        email = "player@mergington.edu"

        # Act - Sign up
        client.post(f"/activities/{activity_name}/signup?email={email}")

        # Delete
        response_delete = client.delete(f"/activities/{activity_name}/participants/{email}")
        assert response_delete.status_code == 200

        # Sign up again
        response_signup = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response_signup.status_code == 200
        response_activities = client.get("/activities")
        data = response_activities.json()
        assert email in data[activity_name]["participants"]


class TestIntegrationScenarios:
    """Integration tests combining multiple endpoints."""

    def test_full_signup_and_delete_workflow(self, client):
        """Test complete workflow: get activities -> signup -> delete -> get activities"""
        # Arrange
        activity_name = "Soccer Club"
        email = "integration@mergington.edu"

        # Act - Get initial state
        response_initial = client.get("/activities")
        initial_count = len(response_initial.json()[activity_name]["participants"])

        # Sign up
        response_signup = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response_signup.status_code == 200

        # Verify signup
        response_after_signup = client.get("/activities")
        after_signup_count = len(response_after_signup.json()[activity_name]["participants"])

        # Delete
        response_delete = client.delete(f"/activities/{activity_name}/participants/{email}")
        assert response_delete.status_code == 200

        # Verify deletion
        response_after_delete = client.get("/activities")
        after_delete_count = len(response_after_delete.json()[activity_name]["participants"])

        # Assert
        assert after_signup_count == initial_count + 1
        assert after_delete_count == initial_count

    def test_state_isolation_between_tests(self, client):
        """
        Test that each test gets fresh state (AAA fixture resets between tests).
        This verifies that signup in one test doesn't affect another test.
        """
        # Arrange
        activity_name = "Art Club"

        # Act
        response = client.get("/activities")
        initial_participants = response.json()[activity_name]["participants"]

        # Assert - Art Club should start with empty participants (fixture resets)
        assert initial_participants == []
