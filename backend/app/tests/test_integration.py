import pytest

# -----------------------------------------------------
# 🧪 End-to-End Integration Tests
# -----------------------------------------------------
def test_end_to_end(client):
    # -----------------------------------------------------
    # 1️⃣ Create user
    # -----------------------------------------------------
    user_payload = {
        "first_name": "xyz",
        "last_name": "abc",
        "email": "abc@example.com"
    }

    user_response = client.post("/users/", json=user_payload)
    print("👤 User response:", user_response.json())
    assert user_response.status_code in (200, 201)

    user_id = user_response.json().get("id") or 1

    # -----------------------------------------------------
    # 2️⃣ Create product
    # -----------------------------------------------------
    product_payload = {
        "name": "Apple iPhone 16",
        "url": "https://example.com/iphone16",
        "target_price": 999.99,
        "image_url": "https://example.com/img/iphone16.jpg"
    }

    product_response = client.post("/products/", json=product_payload)
    print("📦 Product response:", product_response.json())
    assert product_response.status_code in (200, 201)

    product_id = product_response.json().get("id") or 1

    # -----------------------------------------------------
    # 3️⃣ Add product to wishlist
    # -----------------------------------------------------
    wishlist_payload = {
        "user_id": user_id,
        "product_id": product_id
    }

    wishlist_response = client.post("/wishlist/", json=wishlist_payload)
    print("📝 Wishlist response:", wishlist_response.json())
    assert wishlist_response.status_code in (200, 201)

    wishlist_id = wishlist_response.json().get("id") or 1

    # -----------------------------------------------------
    # 4️⃣ Get all users
    # -----------------------------------------------------
    users_list = client.get("/users/")
    assert users_list.status_code == 200
    print("📋 Users:", users_list.json())
    assert len(users_list.json()) >= 1

    # -----------------------------------------------------
    # 5️⃣ Get all products
    # -----------------------------------------------------
    products_list = client.get("/products/")
    assert products_list.status_code == 200
    print("📦 Products:", products_list.json())
    assert len(products_list.json()) >= 1

    # -----------------------------------------------------
    # 6️⃣ Get wishlist for this user
    # -----------------------------------------------------
    wishlist_list = client.get(f"/wishlist/{user_id}")
    assert wishlist_list.status_code == 200
    print("💖 Wishlist:", wishlist_list.json())
    assert len(wishlist_list.json()) >= 1

    # -----------------------------------------------------
    # ✅ All done
    # -----------------------------------------------------
    print("\n✅ End-to-end test passed successfully!\n")
