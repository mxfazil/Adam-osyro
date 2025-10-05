"""
Tests for Business Card OCR API
Run with: pytest test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from ocr import app
import io
from PIL import Image
import os

# Test API key (should match your .env)
TEST_API_KEY = os.getenv("API_KEY", "your-secret-api-key-change-this-in-production")

client = TestClient(app)


@pytest.fixture
def auth_headers():
    """Fixture for authentication headers"""
    return {"Authorization": f"Bearer {TEST_API_KEY}"}


@pytest.fixture
def sample_business_card_image():
    """Create a sample business card image for testing"""
    # Create a simple test image
    img = Image.new('RGB', (400, 200), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes


@pytest.fixture
def sample_card_data():
    """Sample business card data"""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "+1234567890",
        "company": "Test Company"
    }


class TestHealthCheck:
    """Test health check endpoints"""
    
    def test_api_health_check(self):
        """Test API health endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "supabase_connected" in data
        assert "llama_api_configured" in data
        assert "version" in data
    
    def test_legacy_health_check(self):
        """Test legacy health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAuthentication:
    """Test API authentication"""
    
    def test_missing_auth_token(self):
        """Test request without authentication"""
        response = client.get("/api/v1/cards")
        assert response.status_code == 403  # Forbidden without auth
    
    def test_invalid_auth_token(self):
        """Test request with invalid token"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/cards", headers=headers)
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]
    
    def test_valid_auth_token(self, auth_headers):
        """Test request with valid token"""
        response = client.get("/api/v1/cards", headers=auth_headers)
        assert response.status_code == 200


class TestCardCRUD:
    """Test CRUD operations for business cards"""
    
    def test_create_card(self, auth_headers, sample_card_data):
        """Test creating a business card"""
        response = client.post(
            "/api/v1/cards",
            json=sample_card_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
    
    def test_create_card_missing_name(self, auth_headers):
        """Test creating card without required name field"""
        invalid_data = {
            "email": "test@example.com"
        }
        response = client.post(
            "/api/v1/cards",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error
    
    def test_create_card_invalid_email(self, auth_headers):
        """Test creating card with invalid email"""
        invalid_data = {
            "name": "Test User",
            "email": "not-an-email"
        }
        response = client.post(
            "/api/v1/cards",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_list_cards_default_pagination(self, auth_headers):
        """Test listing cards with default pagination"""
        response = client.get("/api/v1/cards", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["page"] == 1
        assert data["page_size"] == 10
    
    def test_list_cards_custom_pagination(self, auth_headers):
        """Test listing cards with custom pagination"""
        response = client.get(
            "/api/v1/cards?page=2&page_size=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 5
    
    def test_list_cards_with_search(self, auth_headers):
        """Test searching cards"""
        response = client.get(
            "/api/v1/cards?search=Test",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_card_not_found(self, auth_headers):
        """Test getting non-existent card"""
        response = client.get("/api/v1/cards/999999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_card_not_found(self, auth_headers, sample_card_data):
        """Test updating non-existent card"""
        response = client.put(
            "/api/v1/cards/999999",
            json=sample_card_data,
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_delete_card_not_found(self, auth_headers):
        """Test deleting non-existent card"""
        response = client.delete("/api/v1/cards/999999", headers=auth_headers)
        assert response.status_code == 404


class TestOCRExtraction:
    """Test OCR extraction functionality"""
    
    def test_extract_with_file(self, auth_headers, sample_business_card_image):
        """Test OCR extraction with file upload"""
        files = {"file": ("test_card.jpg", sample_business_card_image, "image/jpeg")}
        response = client.post(
            "/api/v1/ocr/extract",
            files=files,
            headers=auth_headers
        )
        # May succeed or fail depending on Llama API availability
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            if data["success"]:
                assert "fields" in data
    
    def test_extract_without_file(self, auth_headers):
        """Test OCR extraction without file"""
        response = client.post(
            "/api/v1/ocr/extract",
            headers=auth_headers
        )
        assert response.status_code == 422  # Missing required field
    
    def test_extract_with_invalid_file_type(self, auth_headers):
        """Test OCR extraction with non-image file"""
        files = {"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")}
        response = client.post(
            "/api/v1/ocr/extract",
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]


class TestIntegrationWorkflow:
    """Test complete workflows"""
    
    def test_full_card_lifecycle(self, auth_headers, sample_card_data):
        """Test creating, reading, updating, and deleting a card"""
        # Create
        create_response = client.post(
            "/api/v1/cards",
            json=sample_card_data,
            headers=auth_headers
        )
        assert create_response.status_code == 201
        card_id = create_response.json()["data"]["id"]
        
        # Read
        get_response = client.get(f"/api/v1/cards/{card_id}", headers=auth_headers)
        assert get_response.status_code == 200
        card_data = get_response.json()
        assert card_data["name"] == sample_card_data["name"]
        assert card_data["email"] == sample_card_data["email"]
        
        # Update
        updated_data = sample_card_data.copy()
        updated_data["company"] = "Updated Company"
        update_response = client.put(
            f"/api/v1/cards/{card_id}",
            json=updated_data,
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        # Verify update
        get_updated = client.get(f"/api/v1/cards/{card_id}", headers=auth_headers)
        assert get_updated.json()["company"] == "Updated Company"
        
        # Delete
        delete_response = client.delete(
            f"/api/v1/cards/{card_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_deleted = client.get(f"/api/v1/cards/{card_id}", headers=auth_headers)
        assert get_deleted.status_code == 404


class TestWebInterface:
    """Test web interface endpoints"""
    
    def test_home_page(self):
        """Test home page loads"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_web_extract_endpoint(self, sample_business_card_image):
        """Test web interface extract endpoint"""
        files = {"file": ("test_card.jpg", sample_business_card_image, "image/jpeg")}
        response = client.post("/extract", files=files)
        # May succeed or fail depending on Llama API
        assert response.status_code in [200, 503]
    
    def test_web_save_endpoint(self, sample_card_data):
        """Test web interface save endpoint"""
        response = client.post("/save", data=sample_card_data)
        # May succeed or fail depending on Supabase
        assert response.status_code in [200, 503]


class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_json_body(self, auth_headers):
        """Test sending invalid JSON"""
        response = client.post(
            "/api/v1/cards",
            data="not valid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self, auth_headers):
        """Test missing required fields"""
        response = client.post(
            "/api/v1/cards",
            json={},
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_invalid_page_number(self, auth_headers):
        """Test invalid pagination parameters"""
        response = client.get(
            "/api/v1/cards?page=-1",
            headers=auth_headers
        )
        assert response.status_code == 422


class TestDataValidation:
    """Test data validation"""
    
    def test_name_length_validation(self, auth_headers):
        """Test name length limits"""
        # Empty name should fail
        response = client.post(
            "/api/v1/cards",
            json={"name": ""},
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_email_format_validation(self, auth_headers):
        """Test email format validation"""
        invalid_emails = ["notanemail", "@example.com", "user@", "user@.com"]
        
        for invalid_email in invalid_emails:
            response = client.post(
                "/api/v1/cards",
                json={
                    "name": "Test User",
                    "email": invalid_email
                },
                headers=auth_headers
            )
            assert response.status_code == 422


# Performance tests (optional)
class TestPerformance:
    """Test API performance"""
    
    @pytest.mark.slow
    def test_bulk_create_performance(self, auth_headers):
        """Test creating multiple cards"""
        import time
        
        start_time = time.time()
        created_ids = []
        
        for i in range(10):
            response = client.post(
                "/api/v1/cards",
                json={
                    "name": f"Test User {i}",
                    "email": f"test{i}@example.com",
                    "company": "Test Company"
                },
                headers=auth_headers
            )
            if response.status_code == 201:
                created_ids.append(response.json()["data"]["id"])
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete in reasonable time (adjust as needed)
        assert elapsed < 10.0  # 10 seconds for 10 cards
        
        # Cleanup
        for card_id in created_ids:
            client.delete(f"/api/v1/cards/{card_id}", headers=auth_headers)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])