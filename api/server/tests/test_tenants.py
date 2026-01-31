"""
Tests for tenant and workspace management.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from ..app import app
from ..database import get_db, Base
from ..models.user import User
from ..models.tenant import (
    Tenant, Project, TenantMember, ProjectMember,
    TenantCreate, ProjectCreate, TenantStatus, ProjectStatus,
    TenantRole, ProjectRole
)
from ..services.tenant_service import TenantService


# Test Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_database():
    """Setup test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(setup_database):
    """Create test user."""
    db = TestingSessionLocal()
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        role="admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Get auth token
    response = client.post("/auth/login", data={
        "username": "testuser",
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    
    db.close()
    return user, token


@pytest.fixture
def tenant_service(setup_database):
    """Create tenant service instance."""
    db = TestingSessionLocal()
    service = TenantService(db)
    yield service
    db.close()


class TestTenantCreation:
    """Test tenant creation and management."""

    def test_create_tenant_success(self, test_user):
        """Test successful tenant creation."""
        user, token = test_user
        
        tenant_data = {
            "name": "Test Tenant",
            "slug": "test-tenant",
            "description": "A test tenant",
            "storage_quota_gb": 100,
            "user_limit": 50,
            "project_limit": 10
        }
        
        response = client.post(
            "/tenants/",
            json=tenant_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Tenant"
        assert data["slug"] == "test-tenant"
        assert data["status"] == TenantStatus.ACTIVE
        assert data["member_count"] == 1  # Creator is automatically added

    def test_create_tenant_duplicate_slug(self, test_user):
        """Test tenant creation with duplicate slug."""
        user, token = test_user
        
        tenant_data = {
            "name": "Test Tenant 2",
            "slug": "test-tenant",  # Same slug as previous test
            "description": "Another test tenant"
        }
        
        response = client.post(
            "/tenants/",
            json=tenant_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_create_tenant_auto_slug(self, test_user):
        """Test tenant creation with auto-generated slug."""
        user, token = test_user
        
        tenant_data = {
            "name": "Auto Slug Tenant",
            "description": "Test auto slug generation"
        }
        
        response = client.post(
            "/tenants/",
            json=tenant_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["slug"] == "auto-slug-tenant"

    def test_list_user_tenants(self, test_user):
        """Test listing user's tenants."""
        user, token = test_user
        
        # Create a tenant first
        tenant_data = {
            "name": "List Test Tenant",
            "description": "For listing test"
        }
        client.post(
            "/tenants/",
            json=tenant_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # List tenants
        response = client.get(
            "/tenants/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(t["name"] == "List Test Tenant" for t in data)

    def test_get_tenant_success(self, test_user):
        """Test getting tenant by ID."""
        user, token = test_user
        
        # Create a tenant
        tenant_data = {
            "name": "Get Test Tenant",
            "description": "For get test"
        }
        create_response = client.post(
            "/tenants/",
            json=tenant_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        tenant_id = create_response.json()["id"]
        
        # Get tenant
        response = client.get(
            f"/tenants/{tenant_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Get Test Tenant"

    def test_get_tenant_unauthorized(self, test_user):
        """Test getting tenant without access."""
        user, token = test_user
        
        response = client.get(
            "/tenants/999",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404

    def test_update_tenant_success(self, test_user):
        """Test updating tenant."""
        user, token = test_user
        
        # Create a tenant
        tenant_data = {
            "name": "Update Test Tenant",
            "description": "For update test"
        }
        create_response = client.post(
            "/tenants/",
            json=tenant_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        tenant_id = create_response.json()["id"]
        
        # Update tenant
        update_data = {
            "name": "Updated Tenant Name",
            "description": "Updated description"
        }
        response = client.put(
            f"/tenants/{tenant_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Tenant Name"
        assert data["description"] == "Updated description"

    def test_delete_tenant_success(self, test_user):
        """Test deleting tenant."""
        user, token = test_user
        
        # Create a tenant
        tenant_data = {
            "name": "Delete Test Tenant",
            "description": "For delete test"
        }
        create_response = client.post(
            "/tenants/",
            json=tenant_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        tenant_id = create_response.json()["id"]
        
        # Delete tenant
        response = client.delete(
            f"/tenants/{tenant_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 204


class TestProjectManagement:
    """Test project creation and management."""

    def test_create_project_success(self, test_user):
        """Test successful project creation."""
        user, token = test_user
        
        # Create a tenant first
        tenant_data = {
            "name": "Project Test Tenant",
            "description": "For project tests"
        }
        tenant_response = client.post(
            "/tenants/",
            json=tenant_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        tenant_id = tenant_response.json()["id"]
        
        # Create project
        project_data = {
            "name": "Test Project",
            "slug": "test-project",
            "description": "A test project",
            "storage_quota_gb": 10
        }
        
        response = client.post(
            f"/tenants/{tenant_id}/projects",
            json=project_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["slug"] == "test-project"
        assert data["tenant_id"] == tenant_id
        assert data["status"] == ProjectStatus.ACTIVE

    def test_list_tenant_projects(self, test_user):
        """Test listing projects in tenant."""
        user, token = test_user
        
        # Create a tenant
        tenant_data = {
            "name": "Project List Tenant",
            "description": "For project list test"
        }
        tenant_response = client.post(
            "/tenants/",
            json=tenant_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        tenant_id = tenant_response.json()["id"]
        
        # Create projects
        for i in range(3):
            project_data = {
                "name": f"Project {i}",
                "description": f"Test project {i}"
            }
            client.post(
                f"/tenants/{tenant_id}/projects",
                json=project_data,
                headers={"Authorization": f"Bearer {token}"}
            )
        
        # List projects
        response = client.get(
            f"/tenants/{tenant_id}/projects",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_update_project_success(self, test_user):
        """Test updating project."""
        user, token = test_user
        
        # Create tenant and project
        tenant_response = client.post(
            "/tenants/",
            json={"name": "Update Project Tenant"},
            headers={"Authorization": f"Bearer {token}"}
        )
        tenant_id = tenant_response.json()["id"]
        
        project_response = client.post(
            f"/tenants/{tenant_id}/projects",
            json={"name": "Test Project"},
            headers={"Authorization": f"Bearer {token}"}
        )
        project_id = project_response.json()["id"]
        
        # Update project
        update_data = {
            "name": "Updated Project Name",
            "description": "Updated description"
        }
        response = client.put(
            f"/tenants/projects/{project_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Project Name"

    def test_delete_project_success(self, test_user):
        """Test deleting project."""
        user, token = test_user
        
        # Create tenant and project
        tenant_response = client.post(
            "/tenants/",
            json={"name": "Delete Project Tenant"},
            headers={"Authorization": f"Bearer {token}"}
        )
        tenant_id = tenant_response.json()["id"]
        
        project_response = client.post(
            f"/tenants/{tenant_id}/projects",
            json={"name": "Delete Test Project"},
            headers={"Authorization": f"Bearer {token}"}
        )
        project_id = project_response.json()["id"]
        
        # Delete project
        response = client.delete(
            f"/tenants/projects/{project_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 204


class TestMemberManagement:
    """Test tenant and project member management."""

    def test_add_tenant_member(self, test_user):
        """Test adding member to tenant."""
        user, token = test_user
        
        # Create another user
        db = TestingSessionLocal()
        other_user = User(
            username="otheruser",
            email="other@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)
        db.close()
        
        # Create tenant
        tenant_response = client.post(
            "/tenants/",
            json={"name": "Member Test Tenant"},
            headers={"Authorization": f"Bearer {token}"}
        )
        tenant_id = tenant_response.json()["id"]
        
        # Add member
        member_data = {
            "user_id": other_user.id,
            "role": TenantRole.MEMBER
        }
        response = client.post(
            f"/tenants/{tenant_id}/members",
            json=member_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201

    def test_update_tenant_member_role(self, test_user):
        """Test updating tenant member role."""
        user, token = test_user
        
        # Create another user and tenant
        db = TestingSessionLocal()
        other_user = User(
            username="memberuser",
            email="member@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)
        db.close()
        
        tenant_response = client.post(
            "/tenants/",
            json={"name": "Role Test Tenant"},
            headers={"Authorization": f"Bearer {token}"}
        )
        tenant_id = tenant_response.json()["id"]
        
        # Add member
        client.post(
            f"/tenants/{tenant_id}/members",
            json={"user_id": other_user.id, "role": TenantRole.MEMBER},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Update role
        update_data = {"role": TenantRole.ADMIN}
        response = client.put(
            f"/tenants/{tenant_id}/members/{other_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200

    def test_add_project_member(self, test_user):
        """Test adding member to project."""
        user, token = test_user
        
        # Create another user
        db = TestingSessionLocal()
        other_user = User(
            username="projectuser",
            email="project@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)
        db.close()
        
        # Create tenant and project
        tenant_response = client.post(
            "/tenants/",
            json={"name": "Project Member Tenant"},
            headers={"Authorization": f"Bearer {token}"}
        )
        tenant_id = tenant_response.json()["id"]
        
        project_response = client.post(
            f"/tenants/{tenant_id}/projects",
            json={"name": "Member Test Project"},
            headers={"Authorization": f"Bearer {token}"}
        )
        project_id = project_response.json()["id"]
        
        # Add member
        member_data = {
            "user_id": other_user.id,
            "role": ProjectRole.MEMBER
        }
        response = client.post(
            f"/tenants/projects/{project_id}/members",
            json=member_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201


class TestUserContext:
    """Test user context and permissions."""

    def test_get_user_context(self, test_user):
        """Test getting complete user context."""
        user, token = test_user
        
        # Create tenant and project
        tenant_response = client.post(
            "/tenants/",
            json={"name": "Context Test Tenant"},
            headers={"Authorization": f"Bearer {token}"}
        )
        tenant_id = tenant_response.json()["id"]
        
        project_response = client.post(
            f"/tenants/{tenant_id}/projects",
            json={"name": "Context Test Project"},
            headers={"Authorization": f"Bearer {token}"}
        )
        project_id = project_response.json()["id"]
        
        # Get user context
        response = client.get(
            "/tenants/context/user",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user.id
        assert len(data["tenants"]) >= 1
        assert len(data["projects"]) >= 1
        
        # Check tenant access
        tenant_access = next(t for t in data["tenants"] if t["tenant_id"] == tenant_id)
        assert tenant_access["role"] == TenantRole.OWNER
        assert "tenant:read" in tenant_access["permissions"]
        
        # Check project access
        project_access = next(p for p in data["projects"] if p["project_id"] == project_id)
        assert project_access["role"] == ProjectRole.OWNER
        assert "project:read" in project_access["permissions"]


class TestTenantIsolation:
    """Test tenant data isolation."""

    def test_tenant_isolation(self, test_user):
        """Test that users can only access their own tenants."""
        user, token = test_user
        
        # Create tenant for user 1
        tenant1_response = client.post(
            "/tenants/",
            json={"name": "User1 Tenant"},
            headers={"Authorization": f"Bearer {token}"}
        )
        tenant1_id = tenant1_response.json()["id"]
        
        # Create second user and their tenant
        db = TestingSessionLocal()
        user2 = User(
            username="user2",
            email="user2@example.com",
            hashed_password="hashed_password",
            is_active=True
        )
        db.add(user2)
        db.commit()
        db.refresh(user2)
        db.close()
        
        # Get token for user2
        user2_response = client.post("/auth/login", data={
            "username": "user2",
            "password": "testpassword"
        })
        user2_token = user2_response.json()["access_token"]
        
        tenant2_response = client.post(
            "/tenants/",
            json={"name": "User2 Tenant"},
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        tenant2_id = tenant2_response.json()["id"]
        
        # User1 should not be able to access User2's tenant
        response = client.get(
            f"/tenants/{tenant2_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404
        
        # User2 should not be able to access User1's tenant
        response = client.get(
            f"/tenants/{tenant1_id}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__])
