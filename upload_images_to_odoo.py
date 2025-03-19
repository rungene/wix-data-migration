import csv
import xmlrpc.client
import base64
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
    filename="upload_images_to_odoo.log",  # Save logs to a file
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def upload_images_to_odoo(odoo_url, db_name, username, password,
                          csv_file, image_folder):
    """Uploads product images to Odoo from a CSV file."""

    # Connect to Odoo
    common = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/common")
    uid = common.authenticate(db_name, username, password, {})

    if not uid:
        logging.error("Failed to authenticate with Odoo. Check credentials.")
        return

    models = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/object")
    counter = 0
    # Read CSV file
    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            external_id = row.get("External ID")
            image_name = row.get("Image")

            if not external_id or not image_name:
                logging.warning(f'{row} skipped')
                continue  # Skip rows with missing data

            image_path = os.path.join(image_folder, image_name)

            if not os.path.exists(image_path):
                logging.warning(f"Image not found: {image_path}")
                continue
            try:
                # Read image and encode in base64
                with open(image_path, "rb") as img_file:
                    image_data = base64.b64encode(img_file.read()
                                                  ).decode("utf-8")

                # Find product by External ID
                product_ids = models.execute_kw(
                    db_name, uid, password, "product.template", "search",
                    [[["external_id", "=", external_id]]]
                )
            except Exception as e:
                logging.error(f'Error {e}: while reading {image_path}')
                continue

            if not product_ids:
                logging.warning(f"Product not found for External"
                                f"ID: {external_id}")
                continue

            product_id = product_ids[0]

            # Update product with image
            models.execute_kw(
                db_name, uid, password, "product.template", "write",
                [[product_id], {"image_1920": image_data}]
            )
            counter += 1
            if counter % 100 == 0:
                logging.info(f"Uploaded images {counter}")

    logging.info(f"Image upload completed! {counter} images uploaded")


if __name__ == "__main__":
    upload_images_to_odoo(
        odoo_url=ODOO_URL,
        db_name=DB_NAME,
        username=USERNAME,
        password=PASSWORD,
        csv_file="odoo_copy.csv",
        image_folder="compressed_images"
    )
