import requests

def get_products():
    url = "http://localhost:8000/api/products"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to retrieve products. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return
    products = response.json()
    print("Products retrieved successfully:")
    for product in products.get('data', []):
        print(product)
        
def main():
    get_products()
        
if __name__ == "__main__":
    main()