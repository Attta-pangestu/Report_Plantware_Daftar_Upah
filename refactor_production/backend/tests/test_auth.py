import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the app instance from main
from main import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture
def mock_test_mode():
    """Enable test mode for testing"""
    original_test_mode = os.environ.get("TEST_MODE")
    os.environ["TEST_MODE"] = "true"
    yield
    if original_test_mode is not None:
        os.environ["TEST_MODE"] = original_test_mode
    else:
        del os.environ["TEST_MODE"]

def test_dev_mode_endpoint(client):
    """Test the dev mode info endpoint"""
    response = client.get("/dev-mode")
    assert response.status_code == 200
    data = response.json()
    assert "dev_mode" in data
    assert "test_mode" in data

def test_auth_required_endpoints_in_test_mode(client, mock_test_mode):
    """Test that auth endpoints work in test mode"""
    # With test mode enabled, should return mock user info
    response = client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert "username" in data
    assert data["username"] == "test"  # Default test user

def test_get_accessible_divisions_in_test_mode(client, mock_test_mode):
    """Test getting accessible divisions with test mode"""
    response = client.get("/auth/accessible-divisions")
    assert response.status_code == 200
    data = response.json()
    # Should return a list of divisions
    assert isinstance(data, list)
    assert len(data) > 0  # Should have some divisions

def test_auth_test_token_endpoint_in_test_mode(client, mock_test_mode):
    """Test getting test token in test mode"""
    response = client.get("/auth/test-token")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_endpoint(client):
    """Test the login endpoint responds properly"""
    # Test with test mode on
    with patch.dict(os.environ, {"TEST_MODE": "true"}):
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin"
        })

        # Should either succeed or fail with auth error (both are valid responses)
        assert response.status_code in [200, 401]