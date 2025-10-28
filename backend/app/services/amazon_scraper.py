import os
import re
import json
import logging
import random
import time
from typing import Dict
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class AmazonScraper:
    def __init__(self):
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with realistic headers and cookies"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
        })
        
        # Add some common cookies that make us look like a real browser
        self.session.cookies.update({
            'session-id': ''.join(random.choices('123456789', k=10)),
            'session-id-time': '2082787201l',
            'i18n-prefs': 'USD',
            'ubid-main': ''.join(random.choices('1234567890', k=10)),
        })
    
    def _get_rotating_headers(self):
        """Return rotating headers to avoid detection"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        headers = self.session.headers.copy()
        headers['User-Agent'] = random.choice(user_agents)
        return headers
    
    def _is_captcha_page(self, html: str) -> bool:
        """Check if Amazon is showing a CAPTCHA page"""
        captcha_indicators = [
            'captcha',
            'robot',
            'enter the characters you see',
            'try again',
            'sorry we just need to make sure'
        ]
        html_lower = html.lower()
        return any(indicator in html_lower for indicator in captcha_indicators)
    
    def _extract_from_json_ld(self, soup: BeautifulSoup) -> Dict:
        """Extract product data from JSON-LD structured data"""
        try:
            script_tags = soup.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') in ['Product', 'ItemPage']:
                        name = data.get('name')
                        offers = data.get('offers', {})
                        price = offers.get('price')
                        image = data.get('image')
                        
                        if name and price:
                            return {
                                'name': name,
                                'price': float(price),
                                'image_url': image
                            }
                except:
                    continue
        except:
            pass
        return {}
    
    def _extract_price_advanced(self, soup: BeautifulSoup, html: str) -> float:
        """Advanced price extraction with multiple strategies"""
        # Strategy 1: JSON-LD structured data
        json_ld_data = self._extract_from_json_ld(soup)
        if json_ld_data.get('price'):
            return json_ld_data['price']
        
        # Strategy 2: Data attributes in HTML
        price_patterns = [
            r'"priceAmount":\s*(\d+\.?\d*)',
            r'data-a-price="(\d+\.?\d*)"',
            r'\"currentPrice\":\s*\{[^}]*\"amount\":\s*(\d+\.?\d*)',
            r'\"buyingPrice\":\s*(\d+\.?\d*)',
            r'\"salePrice\":\s*(\d+\.?\d*)',
            r'\"value\":\s*(\d+\.?\d*)',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                try:
                    price = float(match)
                    if 0.01 < price < 100000:
                        return price
                except ValueError:
                    continue
        
        # Strategy 3: CSS selectors for price elements
        price_selectors = [
            "span.a-offscreen",
            ".a-price-whole",
            ".a-price .a-offscreen",
            "#priceblock_dealprice",
            "#priceblock_ourprice",
            "#priceblock_saleprice",
            ".a-price-range .a-offscreen",
            "[data-a-size='xl'] .a-offscreen",
            ".a-text-price .a-offscreen",
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                price_text = element.get_text(strip=True)
                if '$' in price_text:
                    cleaned = re.sub(r'[^\d.]', '', price_text)
                    if cleaned:
                        try:
                            price = float(cleaned)
                            if 0.01 < price < 100000:
                                return price
                        except ValueError:
                            continue
        
        return None
    
    def _extract_title_advanced(self, soup: BeautifulSoup) -> str:
        """Advanced title extraction"""
        title_selectors = [
            "#productTitle",
            "#title",
            "h1.a-size-large",
            ".a-size-extra-large",
            "#btAsinTitle",
            "span#productTitle",
            "h1.a-size-medium",
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        # Try meta tags as fallback
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            return meta_title['content']
        
        # Try title tag as last resort
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        
        return None
    
    async def scrape_amazon_product(self, url: str) -> Dict:
        """
        Enhanced Amazon scraper with better anti-detection
        """
        result = {
            "name": None,
            "price": None,
            "image_url": None,
            "site": "amazon.com",
            "success": False,
            "error": None,
            "method": "requests"
        }

        try:
            logger.info(f"🛒 Starting ENHANCED Amazon scraping: {url}")
            
            # Add random delay to appear human
            time.sleep(random.uniform(1, 3))
            
            # Fetch with rotating headers
            headers = self._get_rotating_headers()
            response = self.session.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            
            html_content = response.text
            
            # Check if we got a CAPTCHA page
            if self._is_captcha_page(html_content):
                result["error"] = "Amazon showed CAPTCHA page - request was blocked"
                logger.error("❌ Amazon CAPTCHA detected")
                return result
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Log sample of HTML for debugging
            logger.info(f"📄 HTML sample: {html_content[:500]}...")
            
            # EXTRACT DATA USING ADVANCED METHODS
            result["name"] = self._extract_title_advanced(soup)
            result["price"] = self._extract_price_advanced(soup, html_content)
            
            # EXTRACT IMAGE
            image_selectors = [
                "#landingImage",
                "#imgBlkFront", 
                ".a-dynamic-image",
                "[data-old-hires]",
                "[data-a-dynamic-image]",
                "img[data-a-image-name='landingImage']"
            ]
            
            for selector in image_selectors:
                element = soup.select_one(selector)
                if element:
                    src = element.get('src') or element.get('data-old-hires') or element.get('data-a-dynamic-image')
                    if src and isinstance(src, str) and 'http' in src:
                        # Extract URL from data attributes if needed
                        if src.startswith('{'):
                            try:
                                src_dict = json.loads(src)
                                if isinstance(src_dict, dict):
                                    src = list(src_dict.keys())[0] if src_dict else None
                            except:
                                pass
                        if src and 'http' in src:
                            result["image_url"] = src
                            break
            
            # Validate results
            if result["name"] and result["price"]:
                result["success"] = True
                logger.info(f"🎉 Amazon scrape SUCCESS: {result['name'][:30]}... - ${result['price']}")
            else:
                # Try one more approach - look for mobile version
                if not result["name"] or not result["price"]:
                    mobile_result = await self._try_mobile_version(url)
                    if mobile_result.get("success"):
                        return mobile_result
                
                missing = []
                if not result["name"]:
                    missing.append("name")
                if not result["price"]:
                    missing.append("price")
                result["error"] = f"Missing: {', '.join(missing)}. Amazon may be blocking requests."
                logger.warning(f"⚠️ Amazon scrape failed: {result['error']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Amazon scraping error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            result["error"] = error_msg
            return result
    
    async def _try_mobile_version(self, url: str) -> Dict:
        """Try mobile version of Amazon"""
        try:
            mobile_url = url.replace('www.amazon.com', 'm.amazon.com')
            logger.info(f"📱 Trying mobile version: {mobile_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
            
            response = self.session.get(mobile_url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Mobile-specific selectors
            title = soup.select_one('#title') or soup.select_one('.title')
            price = soup.select_one('.price') or soup.select_one('#price')
            
            result = {
                "name": title.get_text(strip=True) if title else None,
                "price": float(re.sub(r'[^\d.]', '', price.get_text())) if price else None,
                "image_url": None,
                "site": "amazon.com",
                "success": bool(title and price),
                "error": None if (title and price) else "Mobile version also failed",
                "method": "requests-mobile"
            }
            
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Mobile version also failed: {e}")
            return {"success": False}

# Global instance
amazon_scraper = AmazonScraper()