# this is learning how to parse csv file and using requests
import argparse
import csv
from os import name
import requests

def parse_csv(filename):
    file = open(filename).read().splitlines()
    csv_reader = csv.DictReader(file, delimiter=';')
    for row in csv_reader:
        send_request(data={
            'name': row['name'],
            'sku_no': row['sku_no'],
            'price': float(row['price']),
            'quantity': int(row['quantity']),
            'created_by': '1'
        })
        
def send_request(data):
    url = "http://localhost:8000/api/products"
    response = requests.post(url, json=data)
    if response.status_code == 201:
        print(f"Successfully sent data: {data}")
        print(f"response: {response.json()}")
    else:
        print(f"Failed to send data: {data}. Status code: {response.status_code}")
        print(f"response: {response.text}")

def main():
    # parsing filename as flag
    parse = argparse.ArgumentParser(description="Parse CSV file and send requests")
    parse.add_argument("--filename", type=str, required=True, help="Path to the CSV file")
    args = parse.parse_args()
    parse_csv(args.filename)

if __name__ == "__main__":
    main()