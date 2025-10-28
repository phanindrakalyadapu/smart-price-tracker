# app/services/insights.py
from statistics import mean

def price_is_it_worth(prices: list[float], current: float) -> str:
    if not prices:
        return "Not enough history yet. Track for a while."
    avg = mean(prices)
    if current < 0.9 * avg:
        return "Looks good — current price is clearly below the recent average."
    if current > 1.1 * avg:
        return "Price is above recent average. Consider waiting."
    return "Price looks typical for recent history."

def short_review_summary(_product_name: str) -> str:
    # Placeholder. Later, fetch reviews and summarize with your LLM.
    return "Reviews mention build quality and value. Consider checking color/size options."
