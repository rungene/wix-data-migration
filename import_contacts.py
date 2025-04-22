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
            if clean_phone.count('+') >= 2:
                parts = [f'+{p}' for p in clean_phone.split('+') if p]
                clean_phone = parts[0] if len(parts) > 0 else False
                clean_mobile = parts[1] if len(parts) > 1 else False
            else:
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
                "email": email if email else False,
                "is_company": False
            }
            if clean_phone:
                contact_data['phone'] = clean_phone
            if clean_mobile:
                contact_data['mobile'] = clean_mobile
            if counter == 100:
                break

            try:
                skip = False
                if email:
                    existing = models.execute_kw(DB_NAME, uid, PASSWORD,
                                                 "res.partner", "search_read",
                                                 [[["email", "=", email]]],
                                                 {"fields": ["id"],
                                                  "limit": 1})
                    if existing:
                        logging.info(f"Skipped duplicate: {email}")
                        skip = True
                if not skip:
                    models.execute_kw(DB_NAME, uid, PASSWORD,
                                      "res.partner", "create", [contact_data])
                    if counter % 100 == 0 and counter != 0:
                        logging.info(f"Imported: {counter} contacts")
                    counter += 1
            except Exception as e:
                logging.error(f"Error importing {name}: {e}")
    logging.info(f'Imported {counter} successfully')


if __name__ == "__main__":
    import_contacts("contacts.csv")
