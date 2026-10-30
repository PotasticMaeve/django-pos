# this is learning how to parse csv file and using requests
import argparse
import csv
import getpass
import requests

BASE_URL = "http://localhost:8000"

def parse_csv(filename, token):
    file = open(filename).read().splitlines()
    csv_reader = csv.DictReader(file, delimiter=';')
    for row in csv_reader:
        send_request(data={
            'name': row['name'],
            'sku_no': row['sku_no'],
            'price': float(row['price']),
            'quantity': int(row['quantity']),
            'created_by': '1'
        }, token=token)
        
def send_request(data, token):
    url = f"{BASE_URL}/products"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        print(f"Successfully sent data: {data}")
        print(f"response: {response.json()}")
    else:
        print(f"Failed to send data: {data}. Status code: {response.status_code}")
        print(f"response: {response.text}")

def login():
    username = input("username: ").strip()
    password = getpass.getpass("password: ").strip()
    if not username or not password:
        print("Username and password are required.")
        return None

    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": username, "password": password}
    )
    if response.status_code != 200:
        print(f"Login failed. status code: {response.status_code}")
        print(f"response: {response.text}")
        return None
    return response.json()["access"]

def main():
    # parsing filename as flag
    parse = argparse.ArgumentParser(description="Parse CSV file and send requests")
    parse.add_argument("--filename", type=str, required=True, help="Path to the CSV file")
    args = parse.parse_args()

    token = login()
    if not token:
        print("stopping: couldn't authenticate")
        return None
    parse_csv(args.filename, token)

if __name__ == "__main__":
    main()