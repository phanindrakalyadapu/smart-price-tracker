import os
import json
import asyncio
import logging
import time
from typing import Dict, Optional, Any
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIScraper:
    def __init__(self):
        # Simple cache using dictionary
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour in seconds
        
        # Initialize OpenAI client
        try:
            from openai import AsyncOpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY not found in environment variables")
                self.openai_available = False
            else:
                self.client = AsyncOpenAI(api_key=api_key)
                self.openai_available = True
                logger.info("✅ AI Scraper initialized with OpenAI")
        except ImportError:
            logger.warning("OpenAI package not installed. AI scraping disabled.")
            self.openai_available = False
        
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo-1106")
    
    def _get_cache_key(self, url: str, content_hash: str) -> str:
        return f"{url}:{content_hash}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self.cache:
            return False
        
        cache_entry = self.cache[cache_key]
        cache_time = cache_entry.get('timestamp', 0)
        return (time.time() - cache_time) < self.cache_ttl
    
    def _clean_html(self, soup: BeautifulSoup) -> str:
        """Remove unnecessary elements to reduce token count"""
        # Remove scripts, styles, nav, footer, etc.
        for element in soup(["script", "style", "nav", "footer", "header", 
                           "meta", "link", "button", "form"]):
            element.decompose()
        
        # Remove elements with common non-content classes
        non_content_classes = ['nav', 'menu', 'footer', 'header', 'sidebar', 
                              'advertisement', 'popup', 'modal', 'cookie']
        for class_name in non_content_classes:
            for element in soup.find_all(class_=lambda x: x and class_name in x.lower()):
                element.decompose()
        
        # Get clean text
        text = soup.get_text()
        
        # Clean up whitespace and limit length
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)[:6000]  # Limit to ~6000 chars for safety
        
        return clean_text
    
    async def _call_gpt_with_retry(self, prompt: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """Call GPT with simple retry logic"""
        if not self.openai_available:
            logger.warning("OpenAI not available, skipping API call")
            return None
            
        for attempt in range(max_retries):
            try:
                from openai import AsyncOpenAI
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": """You are an expert web scraper that extracts product information from e-commerce websites. 
                            Always return valid JSON. If information is not found, use null."""
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=500,
                    response_format={ "type": "json_object" }
                )
                
                result_text = response.choices[0].message.content
                logger.info(f"✅ AI extraction successful (attempt {attempt + 1})")
                return json.loads(result_text)
                
            except Exception as e:
                logger.warning(f"GPT API call attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All GPT API attempts failed: {e}")
        
        return None
    
    async def extract_product_info(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """Extract product information using AI"""
        
        if not self.openai_available:
            logger.warning("OpenAI not available, skipping AI extraction")
            return None
        
        # Create cache key
        content_hash = str(hash(html[:2000]))  # Hash first 2000 chars for uniqueness
        cache_key = self._get_cache_key(url, content_hash)
        
        # Check cache
        if self._is_cache_valid(cache_key):
            logger.info("✅ Using cached AI result")
            return self.cache[cache_key]['data']
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            clean_content = self._clean_html(soup)
            
            prompt = f"""
            Extract product information from this e-commerce webpage. Return ONLY JSON with this exact structure:
            {{
                "name": "product name or null",
                "price": 99.99,
                "currency": "USD",
                "available": true,
                "confidence": 0.95
            }}

            IMPORTANT RULES:
            1. Price must be a number without currency symbols (e.g., 99.99 not $99.99)
            2. Return null for any field that cannot be determined
            3. Confidence should be 0-1 based on how sure you are
            4. Available should be true/false based on out-of-stock indicators
            5. Currency should be 3-letter code like USD, EUR, GBP

            Webpage URL: {url}
            Webpage content:
            {clean_content}
            """
            
            result = await self._call_gpt_with_retry(prompt)
            
            if result:
                # Validate and clean the result
                validated_result = self._validate_result(result)
                
                # Store in cache
                self.cache[cache_key] = {
                    'data': validated_result,
                    'timestamp': time.time()
                }
                
                logger.info(f"✅ AI extracted: {validated_result.get('name')} - ${validated_result.get('price')}")
                return validated_result
                
        except Exception as e:
            logger.error(f"AI extraction failed for {url}: {e}")
        
        return None
    
    def _validate_result(self, result: Dict) -> Dict:
        """Validate and clean AI result"""
        validated = {
            "name": result.get("name"),
            "price": result.get("price"),
            "currency": result.get("currency", "USD"),
            "available": result.get("available", True),
            "confidence": min(max(result.get("confidence", 0), 0), 1),
            "method": "ai"
        }
        
        # Clean price
        if validated["price"] and not isinstance(validated["price"], (int, float)):
            try:
                # Remove any non-numeric characters except decimal point
                price_str = str(validated["price"]).replace('$', '').replace(',', '').strip()
                validated["price"] = float(price_str)
            except (ValueError, TypeError):
                validated["price"] = None
                validated["confidence"] = 0  # Lower confidence if price parsing failed
        
        return validated