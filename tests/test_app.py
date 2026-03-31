"""
Tests for Mergington High School Activities API
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app, activities

client = TestClient(app)


def reset_activities():
    """Reset activities to initial state for each test"""
    global activities
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Test Activity": {
            "description": "Test activity for signup tests",
            "schedule": "Monday 2:00 PM",
            "max_participants": 2,
            "participants": []
        }
    })


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self):
        """Test that all activities are returned"""
        reset_activities()
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Test Activity" in data
    
    def test_get_activities_contains_correct_structure(self):
        """Test that activities have correct data structure"""
        reset_activities()
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
    
    def test_get_activities_shows_participant_count(self):
        """Test that participant count is accurate"""
        reset_activities()
        response = client.get("/activities")
        data = response.json()
        assert len(data["Chess Club"]["participants"]) == 2
        assert data["Chess Club"]["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successfully_adds_participant(self):
        """Test that a student can successfully sign up for an activity"""
        reset_activities()
        response = client.post(
            "/activities/Test%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert "test@mergington.edu" in activities["Test Activity"]["participants"]
    
    def test_signup_fails_with_nonexistent_activity(self):
        """Test that signup fails for non-existent activity"""
        reset_activities()
        response = client.post(
            "/activities/Nonexistent/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_fails_with_duplicate_email(self):
        """Test that a student cannot sign up twice for the same activity"""
        reset_activities()
        # First signup should succeed
        response1 = client.post(
            "/activities/Test%20Activity/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            "/activities/Test%20Activity/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_multiple_students_same_activity(self):
        """Test that multiple students can sign up for the same activity"""
        reset_activities()
        response1 = client.post(
            "/activities/Test%20Activity/signup?email=student1@mergington.edu"
        )
        response2 = client.post(
            "/activities/Test%20Activity/signup?email=student2@mergington.edu"
        )
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert len(activities["Test Activity"]["participants"]) == 2


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successfully_removes_participant(self):
        """Test that a student can unregister from an activity"""
        reset_activities()
        # First add a participant
        client.post("/activities/Test%20Activity/signup?email=test@mergington.edu")
        assert "test@mergington.edu" in activities["Test Activity"]["participants"]
        
        # Then unregister
        response = client.delete(
            "/activities/Test%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert "test@mergington.edu" not in activities["Test Activity"]["participants"]
    
    def test_unregister_fails_with_nonexistent_activity(self):
        """Test that unregister fails for non-existent activity"""
        reset_activities()
        response = client.delete(
            "/activities/Nonexistent/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_fails_if_not_registered(self):
        """Test that unregister fails if student is not registered"""
        reset_activities()
        response = client.delete(
            "/activities/Test%20Activity/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_removes_from_existing_participant(self):
        """Test that unregister works with existing participants"""
        reset_activities()
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in activities["Chess Club"]["participants"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static(self):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestIntegration:
    """Integration tests for multiple operations"""
    
    def test_full_signup_and_unregister_flow(self):
        """Test complete flow of signup and unregister"""
        reset_activities()
        initial_count = len(activities["Test Activity"]["participants"])
        
        # Signup
        signup_response = client.post(
            "/activities/Test%20Activity/signup?email=flow@mergington.edu"
        )
        assert signup_response.status_code == 200
        assert len(activities["Test Activity"]["participants"]) == initial_count + 1
        
        # Verify it appears in activities list
        activities_response = client.get("/activities")
        assert "flow@mergington.edu" in activities_response.json()["Test Activity"]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            "/activities/Test%20Activity/unregister?email=flow@mergington.edu"
        )
        assert unregister_response.status_code == 200
        assert len(activities["Test Activity"]["participants"]) == initial_count
    
    def test_participant_availability_decreases_on_signup(self):
        """Test that available spots decrease when student signs up"""
        reset_activities()
        # Get initial state
        response1 = client.get("/activities")
        max_participants = response1.json()["Test Activity"]["max_participants"]
        initial_participants = len(response1.json()["Test Activity"]["participants"])
        
        # Signup
        client.post("/activities/Test%20Activity/signup?email=test1@mergington.edu")
        
        # Get updated state
        response2 = client.get("/activities")
        updated_participants = len(response2.json()["Test Activity"]["participants"])
        
        assert updated_participants == initial_participants + 1
        assert (max_participants - updated_participants) == (max_participants - initial_participants - 1)
