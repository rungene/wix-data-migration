import requests
import csv
import os
import logging
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    filename="fetch_wix_data.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()
# Define the API endpoint and authorization token
API_URL = os.getenv('API_URL')


# Fetch data from Wix
def fetch_wix_data():
    # headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()

        if not data:
            logging.warning('Api returned an empty response.')
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data: {e}")
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
        logging.error("No data to save.Exiting")
        return

    # Define CSV column headers
    headers = ["External ID", "Name", "inStock", "product options",
               "Sales Description", "Product Type",
               "Sales Price", "price", "collections", "brand",
               "media items", "currency", "discount", "created date",
               "Image", "extra_images", "description_ecommerce"]

    with open(file_name, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()

        row_count = 0
        for item in data:
            # if number == 5:
            #    break
            writer.writerow({
                "External ID": item["_id"],
                "Name": item.get("name", ""),
                "inStock": item.get("inStock", ""),
                "product options": item.get("productOptions", ""),
                "Sales Description": remove_html_tags(
                    item.get("description", "")),
                "Product Type": "Goods",
                "Sales Price": item.get("discountedPrice", 0),
                "price": item.get("price", 0),
                "collections": item.get("collections", ""),
                "brand": item.get("brand", ""),
                "media items": item.get("mediaItems", ""),
                "currency": item.get("currency", ""),
                "discount": item.get("discount", ""),
                "created date": item.get("createdDate", ""),
                "Image": "",
                "extra_images": "",
                "description_ecommerce": remove_html_tags(
                    item.get("description", "")),
            })
            row_count += 1
            if row_count % 100 == 0:
                logging.info(f"Processed {row_count} rows...")
            # number += 1

    logging.info(f"Processed {row_count} rows. Data saved to {file_name}")


# Main process
if __name__ == "__main__":
    data = fetch_wix_data()

    # ensure data is a list, extract it if nested
    if isinstance(data, dict) and 'items' in data:
        # Extract items from dict contains 'items' key
        data = data['items']
    elif not isinstance(data, list):
        logging.error(f'Error: Expected a list of items, but got:'
                      '{type(data)}')
        exit(1)
    save_to_csv(data)
