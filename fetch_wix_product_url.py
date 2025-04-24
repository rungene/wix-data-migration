import requests
import csv
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    filename="fetch_wix_product_url.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()
# Define the API endpoint and authorization token
API_URL = os.getenv('API_URL')
PAGE_LIMIT = 20


# Fetch data from Wix
def fetch_wix_data():
    # headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    all_items = []
    page = 0
    while True:
        try:
            paginated_url = f"{API_URL}?page={page}&limit={PAGE_LIMIT}"
            response = requests.get(paginated_url)
            response.raise_for_status()

            data = response.json()
            if not data:
                logging.warning('Api returned an empty response.')
                break

            if not isinstance(data, dict) or 'items' not in data:
                logging.warning(f"Unexpected response format on"
                                f"page {page}: {data}")
                break

            items = data.get("items", [])

            all_items.extend(items)
            logging.info(f"Fetched page {page}, items: {len(items)}")
            if not data.get("hasNext", False):
                break
            page += 1
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data: {e}")
            break
    logging.info(f"Fetched {len(all_items)} items")
    return {"items": all_items}


# Save data to CSV
def save_to_csv(data, file_name="products_urls.csv"):
    # number = 0
    if not data:
        logging.error("No data to save.Exiting")
        return

    # Define CSV column headers
    headers = ["wix_product_url", "Name", 'created_date', 'slug']

    with open(file_name, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()

        row_count = 0
        for item in data:
            # if number == 50:
            #    break
            writer.writerow({
                "wix_product_url": item["productPageUrl"],
                "Name": item.get("name", ""),
                "created_date": item.get("createdDate", ""),
                "slug": item.get("slug", ""),
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
