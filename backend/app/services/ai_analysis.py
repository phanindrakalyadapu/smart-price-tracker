# app/services/ai_analysis.py
from openai import AsyncOpenAI
from app.core.config import settings

# ✅ Initialize the async OpenAI client with your API key
client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def analyze_product_with_gpt(name: str, old_price: float, new_price: float, description: str = None):
    """
    Returns:
      - ai_summary: short insight about the price change (stored in DB)
      - review_analysis: one-line summary of customer sentiment (not stored)
    """
    try:
        # 🧠 Build the GPT prompt
        prompt = f"""
        You are an e-commerce analyst.

        Product: {name}
        Old Price: ${old_price:.2f}
        New Price: ${new_price:.2f}
        Description: {description or "No description available"}

        Instructions:
        1️⃣ Write one concise sentence explaining whether the new price is a good deal or not.
           Mention the price change (drop/increase) clearly if possible.
        2️⃣ Write one concise sentence summarizing what customers generally say about this product
           (e.g., quality, reliability, satisfaction).

        Label them as:
        AI Insight: ...
        Review Analysis: ...
        """

        # 🚀 Call OpenAI using the new async API format
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # or gpt-4o
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0.7,
        )

        # ✅ Extract GPT response text
        output = response.choices[0].message.content.strip()

        # 🧩 Parse AI Insight and Review Analysis
        ai_summary, review_analysis = None, None
        for line in output.splitlines():
            if line.lower().startswith("ai insight:"):
                ai_summary = line.replace("AI Insight:", "").strip()
            elif line.lower().startswith("review analysis:"):
                review_analysis = line.replace("Review Analysis:", "").strip()

        print(f"🧠 {name} → AI Summary: {ai_summary} | Review: {review_analysis}")

        return ai_summary or "Not available", review_analysis or "Not available"

    except Exception as e:
        print(f"❌ Error analyzing {name}: {e}")
        return "Not available", "Not available"
