import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealth:
    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "name" in response.json()
    
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAuth:
    def test_register(self):
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpassword123",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
    
    def test_register_duplicate_email(self):
        # First registration
        client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user1",
                "password": "testpassword123"
            }
        )
        # Second registration with same email
        response = client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "username": "user2",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 400
    
    def test_login(self):
        # Register first
        client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "password": "testpassword123"
            }
        )
        # Then login
        response = client.post(
            "/api/auth/login",
            data={
                "username": "loginuser",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self):
        response = client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401


class TestProjects:
    @pytest.fixture
    def auth_token(self):
        """Create a user and return auth token."""
        client.post(
            "/api/auth/register",
            json={
                "email": "project@example.com",
                "username": "projectuser",
                "password": "testpassword123"
            }
        )
        response = client.post(
            "/api/auth/login",
            data={
                "username": "projectuser",
                "password": "testpassword123"
            }
        )
        return response.json()["access_token"]
    
    def test_list_projects_empty(self, auth_token):
        response = client.get(
            "/api/projects",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.json() == []
    
    def test_create_project(self, auth_token):
        response = client.post(
            "/api/projects",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Mon Projet Test",
                "client": "Client ABC",
                "description": "Un projet de test"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Mon Projet Test"
        assert data["client"] == "Client ABC"
        assert data["status"] == "draft"
    
    def test_get_project(self, auth_token):
        # Create project first
        create_response = client.post(
            "/api/projects",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Projet à récupérer"}
        )
        project_id = create_response.json()["id"]
        
        # Get project
        response = client.get(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Projet à récupérer"
    
    def test_update_project(self, auth_token):
        # Create project
        create_response = client.post(
            "/api/projects",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Projet original"}
        )
        project_id = create_response.json()["id"]
        
        # Update project
        response = client.put(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Projet modifié"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Projet modifié"
    
    def test_delete_project(self, auth_token):
        # Create project
        create_response = client.post(
            "/api/projects",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Projet à supprimer"}
        )
        project_id = create_response.json()["id"]
        
        # Delete project
        response = client.delete(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 204
        
        # Verify deleted
        get_response = client.get(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert get_response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])