import csv
import os
import xmlrpc.client
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    filename="generate_redirects.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load environment variables
load_dotenv()
ODOO_URL = os.getenv("ODOO_URL")
DB_NAME = os.getenv("DB_NAME")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Set up Odoo connection
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(DB_NAME, USERNAME, PASSWORD, {})
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")


# Use the slug to search product in Odoo
def search_product(name, slug):
    name_clean = name.strip()
    results = models.execute_kw(DB_NAME, uid, PASSWORD,
                                "product.template", "search_read",
                                [[["name", "ilike", name_clean]]],
                                {"fields": ["website_url", "name"],
                                 "limit": 1})
    if results:
        return results[0]
    # If not found, try searching by slug inside website_url
    partial_slug = f'/shop/{slug}'
    results = models.execute_kw(DB_NAME, uid, PASSWORD,
                                "product.template", "search_read",
                                [[["website_url", "ilike", partial_slug]]],
                                {"fields": ["website_url", "name"],
                                 "limit": 1})
    return results[0] if results else None


# Main function to generate redirect mapping
def generate_redirect_mapping(input_csv, output_csv):
    counter = 0
    not_found = 0
    with open(input_csv, mode="r", encoding="utf-8") as infile, \
         open(output_csv, mode="w", newline="", encoding="utf-8") as outfile:

        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=["old_url", "new_url",
                                "matched_name"])
        writer.writeheader()

        for row in reader:
            old_url = row.get("wix_product_url", "").strip()
            name = row.get('Name', '').strip()
            slug = row.get("slug", "").strip()
            if not slug or not old_url:
                logging.info(f'Skipped {slug} or {old_url} empty')
                continue

            match = search_product(name, slug)
            if match:
                writer.writerow({
                    "old_url": old_url,
                    "new_url": match["website_url"],
                    "matched_name": match["name"]
                })
                if counter % 100 == 0 and counter != 0:
                    logging.info(f'{counter} slugs matched with urls')
                counter += 1
            else:
                not_found += 1
                writer.writerow({
                    "old_url": old_url,
                    "new_url": "NOT FOUND",
                    "matched_name": slug.replace("-", " ")
                })

    logging.info(f"Redirect mapping complete. Total {counter} slugs "
                 f"matched with urls")
    logging.info(f"Total {not_found} slugs not matched with Odoo products")


if __name__ == "__main__":
    generate_redirect_mapping("products_urls.csv", "redirect_mapping.csv")
