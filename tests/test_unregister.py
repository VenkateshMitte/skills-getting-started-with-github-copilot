"""
Tests for the DELETE /activities/{activity_name}/participants endpoint.

This test module focuses on testing the unregister/delete functionality.
Each test follows the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and preconditions (e.g., enroll student first)
- Act: Execute the endpoint being tested
- Assert: Verify the results and side effects
"""

import pytest


class TestUnregisterFromActivity:
    """Test suite for DELETE /activities/{activity_name}/participants endpoint."""

    def test_unregister_success_happy_path(self, client, test_emails):
        """
        Test successful unregister when student is enrolled.
        
        AAA Pattern:
        - Arrange: Use a student already enrolled in an activity
        - Act: Call DELETE endpoint to unregister
        - Assert: Verify 200 response and success message
        """
        # Arrange
        activity_name = "Chess Club"
        email = test_emails["enrolled_chess"]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"

    def test_unregister_removes_participant_from_list(self, client, test_emails):
        """
        Test that unregister actually removes the student from the activity's participant list.
        
        AAA Pattern:
        - Arrange: Verify student is in activity initially
        - Act: Call DELETE to unregister
        - Assert: Verify student is no longer in participant list
        """
        # Arrange
        activity_name = "Chess Club"
        email = test_emails["enrolled_chess"]
        
        # Verify student is enrolled initially
        initial_response = client.get("/activities")
        assert email in initial_response.json()[activity_name]["participants"]
        
        # Act
        delete_response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert
        assert delete_response.status_code == 200
        
        # Verify student was removed
        updated_response = client.get("/activities")
        assert email not in updated_response.json()[activity_name]["participants"]

    def test_unregister_activity_not_found_404(self, client):
        """
        Test that unregister fails with 404 when activity doesn't exist.
        
        AAA Pattern:
        - Arrange: Use a non-existent activity name
        - Act: Attempt to unregister from non-existent activity
        - Assert: Verify 404 response and appropriate error message
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_student_not_enrolled_404(self, client):
        """
        Test that unregister fails with 404 when student isn't enrolled.
        
        AAA Pattern:
        - Arrange: Use a student not enrolled in the activity
        - Act: Attempt to unregister them
        - Assert: Verify 404 response and appropriate error message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "not_enrolled@mergington.edu"  # This student is not in Chess Club
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Student is not signed up for this activity"

    def test_unregister_only_participant(self, client):
        """
        Test that the last participant can be unregistered, leaving activity empty.
        
        AAA Pattern:
        - Arrange: Create activity with only one participant, attempt to unregister them
        - Act: Call DELETE endpoint
        - Assert: Verify unregister succeeds and activity has no participants
        """
        # Arrange
        activity_name = "Art Studio"
        # Art Studio has only 1 participant: "isabella@mergington.edu"
        email = "isabella@mergington.edu"
        
        # Verify there's only one participant
        activities_response = client.get("/activities")
        assert len(activities_response.json()[activity_name]["participants"]) == 1
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verify activity now has no participants
        updated_response = client.get("/activities")
        assert len(updated_response.json()[activity_name]["participants"]) == 0

    def test_unregister_preserves_other_participants(self, client):
        """
        Test that unregistering one student doesn't affect other participants.
        
        AAA Pattern:
        - Arrange: Note all participants in activity with multiple students
        - Act: Unregister one specific student
        - Assert: Verify other participants are still enrolled
        """
        # Arrange
        activity_name = "Tennis Club"
        # Tennis Club has: ["james@mergington.edu", "sarah@mergington.edu"]
        student_to_remove = "james@mergington.edu"
        student_to_keep = "sarah@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": student_to_remove}
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verify removed student is gone
        updated_response = client.get("/activities")
        participants = updated_response.json()[activity_name]["participants"]
        assert student_to_remove not in participants
        
        # Verify kept student is still there
        assert student_to_keep in participants

    def test_unregister_multiple_students_sequentially(self, client):
        """
        Test that multiple students can be unregistered in sequence.
        
        AAA Pattern:
        - Arrange: Enroll multiple students first
        - Act: Unregister each one sequentially
        - Assert: Verify each unregister succeeds and list shrinks
        """
        # Arrange
        activity_name = "Programming Class"
        # Program Class has: ["emma@mergington.edu", "sophia@mergington.edu"]
        students = ["emma@mergington.edu", "sophia@mergington.edu"]
        
        # Act & Assert
        for i, email in enumerate(students):
            response = client.delete(
                f"/activities/{activity_name}/participants",
                params={"email": email}
            )
            
            assert response.status_code == 200
            
            # Verify participant count decreases
            activities_response = client.get("/activities")
            participant_count = len(activities_response.json()[activity_name]["participants"])
            assert participant_count == len(students) - i - 1

    def test_unregister_then_cannot_unregister_again_404(self, client, test_emails):
        """
        Test that once unregistered, a student cannot be unregistered again.
        
        AAA Pattern:
        - Arrange: Student is enrolled initially
        - Act: Unregister student, then attempt to unregister again
        - Assert: First unregister succeeds, second one fails with 404
        """
        # Arrange
        activity_name = "Chess Club"
        email = test_emails["enrolled_chess"]
        
        # Act - First unregister
        first_response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Act - Second unregister attempt
        second_response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert
        assert first_response.status_code == 200
        assert second_response.status_code == 404
        assert second_response.json()["detail"] == "Student is not signed up for this activity"

    def test_unregister_then_can_signup_again(self, client):
        """
        Test that after unregistering, a student can sign up again.
        
        AAA Pattern:
        - Arrange: Student is enrolled
        - Act: Unregister student, then attempt to sign up again
        - Assert: Both operations succeed and student is re-enrolled
        """
        # Arrange
        activity_name = "Debate Team"
        email = "noah@mergington.edu"  # Currently in Debate Team
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Act - Signup again
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert unregister_response.status_code == 200
        assert signup_response.status_code == 200
        
        # Verify student is back in activity
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]

    def test_unregister_from_different_activities_independent(self, client):
        """
        Test that unregistering from one activity doesn't affect other activities.
        
        AAA Pattern:
        - Arrange: Enroll same student in two activities
        - Act: Unregister from one activity
        - Assert: Verify student is removed from one but not the other
        """
        # Arrange
        student_email = "multi_activity@mergington.edu"
        activity1 = "Science Club"
        activity2 = "Music Band"
        
        # Signup for both activities
        client.post(
            f"/activities/{activity1}/signup",
            params={"email": student_email}
        )
        client.post(
            f"/activities/{activity2}/signup",
            params={"email": student_email}
        )
        
        # Act - Unregister from activity1 only
        response = client.delete(
            f"/activities/{activity1}/participants",
            params={"email": student_email}
        )
        
        # Assert
        assert response.status_code == 200
        
        activities_response = client.get("/activities")
        activities = activities_response.json()
        
        # Verify removed from activity1
        assert student_email not in activities[activity1]["participants"]
        
        # Verify still in activity2
        assert student_email in activities[activity2]["participants"]

    def test_unregister_count_matches_after_operations(self, client):
        """
        Test that participant counts remain accurate after signup and unregister.
        
        AAA Pattern:
        - Arrange: Note initial participant count
        - Act: Signup new student, then unregister them
        - Assert: Verify count matches initial state
        """
        # Arrange
        activity_name = "Gym Class"
        email = "gym_student@mergington.edu"
        
        # Get initial count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act - Signup
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Verify count increased
        after_signup = client.get("/activities")
        signup_count = len(after_signup.json()[activity_name]["participants"])
        assert signup_count == initial_count + 1
        
        # Act - Unregister
        client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        
        # Assert - Count should return to initial
        after_unregister = client.get("/activities")
        final_count = len(after_unregister.json()[activity_name]["participants"])
        assert final_count == initial_count
