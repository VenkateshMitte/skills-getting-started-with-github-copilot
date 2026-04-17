"""
Tests for the GET /activities endpoint.

This test module focuses on testing the activities retrieval functionality.
Each test follows the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and preconditions
- Act: Execute the endpoint being tested
- Assert: Verify the results
"""

import pytest


class TestGetActivities:
    """Test suite for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, fresh_activities):
        """
        Test that GET /activities returns all activities with correct structure.
        
        AAA Pattern:
        - Arrange: Fresh activities data is prepared by fixture
        - Act: Call GET /activities endpoint
        - Assert: Verify all 9 activities are returned with correct structure
        """
        # Arrange
        expected_activity_count = 9
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert len(data) == expected_activity_count
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_response_structure(self, client):
        """
        Test that each activity in response has required fields.
        
        AAA Pattern:
        - Arrange: N/A (using fixture data)
        - Act: Call GET /activities and extract one activity
        - Assert: Verify all required fields are present
        """
        # Act
        response = client.get("/activities")
        activities = response.json()
        chess_club = activities["Chess Club"]
        
        # Assert
        assert response.status_code == 200
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club

    def test_get_activities_participants_list_integrity(self, client):
        """
        Test that participant lists are preserved correctly in the response.
        
        AAA Pattern:
        - Arrange: Fresh activities with known participants
        - Act: Call endpoint and extract specific activity
        - Assert: Verify participants list matches original data
        """
        # Arrange
        expected_chess_participants = ["michael@mergington.edu", "daniel@mergington.edu"]
        
        # Act
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        
        # Assert
        assert response.status_code == 200
        assert chess_club["participants"] == expected_chess_participants
        assert len(chess_club["participants"]) == 2

    def test_get_activities_max_participants_values(self, client):
        """
        Test that max_participants values are correct for various activities.
        
        AAA Pattern:
        - Arrange: Map activity names to expected max participant counts
        - Act: Call endpoint and retrieve activities
        - Assert: Verify max_participants matches expected values
        """
        # Arrange
        expected_max_participants = {
            "Chess Club": 12,
            "Programming Class": 20,
            "Gym Class": 30,
            "Basketball Team": 15,
        }
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity_name, expected_max in expected_max_participants.items():
            assert activities[activity_name]["max_participants"] == expected_max

    def test_get_activities_description_present(self, client):
        """
        Test that all activities have meaningful descriptions.
        
        AAA Pattern:
        - Arrange: Set minimum description length expectation
        - Act: Call endpoint
        - Assert: Verify descriptions are non-empty and have content
        """
        # Arrange
        min_description_length = 10
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in activities.items():
            assert len(activity_data["description"]) > min_description_length
            assert isinstance(activity_data["description"], str)

    def test_get_activities_schedule_present(self, client):
        """
        Test that all activities have schedules defined.
        
        AAA Pattern:
        - Arrange: Set expectation for schedule field (non-empty string)
        - Act: Call endpoint
        - Assert: Verify each activity has a valid schedule
        """
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in activities.items():
            assert "schedule" in activity_data
            assert isinstance(activity_data["schedule"], str)
            assert len(activity_data["schedule"]) > 0
