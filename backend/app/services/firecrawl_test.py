import os
import json
import logging
from typing import Dict, Optional
from urllib.parse import urlparse

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class FirecrawlTestService:
    def __init__(self):
        # Enhanced debugging
        logger.info("🔄 Initializing Firecrawl Test Service...")
        
        api_key = os.getenv('FIRECRAWL_API_KEY')
        logger.info(f"🔑 API Key found: {'Yes' if api_key else 'No'}")
        
        if api_key:
            logger.info(f"📏 API Key length: {len(api_key)}")
            logger.info(f"🔒 API Key starts with: {api_key[:5]}...")
        else:
            logger.warning("❌ FIRECRAWL_API_KEY not found in environment variables")
            self.available = False
            return
        
        try:
            from firecrawl import FirecrawlApp
            logger.info("✅ firecrawl-py import successful")
            
            self.app = FirecrawlApp(api_key=api_key)
            self.available = True
            logger.info("🎉 Firecrawl Test Service initialized successfully!")
            
            # Test the available methods
            logger.info(f"🔍 Available methods: {[method for method in dir(self.app) if not method.startswith('_')]}")
            
        except ImportError as e:
            logger.error(f"❌ firecrawl-py not installed: {e}")
            logger.info("💡 Run: pip install firecrawl-py")
            self.available = False
        except Exception as e:
            logger.error(f"❌ Firecrawl init failed: {e}")
            self.available = False
    
    async def test_extract_product(self, url: str) -> Dict:
        """Test product extraction with detailed logging"""
        if not self.available:
            return self._error_response("Firecrawl not available")
        
        try:
            logger.info(f"🧪 Starting Firecrawl test for: {url}")
            
            # Define what we want to extract
            extraction_schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "number"},
                    "currency": {"type": "string", "default": "USD"},
                    "image_url": {"type": "string"},
                    "available": {"type": "boolean", "default": True},
                    "color": {"type": "string"},
                    "description": {"type": "string"},
                    "brand": {"type": "string"}
                },
                "required": ["name", "price"]
            }
            
            logger.info("🎯 Calling Firecrawl API...")
            
            # TRY DIFFERENT METHOD NAMES - Firecrawl API might have changed
            result = None
            
            # Method 1: Try the new API method
            try:
                logger.info("🔄 Trying method: scrape_url (new API)")
                result = self.app.scrape_url(url, params={
                    'formats': ['extract'],
                    'extract': {
                        'schema': extraction_schema
                    }
                })
            except AttributeError:
                # Method 2: Try alternative method name
                try:
                    logger.info("🔄 Trying method: extract (alternative)")
                    result = self.app.extract(url, extraction_schema)
                except AttributeError:
                    # Method 3: Try basic scrape first
                    try:
                        logger.info("🔄 Trying method: scrape (basic)")
                        result = self.app.scrape(url, params={'formats': ['markdown']})
                        # Then manually extract data
                        if result and 'markdown' in result:
                            extracted_data = self._extract_from_markdown(result['markdown'])
                            result = {'extract': extracted_data}
                    except Exception as e:
                        logger.error(f"❌ All methods failed: {e}")
                        return self._error_response(f"Firecrawl API methods not working: {e}")
            
            if result is None:
                return self._error_response("No valid Firecrawl method found")
            
            logger.info(f"📦 Firecrawl response received")
            logger.info(f"Response keys: {list(result.keys())}")
            
            if 'error' in result:
                error_msg = f"Firecrawl API error: {result['error']}"
                logger.error(f"❌ {error_msg}")
                return self._error_response(error_msg)
            
            # Handle different response formats
            extracted_data = {}
            if 'extract' in result:
                extracted_data = result.get('extract', {})
            elif 'data' in result:
                extracted_data = result.get('data', {})
            else:
                # Use the entire result as extracted data
                extracted_data = result
            
            logger.info(f"📊 Extracted data keys: {list(extracted_data.keys())}")
            
            # Validate required fields
            if not extracted_data.get('name'):
                logger.warning("⚠️ Could not extract product name")
                # Try to find name in other fields
                name = (extracted_data.get('title') or 
                       extracted_data.get('productName') or 
                       extracted_data.get('product_name'))
                if name:
                    extracted_data['name'] = name
                else:
                    return self._error_response("Could not extract product name")
            
            if not extracted_data.get('price'):
                logger.warning("⚠️ Could not extract product price")
                # Try to find price in other fields
                price = (extracted_data.get('currentPrice') or 
                        extracted_data.get('productPrice') or 
                        extracted_data.get('amount'))
                if price:
                    extracted_data['price'] = float(price) if isinstance(price, (int, float, str)) else None
                else:
                    return self._error_response("Could not extract product price")
            
            # Format successful response
            response = {
                "name": extracted_data.get('name'),
                "price": extracted_data.get('price'),
                "currency": extracted_data.get('currency', 'USD'),
                "image_url": extracted_data.get('image_url') or extracted_data.get('imageUrl') or extracted_data.get('image'),
                "color": extracted_data.get('color'),
                "description": extracted_data.get('description'),
                "brand": extracted_data.get('brand'),
                "available": extracted_data.get('available', True),
                "site": urlparse(url).netloc,
                "url": url,
                "success": True,
                "method": "firecrawl",
                "raw_data": extracted_data
            }
            
            logger.info(f"✅ EXTRACTION SUCCESS: {response['name']} - ${response['price']}")
            return response
            
        except Exception as e:
            error_msg = f"Firecrawl extraction failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            logger.exception(e)
            return self._error_response(error_msg)
    
    def _extract_from_markdown(self, markdown_content: str) -> Dict:
        """Fallback: Try to extract data from markdown content"""
        # Simple extraction logic from markdown
        extracted = {}
        lines = markdown_content.split('\n')
        
        for line in lines:
            if 'price' in line.lower() and '$' in line:
                # Try to extract price
                import re
                price_match = re.search(r'\$(\d+\.?\d*)', line)
                if price_match:
                    extracted['price'] = float(price_match.group(1))
            
            if 'title' in line.lower() or 'name' in line.lower():
                extracted['name'] = line.strip()
        
        return extracted
    
    def _error_response(self, error: str) -> Dict:
        return {
            "name": None,
            "price": None,
            "image_url": None,
            "site": "",
            "success": False,
            "error": error,
            "method": "firecrawl"
        }

# Global test instance
firecrawl_test = FirecrawlTestService()