import requests
import concurrent.futures

# --- CONFIGURATION ---
BASE_URL = "http://127.0.0.1:5000"
PRODUCT_ID = 1  # The ID of the product we are buying
LOGIN_DATA = {
    "email": "admin@gymshop.local", #We will make the purchases through the admin user
    "password": "admin123"     
}

def shopaholic_buyer(worker_id):
    """Simulates one single customer going through the purchase flow."""
    #We create a virtual browser session
    client = requests.Session()
    
    #Log in
    client.post(f"{BASE_URL}/login", data=LOGIN_DATA)
    
    #Add the item to the cart
    client.get(f"{BASE_URL}/add_to_cart/{PRODUCT_ID}")
    
    #Hit the checkout route
    response = client.get(f"{BASE_URL}/checkout")
    
#Result
    if "Order placed successfully" in response.text:
        return f"🟢 Worker {worker_id}: SUCCESS - Got one!"
    elif "left in stock" in response.text or "out of stock" in response.text:
        return f"🔴 Worker {worker_id}: FAILED - Too slow"
    elif "Your cart is empty" in response.text:
        return f"🟡 Worker {worker_id}: ERROR - The 'Add to cart' step failed! Cart is empty."
    else:
        #Error check, if stop working check what route they ended on
        return f"🟡 Worker {worker_id}: ERROR - Ended up on URL: {response.url}"
if __name__ == "__main__":
    print(f"Starting Load Test: 50 Shopaholics rushing to buy Product #{PRODUCT_ID}...")
    
    #Run 50 threads at the exact same time
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(shopaholic_buyer, i) for i in range(1, 51)]
        
        #Print the results
        for future in concurrent.futures.as_completed(futures):
            print(future.result())
            
    print("Load test complete!")