import asyncio
import logging
from typing import Dict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class HybridScraper:
    def __init__(self):
        from app.services.scraper import UniversalProductScraper
        from app.services.ai_scraper import AIScraper
        
        self.traditional_scraper = UniversalProductScraper()
        self.ai_scraper = AIScraper()
        
        # Sites where traditional scraping works well (no AI needed)
        self.optimized_sites = {
            'amazon.com', 'nike.com', 'bestbuy.com', 'walmart.com',
            'target.com', 'apple.com', 'adidas.com', 'puma.com'
        }
    
    def _should_use_ai_first(self, url: str) -> bool:
        """Determine if we should try AI first"""
        try:
            domain = urlparse(url).netloc.lower()
            # Use AI for unknown sites, traditional for known sites
            return domain not in self.optimized_sites
        except:
            return True  # Use AI if URL parsing fails
    
    async def scrape_product(self, url: str) -> Dict:
        """Hybrid scraping - try best method first"""
        
        logger.info(f"🎯 Starting hybrid scrape for: {url}")
        
        # Fetch HTML once
        html = await self.traditional_scraper.fetch_html(url)
        if not html:
            return self._error_response("Failed to fetch page")
        
        # Strategy based on domain
        if self._should_use_ai_first(url):
            logger.info(f"🤖 Using AI-first approach for {url}")
            result = await self._scrape_with_ai_fallback(html, url)
        else:
            logger.info(f"⚡ Using traditional-first approach for {url}")
            result = await self._scrape_with_traditional_fallback(html, url)
        
        logger.info(f"📦 Final result - Price: ${result.get('price')}, Method: {result.get('method')}")
        return result
    
    async def _scrape_with_ai_fallback(self, html: str, url: str) -> Dict:
        """Try AI first, fallback to traditional"""
        ai_result = await self.ai_scraper.extract_product_info(html, url)
        
        # Use AI result if it has price and good confidence
        if ai_result and ai_result.get('price') and ai_result.get('confidence', 0) > 0.7:
            logger.info("✅ AI scraping successful")
            return self._format_ai_result(ai_result, url)
        
        logger.info("🔄 AI failed or low confidence, trying traditional scraping")
        return await self.traditional_scraper.scrape_product(url)
    
    async def _scrape_with_traditional_fallback(self, html: str, url: str) -> Dict:
        """Try traditional first, fallback to AI"""
        traditional_result = await self.traditional_scraper.scrape_product(url)
        
        if traditional_result and traditional_result.get('price'):
            logger.info("✅ Traditional scraping successful")
            return traditional_result
        
        logger.info("🔄 Traditional failed, trying AI")
        ai_result = await self.ai_scraper.extract_product_info(html, url)
        if ai_result and ai_result.get('price'):
            return self._format_ai_result(ai_result, url)
        
        # Return whichever result we have (even if no price)
        return traditional_result
    
    def _format_ai_result(self, ai_result: Dict, url: str) -> Dict:
        """Format AI result to match traditional scraper format"""
        from urllib.parse import urlparse

        # Get image from traditional scraper for better results
        image_url = None
        try:
            # Use traditional scraper to extract image
            import asyncio
            from bs4 import BeautifulSoup
        
            # Run the async fetch_html in a synchronous context
            html = asyncio.run(self.traditional_scraper.fetch_html(url))
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                image_url = self.traditional_scraper.extract_image_url(soup, url)
        except Exception as e:
            logger.warning(f"Could not extract image for AI result: {e}")
            pass

        return {
            "name": ai_result.get("name", "Unknown Product"),
            "price": ai_result.get("price"),
            "image_url": image_url,  # Now includes image from traditional scraping
            "site": urlparse(url).netloc,
            "success": True,
            "specs": {},
            "url": url,
            "method": "ai",
            "confidence": ai_result.get("confidence", 0),
            "available": ai_result.get("available", True),
            "currency": ai_result.get("currency", "USD")
        }

# Global instance
hybrid_scraper = HybridScraper()

# Main interface functions - REPLACE YOUR CURRENT ONES
async def scrape_product(url: str):
    """Main function to scrape products - uses hybrid approach"""
    return await hybrid_scraper.scrape_product(url)

async def scrape_multiple_products(urls: list):
    """Scrape multiple products concurrently"""
    tasks = [scrape_product(url) for url in urls]
    return await asyncio.gather(*tasks, return_exceptions=True)