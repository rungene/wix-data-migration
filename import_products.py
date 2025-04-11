import csv
import xmlrpc.client
import os
import logging
from dotenv import load_dotenv

load_dotenv()
ODOO_URL = os.getenv('ODOO_URL')
DB_NAME = os.getenv('DB_NAME')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

# Configure logging
logging.basicConfig(
    filename="import_products_to_odoo.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(DB_NAME, USERNAME, PASSWORD, {})

if not uid:
    logging.error("Failed to authenticate with Odoo.")
    exit()

models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

BATCH_SIZE = 100


def import_products(csv_file):
    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        batch = []
        product_type_map = {
            "Goods": "consu",
            "Combo": "combo",
            "Service": "service"
        }

        for row in reader:
            external_id = row.get("External ID", "").strip()
            if not external_id:
                logging.warning(f"Skipping '{row.get('Name', 'Unknown')}'"
                                f"- Missing External ID")
                continue  # Skip products without External ID

            # Check if External ID already exists in Odoo
            existing_product = models.execute_kw(
                DB_NAME, uid, PASSWORD, "ir.model.data", "search_read",
                [[["model", "=", "product.template"],
                  ["name", "=", external_id]]], {"fields": ["res_id"]})

            if existing_product:
                logging.info(f"Product '{row['Name']}' already exists."
                             f"Skipping.")
                continue  # Avoid duplicate creation

            # Prepare product data
            product_data = {
                "name": row["Name"],
                "description_sale": row.get("Sales Description", ""),
                "standard_price": row.get("standard_price", 0.00),
                "type": product_type_map.get(row.get("Product Type",
                                             "").strip(), "consu"),
                "list_price": float(row.get("Sales Price", 0.0)),
                "is_published": (row.get("is_published",
                                         "False").strip().lower() == "true"),
                "is_storable": (row.get("is_storable",
                                        "False").strip().lower() == "true"),
                "description_ecommerce": row.get("Sales Description", ""),
                "allow_out_of_stock_order": (
                    row.get("allow_out_of_stock_order",
                            "False").strip().lower() == "true"),
                "available_in_pos": row.get("available_in_pos",
                                            "False").strip().lower() == "true",
            }

            batch.append((external_id, product_data))

            # Process batch when it reaches BATCH_SIZE
            if len(batch) >= BATCH_SIZE:
                process_batch(batch)
                batch = []  # Reset batch

        # Process remaining batch
        if batch:
            process_batch(batch)


def process_batch(batch):
    """Processes and imports a batch of products into Odoo."""
    created_products = []

    for external_id, product_data in batch:
        try:
            product_id = models.execute_kw(
                DB_NAME, uid, PASSWORD, "product.template",
                "create", [product_data])

            # Register External ID in Odoo
            models.execute_kw(
                DB_NAME, uid, PASSWORD, "ir.model.data", "create",
                [{
                    "name": external_id,
                    "module": "__import__",
                    "model": "product.template",
                    "res_id": product_id
                }]
            )
            created_products.append(product_id)
        except Exception as e:
            logging.error(f"Error creating product"
                          f"'{product_data['name']}': {e}")

    logging.info(f"Imported {len(created_products)} products.")


if __name__ == "__main__":
    csv_file = "products_with_absolute_urls.csv"
    import_products(csv_file)
