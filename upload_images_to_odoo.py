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
                    db_name, uid, password, "ir.model.data", "search_read",
                    [[["model", "=", "product.template"],
                      ["name", "=", external_id]]],
                    {"fields": ["res_id"]}
                )
            except Exception as e:
                logging.error(f'Error {e}: while reading {image_path}')
                continue

            if not product_ids:
                logging.warning(f"Product not found for External"
                                f"ID: {external_id}")
                continue

            product_id = product_ids[0]['res_id']

            # Update product with image
            models.execute_kw(
                db_name, uid, password, "product.template", "write",
                [[product_id], {"image_1920": image_data}]
            )
            counter += 1
            if counter % 100 == 0:
                logging.info(f"Uploaded images {counter}")
            if "extra_images" in row:
                extra_images = row["extra_images"]
                upload_extra_images(models, db_name, uid, password,
                                    product_id, extra_images, image_folder)
            if "Size" in row and row['Size'].strip():
                size_values = [size.strip() for size in row["Size"].split(',')
                               if size.strip()]
                update_product_sizes(models, db_name, uid, password,
                                     product_id, size_values)
            else:
                logging.info(f"Skipping size update for product {product_id} "
                             f"'Size' column is missing or empty.")

    logging.info(f"Main Image upload complete! {counter} images uploaded")


def upload_extra_images(models, db_name, uid, password, product_id,
                        extra_images, image_folder):
    """Uploads extra images to Odoo for a product."""
    counter = 0
    if extra_images:
        for image_name in extra_images.split(";"):
            image_path = os.path.join(image_folder, image_name.strip())

            if not os.path.exists(image_path):
                logging.warning(f"Extra image not found: {image_path}")
                continue

            try:
                with open(image_path, "rb") as img_file:
                    image_data = base64.b64encode(img_file.read()
                                                  ).decode("utf-8")

                models.execute_kw(
                    db_name, uid, password, "product.image", "create",
                    [{
                        "product_tmpl_id": product_id,
                        "image_1920": image_data,
                        "name": image_name
                    }]
                )
                counter += 1
                if counter % 100 == 0:
                    logging.info(f"Uploaded extra image progress:"
                                 f"{counter} images uploaded")

            except Exception as e:
                logging.error(f"Error uploading extra image {image_name}: {e}")
    logging.info(f"Extra Images upload complete! {counter} images uploaded")


def update_product_sizes(models, db_name, uid, password, product_id,
                         size_values):
    """Updates product attributes in Odoo based on the sizes provided."""

    if not size_values:
        logging.info(f"No sizes to update for product {product_id}")
        return

    # Ensure the attribute "Size" exists in Odoo
    size_attribute_id = models.execute_kw(
        db_name, uid, password, "product.attribute", "search",
        [[["name", "=", "Size"]]]
    )

    if not size_attribute_id:
        size_attribute_id = models.execute_kw(
            db_name, uid, password, "product.attribute", "create",
            [{"name": "Size"}]
        )
    else:
        size_attribute_id = size_attribute_id[0]  # Extract the ID

    # Get existing size values in Odoo
    existing_size_values = models.execute_kw(
        db_name, uid, password, "product.attribute.value", "search_read",
        [[["attribute_id", "=", size_attribute_id]]],
        {"fields": ["id", "name"]}
    )

    existing_size_dict = {val["name"]: val["id"] for val in
                          existing_size_values}

    size_value_ids = []
    for size in size_values:
        size = size.strip()
        if not size:
            continue

        if size in existing_size_dict:
            size_value_ids.append(existing_size_dict[size])
        else:
            # Create new size value
            new_size_id = models.execute_kw(
                db_name, uid, password, "product.attribute.value", "create",
                [{"name": size, "attribute_id": size_attribute_id}]
            )
            size_value_ids.append(new_size_id)
            existing_size_dict[size] = new_size_id  # Update cache

    # Link the sizes to the product
    models.execute_kw(
        db_name, uid, password, "product.template.attribute.line", "create",
        [{
            "product_tmpl_id": product_id,
            "attribute_id": size_attribute_id,
            "value_ids": [(6, 0, size_value_ids)]
        }]
    )

    logging.info(f"Updated sizes for product {product_id}: {size_values}")


if __name__ == "__main__":
    upload_images_to_odoo(
        odoo_url=ODOO_URL,
        db_name=DB_NAME,
        username=USERNAME,
        password=PASSWORD,
        csv_file="odoo_copy.csv",
        image_folder="compressed_images"
    )
