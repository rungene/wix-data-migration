import requests
import csv
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
# Define the API endpoint and authorization token
API_URL = os.getenv('API_URL')


# Fetch data from Wix
def fetch_wix_data():
    # headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []


# Remove HTML tags from description
def remove_html_tags(text):
    if text is None:
        return ""
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text().strip()


# Save data to CSV
def save_to_csv(data, file_name="products.csv"):
    # number = 0
    if not data:
        print("No data to save.")
        return

    # Define CSV column headers
    headers = ["id", "name", "inStock", "product options", "description",
               "discounted price", "price", "collections", "brand",
               "media items", "currency", "discount", "created date"]

    with open(file_name, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()

        for item in data:
            # if number == 5:
            #    break
            print(f"Item data: {item}")
            writer.writerow({
                "id": item["_id"],
                "name": item.get("name", ""),
                "inStock": item.get("inStock", ""),
                "product options": item.get("productOptions", ""),
                "description": remove_html_tags(item.get("description", "")),
                "discounted price": item.get("discountedPrice", 0),
                "price": item.get("price", 0),
                "collections": item.get("collections", ""),
                "brand": item.get("brand", ""),
                "media items": item.get("mediaItems", ""),
                "currency": item.get("currency", ""),
                "discount": item.get("discount", ""),
                "created date": item.get("createdDate", ""),
            })
            # number += 1

    print(f"Data saved to {file_name}")


# Main process
if __name__ == "__main__":
    data = fetch_wix_data()

    # ensure data is a list, extract it if nested
    if isinstance(data, dict) and 'items' in data:
        # Extract items from dict contains 'items' key
        data = data['items']
    elif not isinstance(data, list):
        print('Error: Expected a list of items, but got:', type(data))
        exit(1)
    save_to_csv(data)
