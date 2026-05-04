"""
Tests for the POST /activities/{activity_name}/signup endpoint.

This test module focuses on testing the signup functionality.
Each test follows the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and preconditions
- Act: Execute the endpoint being tested
- Assert: Verify the results and side effects
"""

import pytest


class TestSignupForActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_success_happy_path(self, client, test_emails):
        """
        Test successful signup when all conditions are met.
        
        AAA Pattern:
        - Arrange: Prepare activity name and email of a student not yet enrolled
        - Act: Call POST /signup endpoint
        - Assert: Verify 200 response and success message
        """
        # Arrange
        activity_name = "Chess Club"
        email = test_emails["not_enrolled_chess"]
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"

    def test_signup_adds_participant_to_list(self, client, test_emails):
        """
        Test that signup actually adds the student to the activity's participant list.
        
        AAA Pattern:
        - Arrange: Get initial participant count
        - Act: Sign up new student, then retrieve activities to verify
        - Assert: Verify participant was added to the list
        """
        # Arrange
        activity_name = "Programming Class"
        email = test_emails["not_enrolled_programming"]
        
        # Act
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        activities_response = client.get("/activities")
        updated_activities = activities_response.json()
        
        # Assert
        assert signup_response.status_code == 200
        assert email in updated_activities[activity_name]["participants"]

    def test_signup_activity_not_found_404(self, client, test_emails):
        """
        Test that signup fails with 404 when activity doesn't exist.
        
        AAA Pattern:
        - Arrange: Use a non-existent activity name
        - Act: Attempt signup
        - Assert: Verify 404 response and appropriate error message
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "new_student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_already_enrolled_400(self, client, test_emails):
        """
        Test that signup fails with 400 when student is already enrolled.
        
        AAA Pattern:
        - Arrange: Use a student already enrolled in the activity
        - Act: Attempt to sign up the same student again
        - Assert: Verify 400 response and appropriate error message
        """
        # Arrange
        activity_name = "Chess Club"
        email = test_emails["enrolled_chess"]  # Already in Chess Club
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_activity_full_400(self, client):
        """
        Test that signup fails with 400 when activity is at capacity.
        
        AAA Pattern:
        - Arrange: Create activity with max 2 participants, add 2 students
        - Act: Attempt to sign up a third student
        - Assert: Verify 400 response and "Activity is full" error
        """
        # Arrange
        activity_name = "Basketball Team"
        # Basketball Team has max_participants=15, currently has 1
        # We'll manually fill it up to test the full condition
        email_to_add = "test_student@mergington.edu"
        
        # First, let's get current participant count
        activities_response = client.get("/activities")
        current_participants = len(activities_response.json()[activity_name]["participants"])
        max_participants = activities_response.json()[activity_name]["max_participants"]
        
        # Sign up students until activity is full
        for i in range(max_participants - current_participants):
            test_email = f"filler_{i}@mergington.edu"
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": test_email}
            )
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email_to_add}
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Activity is full"

    def test_signup_multiple_students_same_activity(self, client):
        """
        Test that multiple different students can successfully sign up for same activity.
        
        AAA Pattern:
        - Arrange: Prepare list of new students to sign up
        - Act: Sign up multiple students sequentially
        - Assert: Verify all signups succeed and participants list grows
        """
        # Arrange
        activity_name = "Art Studio"
        new_students = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu",
        ]
        
        # Act
        responses = []
        for email in new_students:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            responses.append(response)
        
        # Assert
        for response in responses:
            assert response.status_code == 200
        
        # Verify all students are in the activity
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        for email in new_students:
            assert email in participants

    def test_signup_preserves_existing_participants(self, client):
        """
        Test that signup doesn't remove or modify existing participants.
        
        AAA Pattern:
        - Arrange: Note existing participants in an activity
        - Act: Sign up a new student
        - Assert: Verify existing participants are still there
        """
        # Arrange
        activity_name = "Music Band"
        new_email = "new_musician@mergington.edu"
        
        # Get original participants before signup
        original_response = client.get("/activities")
        original_participants = original_response.json()[activity_name]["participants"].copy()
        
        # Act
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Get participants after signup
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity_name]["participants"]
        
        # Assert
        assert signup_response.status_code == 200
        
        # All original participants should still be there
        for original_email in original_participants:
            assert original_email in updated_participants
        
        # New participant should be added (not replace)
        assert len(updated_participants) == len(original_participants) + 1
        assert new_email in updated_participants

    def test_signup_last_available_spot(self, client):
        """
        Test that signup succeeds when claiming the last available spot.
        
        AAA Pattern:
        - Arrange: Create activity near capacity, fill all but one spot
        - Act: Sign up for the last available spot
        - Assert: Verify signup succeeds with 200 status
        """
        # Arrange
        activity_name = "Debate Team"
        # Debate Team has max 14, currently has 1
        
        activities_response = client.get("/activities")
        max_participants = activities_response.json()[activity_name]["max_participants"]
        current_count = len(activities_response.json()[activity_name]["participants"])
        
        # Fill up to one before max
        for i in range(max_participants - current_count - 1):
            test_email = f"debater_{i}@mergington.edu"
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": test_email}
            )
        
        # Act - Sign up for last spot
        last_email = "final_debater@mergington.edu"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": last_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {last_email} for {activity_name}"

    def test_signup_different_activities_independent(self, client):
        """
        Test that signups for different activities don't interfere with each other.
        
        AAA Pattern:
        - Arrange: Prepare two activities and one student
        - Act: Sign student up for both activities
        - Assert: Verify both signups succeed independently
        """
        # Arrange
        student_email = "versatile_student@mergington.edu"
        activity1 = "Science Club"
        activity2 = "Tennis Club"
        
        # Act
        response1 = client.post(
            f"/activities/{activity1}/signup",
            params={"email": student_email}
        )
        response2 = client.post(
            f"/activities/{activity2}/signup",
            params={"email": student_email}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify student is in both activities
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert student_email in activities[activity1]["participants"]
        assert student_email in activities[activity2]["participants"]
