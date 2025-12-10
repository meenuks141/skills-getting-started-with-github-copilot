"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
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
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball training and games",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Tennis lessons and tournament participation",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 12,
            "participants": ["jordan@mergington.edu", "casey@mergington.edu"]
        },
        "Drama Club": {
            "description": "Theater production and performing arts",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["lucas@mergington.edu"]
        },
        "Art Studio": {
            "description": "Painting, drawing, and visual arts creation",
            "schedule": "Fridays, 4:00 PM - 5:30 PM",
            "max_participants": 18,
            "participants": ["mia@mergington.edu", "harper@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop argumentation and public speaking skills",
            "schedule": "Mondays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 16,
            "participants": ["ryan@mergington.edu"]
        },
        "Science Club": {
            "description": "Explore scientific experiments and research projects",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": ["sarah@mergington.edu", "jacob@mergington.edu"]
        }
    }
    
    # Clear and reset activities
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Reset after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 9
    
    def test_activity_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_participants_list(self, client):
        """Test that participants list contains expected data"""
        response = client.get("/activities")
        data = response.json()
        
        chess_participants = data["Chess Club"]["participants"]
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]
        
        # Verify the student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_activity_not_found(self, client):
        """Test signup for a non-existent activity"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_student(self, client):
        """Test signup when student is already registered"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_students(self, client):
        """Test that multiple different students can sign up"""
        response1 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "student1@mergington.edu"}
        )
        response2 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "student2@mergington.edu"}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        participants = activities_data["Chess Club"]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants
    
    def test_signup_updates_availability(self, client):
        """Test that signup updates the availability count"""
        # Get initial availability
        response1 = client.get("/activities")
        data1 = response1.json()
        initial_spots = data1["Chess Club"]["max_participants"] - len(data1["Chess Club"]["participants"])
        
        # Signup
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        # Get updated availability
        response2 = client.get("/activities")
        data2 = response2.json()
        updated_spots = data2["Chess Club"]["max_participants"] - len(data2["Chess Club"]["participants"])
        
        assert updated_spots == initial_spots - 1


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregister from an activity"""
        response = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]
        
        # Verify the student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
    
    def test_unregister_activity_not_found(self, client):
        """Test unregister from a non-existent activity"""
        response = client.delete(
            "/activities/NonExistent%20Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_student_not_registered(self, client):
        """Test unregister when student is not registered"""
        response = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_updates_availability(self, client):
        """Test that unregister updates the availability count"""
        # Get initial availability
        response1 = client.get("/activities")
        data1 = response1.json()
        initial_spots = data1["Chess Club"]["max_participants"] - len(data1["Chess Club"]["participants"])
        
        # Unregister
        client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        # Get updated availability
        response2 = client.get("/activities")
        data2 = response2.json()
        updated_spots = data2["Chess Club"]["max_participants"] - len(data2["Chess Club"]["participants"])
        
        assert updated_spots == initial_spots + 1
    
    def test_signup_after_unregister(self, client):
        """Test that a student can re-signup after unregistering"""
        email = "michael@mergington.edu"
        
        # Unregister
        response1 = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Try to signup again
        response2 = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify the student is registered
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Chess Club"]["participants"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
