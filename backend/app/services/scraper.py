import re
import json
import aiohttp
import asyncio
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UniversalProductScraper:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
        self._update_headers()
        try:
            from app.services.ai_scraper import AIScraper
            self.ai_scraper = AIScraper()
            logger.info("✅ AI Scraper integrated")
        except ImportError:
            logger.warning("AI Scraper not available")
            self.ai_scraper = None

    def _update_headers(self):
        """Update headers with random user agent"""
        user_agent = random.choice(self.user_agents)
        
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate", 
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Pragma": "no-cache",
            "DNT": "1",
        }

    async def scrape_product_with_ai_fallback(self, url: str):
        """Enhanced scraper that uses AI as fallback when traditional fails."""
        print(f"🎯 Starting enhanced scrape for: {url}")
    
        # Fetch HTML once
        html = await self.fetch_html(url)
        if not html:
            return self.error_response("Failed to fetch page")
    
        soup = BeautifulSoup(html, 'html.parser')
        domain = urlparse(url).netloc

    # Debugging
        if 'amazon.com' in domain or 'a.co' in domain:
            self.debug_amazon_price_details(soup)
    
        self.debug_all_prices(soup, url)
    
        # STRATEGY 1: Traditional scraping (fast & free)
        traditional_result = await self._scrape_traditional(soup, url)
        if traditional_result and traditional_result.get('price'):
            print("✅ Traditional scraping successful")
            return traditional_result
    
        # STRATEGY 2: AI fallback (when traditional fails)
        if self.ai_scraper and self.ai_scraper.openai_available:
            print("🔄 Traditional failed, trying AI...")
            ai_result = await self.ai_scraper.extract_product_info(html, url)
        
            if ai_result and ai_result.get('price') and ai_result.get('confidence', 0) > 0.7:
                print("✅ AI extraction successful")
                return self._format_ai_result(ai_result, url, soup)
    
        # STRATEGY 3: Return whatever traditional found (even if no price)
        return traditional_result or self.error_response("No product information found")
    
    async def _scrape_traditional(self, soup, url: str):
        """Your existing traditional scraping logic."""
        domain = urlparse(url).netloc
    
        # Strategy 1: Try Schema.org structured data (most reliable)
        schema_data = self.extract_schema_data(soup)
        if schema_data and schema_data.get('name'):
            print("✅ Using Schema.org data")
            return {
                "name": schema_data.get('name'),
                "price": schema_data.get('price'),
                "image_url": schema_data.get('image_url'),
                "site": domain,
                "success": True,
                "specs": {},
                "url": url,
                "method": "schema"
            }
    
        # Strategy 2: Extract using traditional methods
        name = self.extract_product_name(soup)
        price = self.extract_price_from_page(soup)
        image_url = self.extract_image_url(soup, url)
    
        # Return if we found anything useful
        if name or price or image_url:
            return {
                "name": name or "Unknown Product",
                "price": price,
                "image_url": image_url,
                "site": domain,
                "success": True,
                "specs": {},
                "url": url,
                "method": "traditional"
            }
    
        return None
    
    def _format_ai_result(self, ai_result: dict, url: str, soup: BeautifulSoup):
        """Format AI result with image from traditional scraping."""
        # Use AI for name/price, but get image from traditional scraping
        image_url = self.extract_image_url(soup, url)
    
        return {
            "name": ai_result.get("name", "Unknown Product"),
            "price": ai_result.get("price"),
            "image_url": image_url,
            "site": urlparse(url).netloc,
            "success": True,
            "specs": {},
            "url": url,
            "method": "ai",
            "confidence": ai_result.get("confidence", 0),
            "available": ai_result.get("available", True),
            "currency": ai_result.get("currency", "USD")
        }
    
    def error_response(self, error: str):
        return {
            "name": "Unknown Product",
            "price": None,
            "image_url": None,
            "site": "",
            "success": False,
            "error": error,
            "method": "universal"
        }

    async def fetch_html(self, url: str):
        """Fetch HTML content with anti-bot measures."""
        max_retries = 3
        
        for attempt in range(max_retries):
            # Update headers with new user agent for each retry
            self._update_headers()
            
            # Add random delay between retries
            if attempt > 0:
                delay = random.uniform(2, 5)
                await asyncio.sleep(delay)
            
            html = await self._fetch_with_requests(url)
            if html:
                return html
            
            logger.warning(f"Attempt {attempt + 1} failed for {url}")
        
        logger.error(f"All {max_retries} attempts failed for {url}")
        return None

    async def _fetch_with_requests(self, url: str):
        """Fetch using requests library with better SSL handling."""
        try:
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            # Create session with retry strategy
            session = requests.Session()
            retry_strategy = Retry(
                total=2,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET"],
                backoff_factor=1
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # Enhanced headers for Amazon US site
            enhanced_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                # Amazon-specific headers
                "DNT": "1",
                "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            }
        
            # Add Amazon US parameters to force standard pricing
            parsed_url = urlparse(url)
            if 'amazon.com' in parsed_url.netloc or 'a.co' in parsed_url.netloc:
                # Force US English and standard pricing
                if '?' in url:
                    url += '&language=en_US&currency=USD'
                else:
                    url += '?language=en_US&currency=USD'
        
            response = session.get(
                url, 
                headers=enhanced_headers, 
                timeout=30,
                verify=False,
                cookies={  # Add Amazon US cookies
                    'session-id': '000-0000000-0000000',
                    'session-id-time': '2082787201l',
                    'i18n-prefs': 'USD',
                    'ubid-acbus': '000-0000000-0000000',
                }
            )
        
            if response.status_code == 200:
                logger.info(f"✅ Successfully fetched: {url}")
                return response.text
            else:
                logger.error(f"❌ HTTP {response.status_code} for {url}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Requests failed for {url}: {str(e)}")
            return None

    # ========== KEEP ALL YOUR EXISTING METHODS BELOW ==========
    # Just copy and paste all your existing methods below this line
    # Don't change anything below this line

    def extract_price(self, text):
        """Extract numeric price from any text format."""
        if not text:
            return None
        
        # More robust price extraction
        clean_text = str(text).replace(',', '').strip()
        
        # Multiple price patterns
        patterns = [
            r'\$?(\d+\.\d{2})',  # $159.99 (with cents)
            r'\$?(\d+)\.\d{2}',  # 159.99 (with cents)
            r'\$?(\d+\.\d{1,2})',  # $159.9 or $159.99
            r'\$?(\d+)',  # $159 (without cents)
            r'price["\']?\s*[:=]\s*["\']?\$?(\d+\.?\d{0,2})',  # "price": "159.99"
        ]
        
        # Try to find prices with cents first
        for pattern in patterns:
            matches = re.findall(pattern, clean_text, re.IGNORECASE)
            for match in matches:
                try:
                    price = float(match)
                    # More reasonable price range for products
                    if 1 < price < 10000:  # $1 to $10,000
                        return price
                except (ValueError, TypeError):
                    continue
        
        return None

    def debug_page_content(self, soup, url):
        """Debug function to see what's actually on the page"""
        domain = urlparse(url).netloc
        
        print(f"\n🔍 DEBUGGING {domain}:")
        
        # 1. Check for Schema.org data
        ld_scripts = soup.find_all('script', type='application/ld+json')
        print(f"📊 Found {len(ld_scripts)} JSON-LD scripts")
        for i, script in enumerate(ld_scripts):
            try:
                data = json.loads(script.string)
                type_info = data.get('@type', 'Unknown')
                print(f"   Script {i}: {type_info}")
                if 'Product' in str(type_info):
                    name = data.get('name', 'No name')
                    price = data.get('offers', {}).get('price', 'No price')
                    print(f"   🎯 PRODUCT FOUND: {name} - ${price}")
            except Exception as e:
                print(f"   Script {i}: Invalid JSON")
        
        # 2. Check for price elements in the entire page
        print("💰 SEARCHING FOR PRICES IN PAGE TEXT:")
        page_text = soup.get_text()
        price_matches = re.findall(r'\$\s*\d+\.?\d{0,2}|\d+\.?\d{0,2}\s*USD', page_text)
        for match in price_matches[:10]:
            print(f"   Price match: {match}")
        
        # 3. Check common price elements
        print("🔎 CHECKING PRICE ELEMENTS:")
        price_selectors = [
            '[class*="price"]',
            '[data-test*="price"]',
            '[id*="price"]',
            '[itemprop="price"]',
            '.price', '.cost', '.amount', '.value'
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for elem in elements[:2]:
                text = elem.get_text(strip=True)
                if text and len(text) < 100:
                    price = self.extract_price(text)
                    if price:
                        print(f"   ✅ {selector}: {text} -> ${price}")
                    else:
                        print(f"   ❌ {selector}: {text}")

    def extract_schema_data(self, soup):
        """Extract product data from Schema.org structured data."""
        # Look for JSON-LD data
        ld_scripts = soup.find_all('script', type='application/ld+json')
        
        for script in ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        if self._is_product_data(item):
                            result = self._parse_schema_product(item)
                            if result.get('name') and result.get('price'):
                                print("🎯 Using Schema.org data")
                                return result
                elif self._is_product_data(data):
                    result = self._parse_schema_product(data)
                    if result.get('name') and result.get('price'):
                        print("🎯 Using Schema.org data")
                        return result
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return None

    def _is_product_data(self, data):
        """Check if JSON-LD data contains product information."""
        product_types = ['Product', 'http://schema.org/Product', 'https://schema.org/Product']
        type_info = data.get('@type')
        
        if isinstance(type_info, list):
            return any(pt in type_info for pt in product_types)
        elif isinstance(type_info, str):
            return type_info in product_types or 'Product' in type_info
        
        return False

    def _parse_schema_product(self, data):
        """Parse Schema.org product data."""
        offers = data.get('offers', {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        
        image = data.get('image')
        if isinstance(image, list):
            image = image[0] if image else None
        elif isinstance(image, dict):
            image = image.get('url')
        
        return {
            'name': data.get('name'),
            'price': self.extract_price(offers.get('price') if offers else data.get('price')),
            'currency': offers.get('priceCurrency', 'USD') if offers else 'USD',
            'image_url': image,
            'description': data.get('description'),
            'brand': data.get('brand', {}).get('name') if isinstance(data.get('brand'), dict) else data.get('brand'),
            'method': 'schema'
        }

    def extract_price_from_page(self, soup):
        """Extract price using multiple strategies - returns the most likely product price."""
        strategies = [
            self._extract_price_css_selectors,
            self._extract_price_meta_tags,
            self._extract_price_regex,
        ]
        
        all_prices = []
        
        # Collect all prices from all strategies
        for strategy in strategies:
            try:
                price = strategy(soup)
            except TypeError:
                price = None
            if price:
                all_prices.append(price)
        
        # Debug: Show what we found
        if all_prices:
            print(f"🔍 Found prices from strategies: {all_prices}")
        
        # Prefer CSS selector price if available
        css_price = None
        try:
            css_price = self._extract_price_css_selectors(soup)
        except TypeError:
            css_price = None

        if css_price:
            print(f"🎯 CSS price found: {css_price}")
            # Use CSS-derived price if it looks reasonable
            if 1 < css_price < 10000:
                return css_price
        
        # Fallback: Use aggregated prices (choose median-like value)
        if all_prices:
            print(f"💰 All prices found: {all_prices}")
            reasonable_prices = [p for p in all_prices if isinstance(p, (int, float)) and 1 < p < 10000]
            if reasonable_prices:
                reasonable_prices.sort()
                most_likely = reasonable_prices[len(reasonable_prices) // 2]
                print(f"✅ Selected most likely price: ${most_likely}")
                return most_likely
        
        return None

    def _extract_price_css_selectors(self, soup, return_all=False):
        """Extract price using CSS selectors - can return all prices or just the most likely."""
        price_selectors = [
            # Amazon-specific price elements (HIGH PRIORITY)
            '.a-price-whole', '.a-price-fraction', '.a-offscreen',
            '#priceblock_dealprice', '#priceblock_ourprice', '#priceblock_saleprice',
            '.a-price .a-offscreen', 
        
            # Common e-commerce selectors
            '.price', '.product-price', '.current-price', '.selling-price',
            '.offer-price', '.price-current', '.price--current',
            '[data-test*="price"]', '[data-testid*="price"]',
            '[itemprop="price"]', '[class*="price__current"]',]
    
        found_prices = []
    
        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
             price_text = element.get_text(strip=True)
             price = self.extract_price(price_text)
            if price:
                print(f"✅ Price found with CSS: {selector} -> '{price_text}' -> ${price}")
                found_prices.append(price)
    
        if not found_prices:
            return None if not return_all else []
    
        if return_all:
            return found_prices
    
        # Return the most likely product price
        return self._find_most_likely_price(found_prices)
    
    def _filter_reasonable_prices(self, prices):
        """Filter out unreasonable prices that are clearly not product prices."""
        reasonable_prices = []
    
        for price in prices:
            # Product price range: $5 - $500 (adjust based on your products)
            if 5 <= price <= 500:
                reasonable_prices.append(price)
            # Special case: Allow up to $2000 for expensive items but with caution
            elif 500 < price <= 2000:
                # Only include expensive prices if they appear multiple times (more likely to be real)
                if prices.count(price) > 1:
                    reasonable_prices.append(price)
    
        print(f"🎯 After filtering: {reasonable_prices}")
        return reasonable_prices
    
    def _find_most_likely_price(self, prices):
        """Find the most likely product price from a list of prices."""
        if not prices:
            return None
    
        # Count frequency of each price
        from collections import Counter
        price_counts = Counter(prices)
    
        # Get the most common price
        most_common_price, count = price_counts.most_common(1)[0]
    
        print(f"📊 Price frequency: {dict(price_counts)}")
        print(f"🏆 Most common price: ${most_common_price} (appears {count} times)")
    
        # If we have a clear winner (appears multiple times), use it
        if count >= 2:
            return most_common_price
    
        # Otherwise, use statistical approach - avoid outliers
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
    
        # Use median if we have enough prices
        if n >= 3:
            median_price = sorted_prices[n // 2]
            print(f"📈 Median price: ${median_price}")
            return median_price
    
        # Fallback: average of reasonable prices
        reasonable = [p for p in prices if 10 <= p <= 500]
        if reasonable:
            avg_price = sum(reasonable) / len(reasonable)
            print(f"📊 Average reasonable price: ${avg_price}")
            return round(avg_price, 2)
    
        return sorted_prices[0]  # Last resort: first price

    def _extract_price_meta_tags(self, soup):
        """Extract price from meta tags."""
        meta_selectors = [
            'meta[property="og:price:amount"]',
            'meta[name="twitter:data1"]',
            'meta[itemprop="price"]',
            'meta[name="price"]'
        ]
        
        for selector in meta_selectors:
            element = soup.select_one(selector)
            if element and element.get('content'):
                price = self.extract_price(element['content'])
                if price:
                    print(f"✅ Price found in meta: {selector} -> ${price}")
                    return price
        
        return None
    
    def debug_amazon_price_details(self, soup):
        """Detailed Amazon price analysis"""
        print(f"\n🛒 AMAZON PRICE ANALYSIS:")
    
        # Check for different price types
        price_selectors = {
            'deal_price': '#priceblock_dealprice',
            'our_price': '#priceblock_ourprice', 
            'sale_price': '#priceblock_saleprice',
            'price_whole': '.a-price-whole',
            'price_fraction': '.a-price-fraction',
            'offscreen': '.a-offscreen'
        }
    
        for name, selector in price_selectors.items():
            elements = soup.select(selector)
            for i, element in enumerate(elements[:3]):
                text = element.get_text(strip=True)
                print(f"   {name}[{i}]: '{text}'")
    
        # Check for strike-through prices (original price)
        original_price = soup.select_one('.a-price.a-text-price .a-offscreen')
        if original_price:
            print(f"   💰 ORIGINAL PRICE: {original_price.get_text(strip=True)}")
    
        # Check for savings
        savings = soup.select_one('.a-span12.a-color-price .a-offscreen')
        if savings:
            print(f"   💵 SAVINGS: {savings.get_text(strip=True)}")


    def _extract_price_regex(self, soup):
        """Extract price using regex patterns in page text."""
        page_text = soup.get_text()
        
        # Look for price patterns in the entire page
        price_patterns = [
            r'\$\s*(\d+\.?\d{0,2})',  # $175.00
            r'price["\']?\s*[:=]\s*["\']?\$?(\d+\.?\d{0,2})',  # "price": "175.00"
            r'USD\s*(\d+\.?\d{0,2})',  # USD 175.00
            r'["\']price["\']\s*:\s*["\']\$?(\d+\.?\d{0,2})',  # 'price': '175.00'
            r'currentPrice["\']?\s*[:=]\s*["\']?\$?(\d+\.?\d{0,2})',  # currentPrice: 175.00
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                price = self.extract_price(match)
                if price:
                    print(f"✅ Price found with regex: {match} -> ${price}")
                    return price
        
        return None

    def extract_product_name(self, soup):
        """Extract product name using multiple strategies."""
        
        # BAD TITLES to exclude
        BAD_TITLES = [
            'popular search terms', 'search', 'nike', 'menu', 'navigation',
            'skip to main content', 'footer', 'header', 'breadcrumb'
        ]
        
        name_selectors = [
            # Nike specific - HIGH PRIORITY
            'h1#pdp_product_title',
            'h1.headline-2',
            '[data-test="product-title"]',
            '[data-testid="product-title"]',
            'h1.css-1os9jjn',
            'h1.css-1wd6q3p',
            
            # Common selectors - MEDIUM PRIORITY
            'h1.product-title', 'h1.pdp-title', 'h1.product-name',
            '[data-test*="title"]', '[data-testid*="title"]',
            '[itemprop="name"]', '.product-detail h1',
            'h1.title', 'h1.name',
            
            # Amazon specific
            '#productTitle',
            
            # Target specific
            'h1[data-test="product-title"]',
            
            # Generic fallback - LOW PRIORITY
            'h1', '.product-name', '[class*="product-title"]'
        ]
        
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text(strip=True)
                # BETTER VALIDATION: Exclude bad titles
                name_lower = name.lower()
                if (name and len(name) > 3 and 
                    name != "Unknown Product" and
                    not any(bad in name_lower for bad in BAD_TITLES) and
                    len(name) < 200):  # Reasonable length
                    print(f"✅ Name found: {selector} -> '{name}'")
                    return name
        
        # Fallback to page title with better cleaning
        if soup.title:
            title = soup.title.string
            if title:
                # Clean title (remove site name, etc.)
                clean_title = title.split('|')[0].split('-')[0].split('|')[0].strip()
                if (len(clean_title) > 3 and 
                    not any(bad in clean_title.lower() for bad in BAD_TITLES)):
                    print(f"✅ Using page title: '{clean_title}'")
                    return clean_title
        
        return "Unknown Product"

    def extract_image_url(self, soup, url):
        """Extract product image URL."""
        image_selectors = [
            # Common selectors
            'img.product-image', 'img.pdp-image', '[data-test*="image"]',
            '[itemprop="image"]', '.gallery img', '.product-hero img',
            'img.main-image', '.primary-image img', '#main-image img',
            # Amazon specific
            '#landingImage',
            # Nike specific
            'img[data-test="product-image"]', 'img.css-1fxh5tw',
            # Target specific
            'img[data-test="gallery-image"]',
            # Generic
            'img[src*="product"]', '.product-image img'
        ]
        
        for selector in image_selectors:
            element = soup.select_one(selector)
            if element:
                src = element.get('src') or element.get('data-src') or element.get('data-zoom')
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('//'):
                        src = f"https:{src}"
                    elif src.startswith('/'):
                        parsed_url = urlparse(url)
                        src = f"{parsed_url.scheme}://{parsed_url.netloc}{src}"
                    
                    if src.startswith('http') and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                        print(f"✅ Image found: {selector}")
                        return src
        
        return None

    async def scrape_product(self, url: str):
        """Universal product scraper that works for any website."""
        print(f"🎯 Starting scrape for: {url}")
        
        html = await self.fetch_html(url)
        if not html:
            return {
                "name": "Unknown Product",
                "price": None,
                "image_url": None,
                "site": urlparse(url).netloc,
                "success": False,
                "error": "Failed to fetch page"
            }
        
        soup = BeautifulSoup(html, 'html.parser')
        domain = urlparse(url).netloc

         # Amazon-specific debugging
        if 'amazon.com' in domain or 'a.co' in domain:
            self.debug_amazon_price_details(soup)

        # Enable debugging for ALL sites to see price issues
        self.debug_all_prices(soup, url)
        self.debug_page_content(soup, url)

        # Enable debugging for troubleshooting
        if "nike.com" in domain:
            self.debug_page_content(soup, url)
        
        base_data = {
            "name": "Unknown Product",
            "price": None,
            "image_url": None,
            "site": domain,
            "success": True,
            "specs": {},
            "url": url
        }
        
        # Strategy 1: Try Schema.org structured data (most reliable)
        schema_data = self.extract_schema_data(soup)
        if schema_data and schema_data.get('name'):
            print("✅ Using Schema.org data")
            return {**base_data, **schema_data}
        
        # Strategy 2: Extract using multiple methods
        name = self.extract_product_name(soup)
        price = self.extract_price_from_page(soup)
        image_url = self.extract_image_url(soup, url)
        
        result_data = {
            "name": name,
            "price": price,
            "image_url": image_url,
            "method": "universal"
        }
        
        print(f"📦 Scraped data: {result_data}")
        return {**base_data, **result_data}
    
    def debug_all_prices(self, soup, url):
        """Debug method to see ALL prices on the page."""
        print(f"\n🔍 DEBUGGING ALL PRICES ON PAGE:")
        
        # Method 1: Find all elements with price-like text
        price_like_elements = soup.find_all(string=re.compile(r'\$?\d+\.?\d{0,2}'))
        print("💰 ALL PRICE-LIKE TEXT ON PAGE:")
        for i, element in enumerate(price_like_elements[:20]):  # First 20 only
            text = element.strip()
            if len(text) < 50:  # Avoid long text blocks
                price = self.extract_price(text)
                print(f"   {i+1}. '{text}' -> ${price if price else 'NO MATCH'}")
        
        # Method 2: Check specific price elements
        price_selectors = ['.price', '.product-price', '.current-price', '[data-test*=\"price\"]']
        print("\n🎯 SPECIFIC PRICE ELEMENTS:")
        for selector in price_selectors:
            elements = soup.select(selector)
            for i, element in enumerate(elements[:3]):  # First 3 of each type
                text = element.get_text(strip=True)
                price = self.extract_price(text)
                print(f"   {selector}: '{text}' -> ${price if price else 'NO MATCH'}")

# Create global instance
universal_scraper = UniversalProductScraper()

# Main function (keep the same interface)
async def scrape_product(url: str):
    return await universal_scraper.scrape_product_with_ai_fallback(url)

# Keep your existing traditional function for specific use cases
async def scrape_product_traditional(url: str):
    return await universal_scraper.scrape_product(url)

# Batch scraping
async def scrape_multiple_products(urls: list):
    tasks = [scrape_product(url) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)

# Test function
async def test_scraper():
    """Test the scraper with various URLs"""
    test_urls = [
        "https://www.nike.com/t/air-force-1-07-mens-shoes-5QFp5Z/CW2288-111",
        "https://www.amazon.com/dp/B08N5WRWNW",  # Amazon product
        "https://www.bestbuy.com/site/macbook-pro-14-inch-2023/6534609.p",  # Best Buy
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Testing: {url}")
        print(f"{'='*60}")
        result = await scrape_product(url)
        print(f"Final Result: {result}")
        print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(test_scraper())