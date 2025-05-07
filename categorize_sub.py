import csv
from io import StringIO
import os
import logging
import xmlrpc.client
from dotenv import load_dotenv

# Logging setup
logging.basicConfig(
    filename="categorize_sub.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load env vars
load_dotenv()
ODOO_URL = os.getenv("ODOO_URL")
DB_NAME = os.getenv("DB_NAME")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Odoo connection
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(DB_NAME, USERNAME, PASSWORD, {})
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")


# CSV Keyword Hierarchy Loader
def load_category_keywords(csv_data):
    category_map = []
    reader = csv.DictReader(StringIO(csv_data))
    for row in reader:
        keywords = [kw.strip().lower() for kw in
                    row["Keywords"].split(',') if kw.strip()]
        category_map.append({
            "main": row["Main Category"].strip(),
            "sub": row["Sub Category"].strip(),
            "subsub": row["Sub Sub Category"].strip(),
            "keywords": keywords
        })
    return category_map


# Category Matcher
def match_category_hierarchy(product_name, category_map):
    product_name = product_name.lower()
    for entry in category_map:
        if any(keyword in product_name for keyword in entry["keywords"]):
            return entry["main"], entry["sub"], entry["subsub"]
    return "Uncategorized", "", ""


# Odoo Helpers
def find_or_create(model_name, name, parent_id=None):
    domain = [["name", "=", name]]
    if parent_id:
        domain.append(["parent_id", "=", parent_id])
    ids = models.execute_kw(
        DB_NAME, uid, PASSWORD, model_name, 'search', [domain])
    if ids:
        return ids[0]
    values = {"name": name}
    if parent_id:
        values["parent_id"] = parent_id
    return models.execute_kw(
        DB_NAME, uid, PASSWORD, model_name, 'create', [values])


def get_or_create_category(main, sub, subsub, model_name='product.category'):
    if main == "Uncategorized":
        return None
    main_id = find_or_create(model_name, main)
    sub_id = find_or_create(model_name, sub, main_id) if sub else main_id
    subsub_id = find_or_create(
        model_name, subsub, sub_id) if subsub else sub_id
    return subsub_id


# Product Category Updater
def update_product_categories(product, matched_main, matched_sub,
                              matched_subsub):
    updated = False
    if matched_main == "Uncategorized":
        logging.info(f"Skipping Uncategorized product: {product['name']}")
        return

    product_id = product['id']

    # Internal category
    category_id = get_or_create_category(
        matched_main, matched_sub, matched_subsub,
        model_name='product.category')
    current_categ_id = product.get(
        'categ_id', [None])[0] if isinstance(
        product.get('categ_id'), list) else product.get('categ_id')
    if category_id and category_id != current_categ_id:
        models.execute_kw(DB_NAME, uid, PASSWORD, 'product.template', 'write',
                          [[product_id], {'categ_id': category_id}])
        update = True

    # POS category
    pos_cat_id = get_or_create_category(
        matched_main, matched_sub, matched_subsub, model_name='pos.category')
    current_pos_ids = product.get('pos_categ_ids', [])
    if pos_cat_id and pos_cat_id not in current_pos_ids:
        models.execute_kw(
            DB_NAME, uid, PASSWORD, 'product.template', 'write',
            [[product_id], {'pos_categ_ids': [(6, 0, [pos_cat_id])]}])

    # Website category
    website_cat_id = get_or_create_category(
        matched_main, matched_sub, matched_subsub,
        model_name='product.public.category')
    current_web_ids = product.get('public_categ_ids', [])
    if website_cat_id and website_cat_id not in current_web_ids:
        models.execute_kw(
            DB_NAME, uid, PASSWORD, 'product.template', 'write',
            [[product_id], {'public_categ_ids': [(6, 0, [website_cat_id])]}])

    return updated


# Main Execution
def main():
    updated_count = 0
    # Load keywords from CSV file
    with open("fashion_sub_categories.csv", encoding="utf-8") as f:
        csv_data = f.read()
    category_map = load_category_keywords(csv_data)

    # Fetch products
    product_ids = models.execute_kw(
        DB_NAME, uid, PASSWORD,
        'product.template', 'search', [[['sale_ok', '=', True]]])
    products = models.execute_kw(
        DB_NAME, uid, PASSWORD,
        'product.template', 'read', [product_ids],
        {'fields': ['id', 'name', 'categ_id',
                    'pos_categ_ids', 'public_categ_ids']})

    for product in products:
        name = product['name']
        matched_main, matched_sub, matched_subsub = match_category_hierarchy(
            name, category_map)
        if update_product_categories(
                product, matched_main, matched_sub, matched_subsub):
            updated_count += 1
            if updated_count % 100 == 0 and updated_count != 0:
                logging.info(f'{updated_count} products updated')
    logging.info(f"Total updated: {updated_count}")
    logging.info(f"Processed {len(products)} products."
                 f"Updated {updated_count}.")


if __name__ == '__main__':
    main()
