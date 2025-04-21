import csv
import os
import logging
import re
import xmlrpc.client
from dotenv import load_dotenv


load_dotenv()
ODOO_URL = os.getenv("ODOO_URL")
DB_NAME = os.getenv("DB_NAME")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Configure logging
logging.basicConfig(
    filename="import_contacts_to_odoo.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(DB_NAME, USERNAME, PASSWORD, {})
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")


def import_contacts(csv_file):
    counter = 0
    contact = 'contact'
    idx = 0
    with open(csv_file, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            first_name = row.get("First Name", "").strip()
            last_name = row.get("Last Name", "").strip()
            email = row.get("Email 1", "").strip().lower()
            phone = row.get("Phone 1", "").strip()
            mobile = row.get("Phone 2", "").strip()
            clean_phone = re.sub(r"[^\d+]", "", phone)
            clean_mobile = re.sub(r"[^\d+]", "", mobile)
            if not first_name and not last_name:
                if email:
                    name = email.split('@')[0]
                else:
                    name = f'{contact}_{idx}'
                    idx += 1
            else:
                name = f"{first_name} {last_name}".strip()
            contact_data = {
                "name": name,
                "phone": clean_phone if clean_phone else False,
                "mobile": clean_mobile if clean_mobile else False,
                "email": email if email else False,
                "is_company": False
            }
            if counter == 10:
                break

            try:
                existing = models.execute_kw(DB_NAME, uid, PASSWORD,
                                             "res.partner", "search_read",
                                             [[["email", "=", email]]],
                                             {"fields": ["id"], "limit": 1})
                if not existing:
                    models.execute_kw(DB_NAME, uid, PASSWORD,
                                      "res.partner", "create", [contact_data])
                    if counter % 100 == 0:
                        logging.info(f"Imported: {counter} contacts")
                    counter += 1
                else:
                    continue
                    logging.info(f"Skipped duplicate: {email}")
            except Exception as e:
                logging.error(f"Error importing {name}: {e}")
    logging.info(f'Imported {counter} successfully')


if __name__ == "__main__":
    import_contacts("contacts.csv")
