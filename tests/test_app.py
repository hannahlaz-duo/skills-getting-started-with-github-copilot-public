"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store original state
    original_activities = {
        name: {
            **details,
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state
    for name, details in original_activities.items():
        if name in activities:
            activities[name]["participants"] = details["participants"].copy()


def test_root_redirects_to_static(client):
    """Test that root path redirects to static index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    
    # Verify it's a dictionary with activities
    assert isinstance(data, dict)
    assert len(data) > 0
    
    # Verify structure of an activity
    assert "Programming Class" in data
    programming = data["Programming Class"]
    assert "description" in programming
    assert "schedule" in programming
    assert "max_participants" in programming
    assert "participants" in programming


def test_signup_for_activity_success(client):
    """Test successfully signing up for an activity"""
    response = client.post(
        "/activities/Programming Class/signup?email=test@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "test@mergington.edu" in data["message"]
    assert "Programming Class" in data["message"]
    
    # Verify student was added
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "test@mergington.edu" in activities_data["Programming Class"]["participants"]


def test_signup_for_nonexistent_activity(client):
    """Test signing up for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_signup_duplicate_registration(client):
    """Test that a student cannot register twice for the same activity"""
    email = "duplicate@mergington.edu"
    activity = "Chess Club"
    
    # First signup should succeed
    response1 = client.post(f"/activities/{activity}/signup?email={email}")
    assert response1.status_code == 200
    
    # Second signup should fail
    response2 = client.post(f"/activities/{activity}/signup?email={email}")
    assert response2.status_code == 400
    data = response2.json()
    assert "detail" in data
    assert "already signed up" in data["detail"].lower()


def test_unregister_from_activity_success(client):
    """Test successfully unregistering from an activity"""
    email = "emma@mergington.edu"
    activity = "Programming Class"
    
    # Verify student is initially registered
    activities_response = client.get("/activities")
    assert email in activities_response.json()[activity]["participants"]
    
    # Unregister
    response = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    
    # Verify student was removed
    activities_response = client.get("/activities")
    assert email not in activities_response.json()[activity]["participants"]


def test_unregister_from_nonexistent_activity(client):
    """Test unregistering from an activity that doesn't exist"""
    response = client.delete(
        "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_unregister_not_registered_student(client):
    """Test unregistering a student who is not registered"""
    email = "notregistered@mergington.edu"
    activity = "Chess Club"
    
    response = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "not signed up" in data["detail"].lower()


def test_activity_capacity_tracking(client):
    """Test that participant count is tracked correctly"""
    activity = "Math Club"
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity]["participants"])
    
    # Add a student
    client.post(f"/activities/{activity}/signup?email=newstudent@mergington.edu")
    
    # Check count increased
    response = client.get("/activities")
    new_count = len(response.json()[activity]["participants"])
    assert new_count == initial_count + 1


def test_multiple_activities_signup(client):
    """Test that a student can sign up for multiple different activities"""
    email = "multitasker@mergington.edu"
    
    # Sign up for multiple activities
    response1 = client.post(f"/activities/Chess Club/signup?email={email}")
    response2 = client.post(f"/activities/Drama Club/signup?email={email}")
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Verify student is in both
    activities_response = client.get("/activities")
    data = activities_response.json()
    assert email in data["Chess Club"]["participants"]
    assert email in data["Drama Club"]["participants"]
