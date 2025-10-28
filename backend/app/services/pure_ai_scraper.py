import os
import json
import logging
import re
import random
import time
from typing import Dict
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class PureAIScraper:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')

        if not self.api_key:
            logger.error("❌ OPENAI_API_KEY not found in environment variables")
            self.available = False
            return

        self.available = True
        logger.info("✅ Pure AI Scraper initialized with GPT-4o")

        self.model = "gpt-4o"
        self.max_tokens = 1500
        self.temperature = 0.1

        # Enhanced user agents for Amazon
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        ]

        self.session = requests.Session()
        # Add retry strategy
        self.session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
        self.session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))

    def _get_amazon_headers(self) -> Dict:
        """Enhanced headers specifically for Amazon"""
        return {
            'User-Agent': random.choice(self.user_agents),
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
        }

    def _is_blocked_page(self, html_content: str) -> bool:
        """Check if Amazon is blocking with CAPTCHA or bot detection"""
        blocked_indicators = [
            'captcha',
            'enter the characters you see below',
            'sorry we just need to make sure you',
            'bot check',
            'access denied',
            'amazon.com/bot'
        ]
        
        html_lower = html_content.lower()
        return any(indicator in html_lower for indicator in blocked_indicators)

    def _is_amazon_product_page(self, html_content: str) -> bool:
        """Check if we're actually on an Amazon product page"""
        product_indicators = [
            'productTitle',
            'priceblock_',
            'add-to-cart',
            'buy-now-button',
            'asin',
        ]
        
        html_lower = html_content.lower()
        return any(indicator in html_lower for indicator in product_indicators)

    def _clean_html(self, html: str) -> str:
        """Clean HTML by removing scripts and styles"""
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
        html = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style.*?</style>', '', html, flags=re.DOTALL)
        html = re.sub(r'\s+', ' ', html)
        return html.strip()

    def _fetch_html(self, url: str) -> str:
        """Fetch HTML content from URL with Amazon-specific handling"""
        try:
            logger.info(f"📡 Fetching HTML from: {url}")
            
            # Use Amazon-specific headers
            headers = self._get_amazon_headers()
            
            # Add random delay to be more human-like
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            html_content = response.text
            
            # Check if we got blocked
            if self._is_blocked_page(html_content):
                logger.error("🚨 AMAZON BLOCKED: Captcha or bot detection triggered")
                raise Exception("Amazon blocked the request with CAPTCHA")
            
            # Check if we're actually on a product page
            if not self._is_amazon_product_page(html_content):
                logger.warning("⚠️ Not a product page - might be redirected to homepage")
            
            logger.info(f"✅ Fetched {len(html_content)} characters")
            return html_content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error fetching HTML: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to fetch HTML: {e}")
            raise

    def _debug_amazon_price_elements(self, soup: BeautifulSoup, html: str):
        """Debug method to see all Amazon price elements"""
        logger.info("🔍 DEBUG - Amazon Price Elements Analysis:")
        
        # Check for whole + fraction combination
        whole = soup.select_one(".a-price-whole")
        fraction = soup.select_one(".a-price-fraction")
        logger.info(f"🔍 Whole price element: '{whole.get_text(strip=True) if whole else 'NOT FOUND'}'")
        logger.info(f"🔍 Fraction price element: '{fraction.get_text(strip=True) if fraction else 'NOT FOUND'}'")
        
        if whole and fraction:
            logger.info(f"🔍 Combined: {whole.get_text(strip=True)}.{fraction.get_text(strip=True)}")
        
        # Check for current price elements
        current_price_selectors = [
            ".a-price .a-offscreen",
            ".a-price-range .a-price .a-offscreen",
            ".apexPriceToPay .a-offscreen",
            ".a-price[data-a-size='xl'] .a-offscreen"
        ]
        
        for selector in current_price_selectors:
            elements = soup.select(selector)
            for i, element in enumerate(elements[:3]):  # First 3 only
                logger.info(f"🔍 Current price ({selector}): '{element.get_text(strip=True)}'")
        
        # Check for list price elements
        list_price_selectors = [
            ".a-price.a-text-price .a-offscreen",
            ".a-text-strike",
            ".basisPrice .a-offscreen"
        ]
        
        for selector in list_price_selectors:
            elements = soup.select(selector)
            for i, element in enumerate(elements[:2]):  # First 2 only
                logger.info(f"🔍 List price ({selector}): '{element.get_text(strip=True)}'")
        
        # Look for any $X.XX pattern in HTML
        dollar_matches = re.findall(r'\$\d+\.\d{2}', html)
        if dollar_matches:
            unique_dollar_matches = list(set(dollar_matches))
            logger.info(f"🔍 All dollar amounts found: {unique_dollar_matches[:10]}")  # First 10 unique

    def _extract_price_directly(self, html_content: str, url: str) -> float:
        """
        Enhanced Amazon price extraction with discount price priority
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Strategy 1: Extract CURRENT/DISCOUNTED price first (highest priority)
            current_price = self._extract_current_price(soup, html_content)
            if current_price:
                logger.info(f"💰 Found CURRENT price: ${current_price}")
                return current_price
            
            # Strategy 2: JSON-LD structured data
            json_ld_price = self._extract_price_from_json_ld(soup)
            if json_ld_price:
                logger.info(f"💰 Found price in JSON-LD: ${json_ld_price}")
                return json_ld_price
            
            # Strategy 3: Amazon-specific price elements
            amazon_price = self._extract_amazon_price_enhanced(soup, html_content)
            if amazon_price:
                logger.info(f"💰 Found Amazon price: ${amazon_price}")
                return amazon_price
            
            # Strategy 4: Meta tags
            meta_price = self._extract_price_from_meta(soup)
            if meta_price:
                logger.info(f"💰 Found price in meta tags: ${meta_price}")
                return meta_price
            
            # Strategy 5: HTML patterns
            html_price = self._extract_price_from_html_patterns(html_content)
            if html_price:
                logger.info(f"💰 Found price in HTML patterns: ${html_price}")
                return html_price
            
            logger.warning("❌ Could not extract price directly from HTML")
            return None
            
        except Exception as e:
            logger.error(f"❌ Price extraction failed: {e}")
            return None

    def _extract_current_price(self, soup: BeautifulSoup, html: str) -> float:
        """
        Extract CURRENT/DISCOUNTED price with highest priority
        """
        try:
            # STRATEGY 1: Look for current price in specific Amazon elements
            current_price_selectors = [
                ".apexPriceToPay .a-offscreen",          # "Price to pay" - highest priority
                ".a-price[data-a-size='xl'] .a-offscreen", # Large price display
                ".a-price .a-offscreen",                 # Standard price
                ".a-price-range .a-price .a-offscreen",  # Price range (take first)
            ]
            
            for selector in current_price_selectors:
                elements = soup.select(selector)
                for element in elements:
                    price_text = element.get_text(strip=True)
                    if price_text and '$' in price_text:
                        price = self._extract_numeric_price(price_text)
                        if price and self._is_reasonable_price(price):
                            logger.info(f"💰 Found CURRENT price via {selector}: ${price}")
                            return price

            # STRATEGY 2: Look for price in data attributes (current price)
            current_price_patterns = [
                r'"priceAmount":\s*["\']?(\d+\.\d{2})["\']?',
                r'"buyingPrice":\s*["\']?(\d+\.\d{2})["\']?',
                r'"salePrice":\s*["\']?(\d+\.\d{2})["\']?',
                r'"currentPrice":\s*["\']?(\d+\.\d{2})["\']?',
            ]
            
            for pattern in current_price_patterns:
                matches = re.findall(pattern, html)
                for match in matches:
                    try:
                        price = float(match)
                        if self._is_reasonable_price(price):
                            logger.info(f"💰 Found CURRENT price via pattern '{pattern}': ${price}")
                            return price
                    except (ValueError, TypeError):
                        continue

            # STRATEGY 3: Combine whole + fraction (usually current price)
            whole_price_element = soup.select_one(".a-price-whole")
            fraction_price_element = soup.select_one(".a-price-fraction")
            
            if whole_price_element and fraction_price_element:
                whole_text = whole_price_element.get_text(strip=True).replace(',', '')
                fraction_text = fraction_price_element.get_text(strip=True)
                
                try:
                    combined_price = float(f"{whole_text}.{fraction_text}")
                    if self._is_reasonable_price(combined_price):
                        logger.info(f"💰 Found CURRENT price via whole+fraction: ${combined_price}")
                        return combined_price
                except (ValueError, TypeError):
                    pass

            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Current price extraction failed: {e}")
            return None

    def _extract_price_from_json_ld(self, soup: BeautifulSoup) -> float:
        """Extract price from JSON-LD structured data"""
        try:
            script_tags = soup.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    
                    # Handle both single object and array formats
                    if isinstance(data, list):
                        data = data[0]
                    
                    # Multiple possible price locations in JSON-LD
                    price_paths = [
                        data.get('offers', {}).get('price'),  # Current price
                        data.get('price'),
                        data.get('mainEntity', {}).get('offers', {}).get('price'),
                        data.get('aggregateOffer', {}).get('lowPrice'),  # Often current price
                        data.get('aggregateOffer', {}).get('highPrice'),
                    ]
                    
                    for price in price_paths:
                        if price:
                            return float(price)
                            
                except (json.JSONDecodeError, ValueError):
                    continue
                    
        except Exception as e:
            logger.debug(f"JSON-LD extraction failed: {e}")
            
        return None

    def _extract_amazon_price_enhanced(self, soup: BeautifulSoup, html: str) -> float:
        """Enhanced Amazon-specific price extraction that preserves cents"""
        try:
            logger.info("🔍 Starting enhanced Amazon price extraction...")
            
            # STRATEGY 1: Combine whole price and fraction parts
            whole_price_element = soup.select_one(".a-price-whole")
            fraction_price_element = soup.select_one(".a-price-fraction")
            
            if whole_price_element and fraction_price_element:
                whole_text = whole_price_element.get_text(strip=True).replace(',', '')
                fraction_text = fraction_price_element.get_text(strip=True)
                
                try:
                    combined_price = float(f"{whole_text}.{fraction_text}")
                    logger.info(f"💰 Found price via whole+fraction: ${combined_price}")
                    return combined_price
                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️ Failed to combine whole+fraction: {e}")

            # STRATEGY 2: Look for price in offscreen elements
            offscreen_elements = soup.select(".a-price .a-offscreen")
            for element in offscreen_elements:
                price_text = element.get_text(strip=True)
                if price_text and '$' in price_text:
                    price_match = re.search(r'\$?(\d+\.\d{2})', price_text)
                    if price_match:
                        try:
                            price = float(price_match.group(1))
                            if self._is_reasonable_price(price):
                                logger.info(f"💰 Found price in offscreen: ${price}")
                                return price
                        except (ValueError, TypeError):
                            continue

            # STRATEGY 3: Look for any dollar amount with cents
            dollar_cents_pattern = r'\$(\d+\.\d{2})\b'
            matches = re.findall(dollar_cents_pattern, html)
            for match in matches:
                try:
                    price = float(match)
                    if self._is_reasonable_price(price):
                        logger.info(f"💰 Found dollar amount with cents: ${price}")
                        return price
                except (ValueError, TypeError):
                    continue

            logger.warning("❌ Could not find price with cents")
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Amazon price extraction failed: {e}")
        
        return None

    def _extract_numeric_price(self, price_text: str) -> float:
        """Extract numeric price from text while preserving decimals"""
        try:
            if not price_text:
                return None
                
            logger.debug(f"🔍 Cleaning price text: '{price_text}'")
            
            # Extract complete price with cents
            complete_price_match = re.search(r'(\d+\.\d{2})', price_text)
            if complete_price_match:
                price = float(complete_price_match.group(1))
                logger.debug(f"🔍 Extracted complete price with cents: ${price}")
                return price
            
            # Extract any decimal price
            decimal_price_match = re.search(r'(\d+\.\d+)', price_text)
            if decimal_price_match:
                price = float(decimal_price_match.group(1))
                logger.debug(f"🔍 Extracted decimal price: ${price}")
                return price
                
            # Extract whole number only
            whole_price_match = re.search(r'(\d+)', price_text)
            if whole_price_match:
                price = float(whole_price_match.group(1))
                logger.debug(f"🔍 Extracted whole number only: ${price}")
                return price
                
            return None
                
        except Exception as e:
            logger.debug(f"❌ Error extracting numeric price from '{price_text}': {e}")
            return None

    def _is_reasonable_price(self, price: float) -> bool:
        """Check if price is within reasonable range"""
        return 0.01 < price < 100000

    def _extract_price_from_meta(self, soup: BeautifulSoup) -> float:
        """Extract price from meta tags"""
        try:
            meta_selectors = [
                'meta[property="product:price:amount"]',
                'meta[name="twitter:data1"]',
                'meta[itemprop="price"]',
                'meta[name="price"]',
                'meta[property="og:price:amount"]',
            ]
            
            for selector in meta_selectors:
                meta = soup.select_one(selector)
                if meta and meta.get('content'):
                    content = meta['content']
                    price = self._extract_numeric_price(content)
                    if price and self._is_reasonable_price(price):
                        return price
        except Exception as e:
            logger.debug(f"Meta price extraction failed: {e}")
        return None

    def _extract_price_from_html_patterns(self, html: str) -> float:
        """Extract price using regex patterns"""
        try:
            # Look for common price patterns
            price_patterns = [
                r'\$(\d+\.\d{2})',                    # $12.99 format with cents
                r'price["\']?\s*:\s*["\']?(\d+\.\d{2})',  # "price": "12.99"
                r'amount["\']?\s*:\s*["\']?(\d+\.\d{2})', # "amount": "12.99"
                r'value["\']?\s*:\s*["\']?(\d+\.\d{2})',  # "value": "12.99"
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    try:
                        price = float(match)
                        if self._is_reasonable_price(price):
                            return price
                    except (ValueError, TypeError):
                        continue
        except Exception as e:
            logger.debug(f"HTML pattern extraction failed: {e}")
        return None

    def _extract_with_gpt4o(self, html_content: str, url: str, direct_price: float = None) -> Dict:
        """Extract product data using GPT-4o with emphasis on current price"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)

            # Enhanced prompt for Amazon with current price emphasis
            price_context = ""
            if direct_price:
                price_context = f"\nIMPORTANT: Direct CURRENT price extraction found ${direct_price}. Use this exact price."

            prompt = f"""
            Extract product information from this AMAZON product page.

            URL: {url}
            {price_context}

            PAGE CONTENT (first 10000 characters):
            {html_content[:10000]}

            Return ONLY valid JSON with these fields:
            {{
                "name": "Exact visible product name/title",
                "price": 69.95, (MUST be the CURRENT/DISCOUNTED price, not list price. e.g., 69.95 not 99.95)
                "currency": "USD",
                "image_url": "Main product image URL",
                "description": "Product description or key features",
                "brand": "Brand name if available",
                "available": true,
                "color": "Product color if mentioned",
                "size": "Product size/dimensions if mentioned"
            }}

            CRITICAL FOR AMAZON:
            - The product name is always in <span id="productTitle"> or <meta property="og:title"> or "title" JSON-LD fields. Extract the exact text value without HTML tags, trimming whitespace and special symbols.
            - Price MUST be the CURRENT/DISCOUNTED price, NOT the list price
            - Look for patterns like -30% $69$ (this means current price is $69.95)
            - Ignore "List Price" or "Was $99.95" - those are old prices
            - Look for "Price: $69.95" or similar current price indicators
            - If multiple prices, choose the lower one (current/discounted price)
            - If price not found, use 0
            """

            logger.info("🚀 Sending to GPT-4o for analysis...")
        
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You extract product data from Amazon pages. Always return the CURRENT/DISCOUNTED price, not the list price. Price must be a number with decimals if available (0 if not found)."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content.strip()
            logger.info(f"📦 GPT-4o raw response: {result_text}")
        
            # Parse JSON response
            extracted_data = json.loads(result_text)
        
            # Validate and clean price
            price = extracted_data.get('price', 0)
            cleaned_price = self._clean_price(price)
            extracted_data['price'] = cleaned_price
        
            # Prefer direct price extraction if available
            if direct_price and cleaned_price != direct_price:
                logger.info(f"🔄 Using direct CURRENT price extraction: ${direct_price} vs GPT: ${cleaned_price}")
                extracted_data['price'] = direct_price
                extracted_data['price_source'] = 'direct_extraction'
            else:
                extracted_data['price_source'] = 'gpt_extraction'
            
            # ✅ Strong fallback title extraction logic
            name = extracted_data.get("name", "") or ""

            if not name or "product" in name.lower() or "title" in name.lower():
                logger.warning("⚠️ GPT name extraction weak — trying regex fallbacks")

                # Try standard Amazon title
                match = re.search(r'<span[^>]*id=["\']productTitle["\'][^>]*>(.*?)</span>', html_content, re.S | re.I)
                if match:
                    name = re.sub(r'\s+', ' ', match.group(1)).strip()
                    logger.info(f"🧩 Extracted productTitle span: {name}")
                else:
                    # Try meta tag
                    meta = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']', html_content, re.I)
                    if meta:
                        name = meta.group(1).strip()
                        logger.info(f"🧩 Extracted og:title: {name}")
                    else:
                        # Fallback to <title>
                        title_tag = re.search(r'<title>(.*?)</title>', html_content, re.S | re.I)
                        if title_tag:
                            raw_title = title_tag.group(1)
                            name = raw_title.replace("Amazon.com:", "").strip()
                            logger.info(f"🧩 Extracted <title>: {name}")

            extracted_data["name"] = name or "Unknown Product"    
        
            logger.info(f"✅ Final extracted: {extracted_data.get('name')} - ${extracted_data.get('price')}")
            return extracted_data

        except Exception as e:
            logger.error(f"❌ GPT-4o extraction failed: {e}")
            # Fallback with direct price
            return {
                "name": "Product",
                "price": direct_price if direct_price else 0,
                "currency": "USD",
                "price_source": "direct_fallback",
                "available": True
            }

    def _clean_price(self, price_value) -> float:
        """Clean and validate price value"""
        try:
            if price_value is None:
                return 0
            
            if isinstance(price_value, str):
                cleaned = re.sub(r'[^\d.]', '', price_value)
                return float(cleaned) if cleaned else 0
            
            if isinstance(price_value, (int, float)):
                return float(price_value) if price_value > 0 else 0
            
            return 0
        except Exception as e:
            logger.error(f"❌ Price cleaning failed: {e}")
            return 0

    async def amazon_scraper(self, url: str) -> Dict:
        """Main method to scrape Amazon product"""
        logger.info(f"🧠 Starting Amazon scrape for: {url}")

        if not self.available:
            return self._error_response("OpenAI API key not configured")

        try:
            # Step 1: Fetch HTML content
            html_content = self._fetch_html(url)

            # DEBUG: Analyze Amazon price elements
            soup = BeautifulSoup(html_content, 'html.parser')
            self._debug_amazon_price_elements(soup, html_content)
            
            # Step 2: Try direct price extraction first (with CURRENT price priority)
            direct_price = self._extract_price_directly(html_content, url)
            
            # Step 3: Clean HTML for GPT
            cleaned_html = self._clean_html(html_content)
            
            # Step 4: Extract with GPT-4o
            extracted_data = self._extract_with_gpt4o(cleaned_html, url, direct_price)
            
            # Step 5: Format final response
            return {
                "name": extracted_data.get("name"),
                "price": extracted_data.get("price", 0),
                "currency": extracted_data.get("currency", "USD"),
                "image_url": extracted_data.get("image_url"),
                "color": extracted_data.get("color"),
                "description": extracted_data.get("description"),
                "brand": extracted_data.get("brand"),
                "available": extracted_data.get("available", True),
                "site": urlparse(url).netloc,
                "url": url,
                "success": True,
                "method": "gpt-4o",
                "price_source": extracted_data.get("price_source", "gpt_extraction"),
                "direct_price_found": direct_price is not None,
                "direct_price_value": direct_price,  # Add this to see what was extracted directly
                "html_length": len(cleaned_html),
                "model_used": self.model
            }

        except Exception as e:
            logger.error(f"❌ Amazon scraping failed: {e}")
            return self._error_response(f"Scraping failed: {str(e)}")

    def _error_response(self, error: str) -> Dict:
        return {
            "name": None,
            "price": None,
            "image_url": None,
            "site": "",
            "success": False,
            "error": error,
            "method": "gpt-4o"
        }
    
    async def generic_scraper(self, url: str) -> Dict:
        """Generic scraper for all non-Amazon websites"""
        logger.info(f"🌐 Starting GENERIC scrape for: {url}")

        if not self.available:
            return self._error_response("OpenAI API key not configured")

        try:
            # Step 1: Fetch HTML content with generic headers
            html_content = self._fetch_generic_html(url)
        
            # Step 2: Try generic price extraction strategies
            direct_price = self._extract_generic_price(html_content, url)
        
            # Step 3: Clean HTML for GPT
            cleaned_html = self._clean_html(html_content)
        
            # Step 4: Extract with GPT-4o (with generic prompt)
            extracted_data = self._extract_with_gpt4o_generic(cleaned_html, url, direct_price)
        
            # Step 5: Format final response
            return {
                "name": extracted_data.get("name"),
                "price": extracted_data.get("price", 0),
                "currency": extracted_data.get("currency", "USD"),
                "image_url": extracted_data.get("image_url"),
                "color": extracted_data.get("color"),
                "description": extracted_data.get("description"),
                "brand": extracted_data.get("brand"),
                "available": extracted_data.get("available", True),
                "site": urlparse(url).netloc,
                "url": url,
                "success": True,
                "method": "gpt-4o-generic",
                "price_source": extracted_data.get("price_source", "gpt_extraction"),
                "direct_price_found": direct_price is not None,
                "direct_price_value": direct_price,
                "html_length": len(cleaned_html),
                "model_used": self.model,
                "scraper_type": "generic"  # Identify this as generic scraper
            }

        except Exception as e:
            logger.error(f"❌ Generic scraping failed: {e}")
            return self._error_response(f"Generic scraping failed: {str(e)}")
        
    def _fetch_generic_html(self, url: str) -> str:
        """Fetch HTML for generic websites"""
        try:
            logger.info(f"📡 Fetching GENERIC HTML from: {url}")
        
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
        
            # Shorter delay for generic sites
            time.sleep(random.uniform(0.5, 2))
        
            response = self.session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        
            html_content = response.text
            logger.info(f"✅ Fetched {len(html_content)} characters (generic)")
            return html_content
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch generic HTML: {e}")
            raise

    def _extract_generic_price(self, html_content: str, url: str) -> float:
        """Generic price extraction for non-Amazon sites"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
        
            # Strategy 1: JSON-LD structured data (works for most e-commerce sites)
            json_ld_price = self._extract_price_from_json_ld(soup)
            if json_ld_price:
                logger.info(f"💰 Found price in JSON-LD: ${json_ld_price}")
                return json_ld_price
        
            # Strategy 2: Meta tags
            meta_price = self._extract_price_from_meta(soup)
            if meta_price:
                logger.info(f"💰 Found price in meta tags: ${meta_price}")
                return meta_price
        
            # Strategy 3: Common CSS selectors across e-commerce sites
            generic_price_selectors = [
                '.price', '.product-price', '.current-price', '.sale-price',
                '[data-price]', '.value', '.amount', '.cost',
                '.price-current', '.price--current', '.product-cost',
                '.pricing', '.money', '.currency'
            ]
        
            for selector in generic_price_selectors:
                elements = soup.select(selector)
                for element in elements:
                    price_text = element.get_text(strip=True)
                    if price_text and any(char.isdigit() for char in price_text):
                        price = self._extract_numeric_price(price_text)
                        if price and self._is_reasonable_price(price):
                            logger.info(f"💰 Found price via selector '{selector}': ${price}")
                            return price
        
            # Strategy 4: Regex patterns in HTML
            price_patterns = [
                r'"price":\s*["\']?(\d+\.\d{2})["\']?',
                r'"amount":\s*["\']?(\d+\.\d{2})["\']?',
                r'"value":\s*["\']?(\d+\.\d{2})["\']?',
                r'data-price="(\d+\.\d{2})"',
                r'content="\$\s*(\d+\.\d{2})"',
            ]
        
            for pattern in price_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    try:
                        price = float(match)
                        if self._is_reasonable_price(price):
                            logger.info(f"💰 Found price via pattern '{pattern}': ${price}")
                            return price
                    except (ValueError, TypeError):
                        continue
        
            logger.warning("❌ Could not extract price from generic site")
            return None
        
        except Exception as e:
            logger.error(f"❌ Generic price extraction failed: {e}")
            return None

    def _extract_with_gpt4o_generic(self, html_content: str, url: str, direct_price: float = None) -> Dict:
        """GPT-4o extraction optimized for generic e-commerce sites"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)

            price_context = ""
            if direct_price:
                price_context = f"\nDIRECT PRICE EXTRACTION FOUND: ${direct_price}. Use this as reference."

            prompt = f"""
            Extract product information from this e-commerce product page.

            URL: {url}
            {price_context}

            PAGE CONTENT (first 8000 characters):
            {html_content[:8000]}

            Return ONLY valid JSON with these fields:
            {{
                "name": "Product title",
                "price": 49.99, (MUST be a number, never text. Use direct price if available)
                "currency": "USD",
                "image_url": "Main product image URL",
                "description": "Product description or key features",
                "brand": "Brand name if available",
                "available": true,
                "color": "Product color if mentioned",
                "size": "Product size/dimensions if mentioned"
            }}

            IMPORTANT:
            - Look for product title in h1, .product-title, [itemprop="name"] elements
            - Price should be the current selling price, not original price
            - If multiple prices found, choose the one that seems like current price
            - Look for patterns like $49.99, 49.99, etc.
            - Never return "None" or null for price - use 0 if not found
            """

            logger.info("🚀 Sending to GPT-4o for GENERIC analysis...")
    
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You extract product data from e-commerce pages. Always return valid JSON. Price must be a number (0 if not found)."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content.strip()
            logger.info(f"📦 GPT-4o generic response: {result_text}")
    
            extracted_data = json.loads(result_text)
    
            # Validate and clean price
            price = extracted_data.get('price', 0)
            cleaned_price = self._clean_price(price)
            extracted_data['price'] = cleaned_price
    
            # Prefer direct price extraction if available
            if direct_price and cleaned_price != direct_price:
                logger.info(f"🔄 Using direct price: ${direct_price} vs GPT: ${cleaned_price}")
                extracted_data['price'] = direct_price
                extracted_data['price_source'] = 'direct_extraction'
            else:
                extracted_data['price_source'] = 'gpt_extraction'
    
            logger.info(f"✅ Generic extraction: {extracted_data.get('name')} - ${extracted_data.get('price')}")
            return extracted_data

        except Exception as e:
            logger.error(f"❌ GPT-4o generic extraction failed: {e}")
            return {
                "name": "Product",
                "price": direct_price if direct_price else 0,
                "currency": "USD",
                "price_source": "direct_fallback",
                "available": True
        }

# Global instance
pure_ai_scraper = PureAIScraper()