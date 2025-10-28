import os
import json
from fastapi import FastAPI
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import users, products, wishlist, price_history, health
from app.services.firecrawl_test import firecrawl_test
from app.services.pure_ai_scraper import pure_ai_scraper
from app.services.schedular import start_scheduler, shutdown_scheduler
from app.services.amazon_scraper import amazon_scraper
from app.routers import dashboard

# ✅ Load .env
from dotenv import load_dotenv
load_dotenv()

# Test if .env is loading
print("🔍 ENVIRONMENT CHECK IN MAIN.PY:")
print(f"FIRECRAWL_API_KEY: {'✅ LOADED' if os.getenv('FIRECRAWL_API_KEY') else '❌ NOT FOUND'}")

# ✅ Lifespan context manager (for scheduler)
@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    print("✅ Scheduler started.")
    yield
    shutdown_scheduler()
    print("🛑 Scheduler stopped.")

# ✅ Create single FastAPI instance
app = FastAPI(title="Smart Price Tracker API", lifespan=lifespan)

# ✅ CORS Configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

#add frontend url dynamically for stagging and prod
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Optional — Disable slash redirects to fix 307 issue
app.router.redirect_slashes = False

# ✅ Create DB tables
Base.metadata.create_all(bind=engine)

# ✅ Include all routers
app.include_router(health.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(wishlist.router)
app.include_router(price_history.router)
app.include_router(dashboard.router)

# ✅ Root endpoint
@app.get("/")
def home():
    return {"msg": "Smart Price Tracker API is running 🚀"}

# Add this to your main.py for testing
@app.post("/debug-scrape")
async def debug_scrape(url: str):
    """
    Test endpoint for Firecrawl product extraction
    """
    print(f"🧪 DEBUG: Testing Firecrawl with URL: {url}")
    
    # Test Firecrawl
    result = await firecrawl_test.test_extract_product(url)
    
    response_data = {
        "test_method": "firecrawl",
        "firecrawl_available": firecrawl_test.available,
        "url_tested": url,
        "result": result,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"🧪 DEBUG RESULT: {json.dumps(response_data, indent=2)}")
    
    return response_data

# Add this endpoint
@app.post("/debug-pure-ai-scrape")
async def debug_pure_ai_scrape(url: dict):
    """
    Test endpoint for Pure AI product extraction
    """
    print(f"🧠 PURE AI: Testing with URL: {url}")
    
    # Extract URL and site_type from the request
    product_url = url.get('url', '')
    site_type = url.get('site_type', 'auto')  # 'amazon', 'generic', or 'auto'
    
    print(f"🧠 Site type: {site_type}")
    
    # Route to appropriate scraper based on site_type
    if site_type == 'amazon' or ('amazon.com' in product_url and site_type == 'auto'):
        # Use Amazon scraper
        product = await pure_ai_scraper.amazon_scraper(product_url)
        scraper_used = "amazon_scraper"
    else:
        # Use generic scraper (or your original scrape_product if it still exists)
        try:
            # Try the new generic scraper first
            product = await pure_ai_scraper.generic_scraper(product_url)
            scraper_used = "generic_scraper"
        except AttributeError:
            # Fallback to original scrape_product if generic_scraper doesn't exist
            product = await pure_ai_scraper.scrape_product(product_url)
            scraper_used = "scrape_product"
    
    response_data = {
        "test_method": "pure_ai",
        "ai_scraper_available": pure_ai_scraper.available,
        "url_tested": product_url,
        "site_type": site_type,
        "scraper_used": scraper_used,
        "result": product,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"🧠 PURE AI RESULT: {json.dumps(response_data, indent=2)}")
    
    return response_data