"""
Business Card OCR API Client
A Python client library for interacting with the Business Card OCR API
"""

import requests
from typing import Optional, Dict, List, Union
from pathlib import Path
import json


class BusinessCardAPIError(Exception):
    """Custom exception for API errors"""
    pass


class BusinessCardClient:
    """
    Client for Business Card OCR API
    
    Example:
        client = BusinessCardClient("http://localhost:8000", "your-api-key")
        
        # Extract OCR
        result = client.extract_ocr("card.jpg")
        print(result['fields'])
        
        # Create card
        card_id = client.create_card(
            name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            company="Acme Corp"
        )
        
        # List cards
        cards = client.list_cards(page=1, page_size=20)
    """
    
    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        """
        Initialize the API client
        
        Args:
            base_url: Base URL of the API (e.g., http://localhost:8000)
            api_key: Your API key for authentication
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {api_key}"
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Make HTTP request to the API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: JSON data for request body
            files: Files to upload
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            BusinessCardAPIError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            headers = self.headers.copy()
            
            # Don't set Content-Type for multipart/form-data
            if data and not files:
                headers["Content-Type"] = "application/json"
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data if data else None,
                files=files,
                params=params,
                timeout=self.timeout
            )
            
            # Raise exception for HTTP errors
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get('detail', str(e))
            except:
                error_detail = str(e)
            
            raise BusinessCardAPIError(
                f"API request failed: {error_detail}"
            )
        except requests.exceptions.RequestException as e:
            raise BusinessCardAPIError(f"Network error: {str(e)}")
        except json.JSONDecodeError:
            raise BusinessCardAPIError("Invalid JSON response from server")
    
    def health_check(self) -> Dict:
        """
        Check API health status
        
        Returns:
            Health status information
            
        Example:
            status = client.health_check()
            print(f"Status: {status['status']}")
        """
        return self._make_request("GET", "/api/health")
    
    def extract_ocr(self, image_path: Union[str, Path]) -> Dict:
        """
        Extract information from a business card image
        
        Args:
            image_path: Path to the business card image
            
        Returns:
            Dictionary with extracted fields (name, email, phone, company)
            
        Raises:
            BusinessCardAPIError: If extraction fails
            FileNotFoundError: If image file doesn't exist
            
        Example:
            result = client.extract_ocr("card.jpg")
            if result['success']:
                print(result['fields']['name'])
                print(result['fields']['email'])
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, 'image/jpeg')}
            response = self._make_request(
                "POST",
                "/api/v1/ocr/extract",
                files=files
            )
        
        return response
    
    def create_card(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None
    ) -> int:
        """
        Create a new business card entry
        
        Args:
            name: Full name (required)
            email: Email address
            phone: Phone number
            company: Company name
            
        Returns:
            ID of the created card
            
        Example:
            card_id = client.create_card(
                name="John Doe",
                email="john@example.com",
                company="Acme Corp"
            )
            print(f"Created card with ID: {card_id}")
        """
        data = {
            "name": name,
            "email": email,
            "phone": phone,
            "company": company
        }
        
        response = self._make_request(
            "POST",
            "/api/v1/cards",
            data=data
        )
        
        return response['data']['id']
    
    def list_cards(
        self,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None
    ) -> Dict:
        """
        List business cards with pagination
        
        Args:
            page: Page number (default: 1)
            page_size: Items per page (default: 10, max: 100)
            search: Search term for name, email, or company
            
        Returns:
            Dictionary with card list and pagination info
            
        Example:
            result = client.list_cards(page=1, page_size=20, search="Acme")
            print(f"Total cards: {result['total']}")
            for card in result['data']:
                print(f"{card['name']} - {card['company']}")
        """
        params = {
            "page": page,
            "page_size": page_size
        }
        
        if search:
            params["search"] = search
        
        return self._make_request(
            "GET",
            "/api/v1/cards",
            params=params
        )
    
    def get_card(self, card_id: int) -> Dict:
        """
        Get a specific business card by ID
        
        Args:
            card_id: Card ID
            
        Returns:
            Card data
            
        Example:
            card = client.get_card(123)
            print(f"Name: {card['name']}")
            print(f"Email: {card['email']}")
        """
        return self._make_request(
            "GET",
            f"/api/v1/cards/{card_id}"
        )
    
    def update_card(
        self,
        card_id: int,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None
    ) -> bool:
        """
        Update an existing business card
        
        Args:
            card_id: Card ID to update
            name: Full name
            email: Email address
            phone: Phone number
            company: Company name
            
        Returns:
            True if successful
            
        Example:
            success = client.update_card(
                card_id=123,
                name="Jane Doe",
                email="jane@newcompany.com",
                company="New Company Inc"
            )
        """
        data = {
            "name": name,
            "email": email,
            "phone": phone,
            "company": company
        }
        
        response = self._make_request(
            "PUT",
            f"/api/v1/cards/{card_id}",
            data=data
        )
        
        return response['success']
    
    def delete_card(self, card_id: int) -> bool:
        """
        Delete a business card
        
        Args:
            card_id: Card ID to delete
            
        Returns:
            True if successful
            
        Example:
            success = client.delete_card(123)
            if success:
                print("Card deleted successfully")
        """
        response = self._make_request(
            "DELETE",
            f"/api/v1/cards/{card_id}"
        )
        
        return response['success']
    
    def extract_and_save(self, image_path: Union[str, Path]) -> Dict:
        """
        Extract information from image and save in one operation
        
        Args:
            image_path: Path to the business card image
            
        Returns:
            Dictionary with card ID and extracted fields
            
        Example:
            result = client.extract_and_save("card.jpg")
            print(f"Saved with ID: {result['id']}")
            print(f"Name: {result['extracted_fields']['name']}")
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, 'image/jpeg')}
            response = self._make_request(
                "POST",
                "/api/v1/ocr/extract-and-save",
                files=files
            )
        
        return response['data']
    
    def get_all_cards(self, search: Optional[str] = None) -> List[Dict]:
        """
        Get all business cards (handles pagination automatically)
        
        Args:
            search: Optional search term
            
        Returns:
            List of all cards
            
        Example:
            all_cards = client.get_all_cards()
            print(f"Total cards: {len(all_cards)}")
            
            # Search
            acme_cards = client.get_all_cards(search="Acme")
        """
        all_cards = []
        page = 1
        page_size = 100  # Max page size
        
        while True:
            result = self.list_cards(page=page, page_size=page_size, search=search)
            all_cards.extend(result['data'])
            
            if page >= result['total_pages']:
                break
            
            page += 1
        
        return all_cards


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = BusinessCardClient(
        base_url="http://localhost:8000",
        api_key="your-api-key-here"
    )
    
    # Health check
    print("Checking API health...")
    health = client.health_check()
    print(f"Status: {health['status']}")
    print()
    
    # Extract OCR from image
    print("Extracting information from business card...")
    try:
        ocr_result = client.extract_ocr("business-card.jpg")
        if ocr_result['success']:
            fields = ocr_result['fields']
            print(f"Name: {fields.get('name')}")
            print(f"Email: {fields.get('email')}")
            print(f"Phone: {fields.get('phone')}")
            print(f"Company: {fields.get('company')}")
            print()
            
            # Create card with extracted data
            print("Creating card...")
            card_id = client.create_card(
                name=fields.get('name', 'Unknown'),
                email=fields.get('email'),
                phone=fields.get('phone'),
                company=fields.get('company')
            )
            print(f"Card created with ID: {card_id}")
            print()
    except FileNotFoundError:
        print("Business card image not found, skipping OCR example")
        print()
    except BusinessCardAPIError as e:
        print(f"Error: {e}")
        print()
    
    # Or use extract_and_save for one operation
    print("Extracting and saving in one operation...")
    try:
        result = client.extract_and_save("business-card.jpg")
        print(f"Saved with ID: {result['id']}")
        print(f"Extracted fields: {result['extracted_fields']}")
        print()
    except (FileNotFoundError, BusinessCardAPIError) as e:
        print(f"Skipping: {e}")
        print()
    
    # List all cards
    print("Listing cards...")
    cards_result = client.list_cards(page=1, page_size=10)
    print(f"Total cards: {cards_result['total']}")
    print(f"Page {cards_result['page']} of {cards_result['total_pages']}")
    for card in cards_result['data']:
        print(f"  - {card['name']} ({card['company']})")
    print()
    
    # Search cards
    print("Searching for cards...")
    search_results = client.list_cards(search="Acme", page_size=5)
    print(f"Found {len(search_results['data'])} cards matching 'Acme'")
    print()
    
    # Get all cards
    print("Getting all cards...")
    all_cards = client.get_all_cards()
    print(f"Retrieved {len(all_cards)} total cards")
    print()
    
    # Update a card (if any exist)
    if cards_result['data']:
        first_card = cards_result['data'][0]
        print(f"Updating card {first_card['id']}...")
        try:
            success = client.update_card(
                card_id=first_card['id'],
                name=first_card['name'],
                email=first_card.get('email', ''),
                phone=first_card.get('phone', ''),
                company=first_card.get('company', '') + " (Updated)"
            )
            print(f"Update successful: {success}")
            print()
        except BusinessCardAPIError as e:
            print(f"Update error: {e}")
            print()
    
    # Get specific card
    if cards_result['data']:
        card_id = cards_result['data'][0]['id']
        print(f"Getting card {card_id}...")
        card = client.get_card(card_id)
        print(f"Retrieved: {card['name']}")
        print()
    
    print("Example completed!")