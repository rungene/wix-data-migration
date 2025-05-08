import csv
import os
import xmlrpc.client
from collections import defaultdict
import logging
import re
from dotenv import load_dotenv

# Logging setup
logging.basicConfig(
    filename="uncategorize_categorize_main.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load environment variables
load_dotenv()
ODOO_URL = os.getenv("ODOO_URL")
DB_NAME = os.getenv("DB_NAME")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(DB_NAME, USERNAME, PASSWORD, {})
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")


# Load keywords from CSV
def main_categories(in_file):
    category_keywords = defaultdict(list)
    with open(in_file, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            for category, keyword in row.items():
                if keyword:
                    category_keywords[category.strip()]\
                        .append(keyword.strip().lower())
    return category_keywords


# Match product name to category
def match_category(product_name, category_keywords):
    s = re.sub(r'[^\w\s]', '', product_name.lower())
    name_tokens = set(s.split())
    for main_cat, keywords in category_keywords.items():
        for keyword in keywords:
            key = re.sub(r'[^\w\s]', '', keyword.lower())
            keyword_tokens = set(key.split())
            if keyword_tokens.issubset(name_tokens):
                return main_cat
    return "Uncategorized"


# Fetch Uncategorised products from Odoo
def fetch_products():
    category_ids = models.execute_kw(
        DB_NAME, uid, PASSWORD,
        'product.category', 'search',
        [[['name', '=', 'Uncategorized']]])

    if not category_ids:
        return []

    products_ids = models.execute_kw(
        DB_NAME, uid, PASSWORD,
        'product.template', 'search',
        [[['categ_id', '=', category_ids[0]]]])

    if not products_ids:
        return []

    products = models.execute_kw(
        DB_NAME, uid, PASSWORD,
        'product.template', 'read',
        [products_ids],
        {'fields': ['id', 'name', 'categ_id']})

    return products


# Main categorization
def create_find_categories():
    category_keywords = main_categories('main_categories.csv')
    products = fetch_products()
    updated_count = 0

    for product in products:
        name = product['name']
        categ = product.get('categ_id')
        current_cat = categ[0] if isinstance(categ, list) and categ else None
        matched_category = match_category(name, category_keywords)
        if matched_category is None or matched_category.strip() == "":
            logging.warning(f"Empty or invalid matched category for:"
                            f"product '{name}'. Skipping.")
            continue

        if matched_category == "Uncategorized":
            logging.info(f"No match found for: {name}")
            continue
        else:
            # Check if product category already exists
            category_ids = models.execute_kw(
                DB_NAME, uid, PASSWORD,
                'product.category', 'search',
                [[["name", "=", matched_category]]])
            if not category_ids:
                # Create it if not found
                category_id = models.execute_kw(
                    DB_NAME, uid, PASSWORD,
                    'product.category', 'create',
                    [{"name": matched_category}])
            else:
                category_id = category_ids[0]
            # Create or fetch website category
            website_cat_ids = models.execute_kw(
                DB_NAME,
                uid,
                PASSWORD,
                'product.public.category',
                'search',
                [[['name', '=', matched_category]]])

            if not website_cat_ids:
                website_cat_id = models.execute_kw(
                    DB_NAME, uid, PASSWORD,
                    'product.public.category',
                    'create', [{'name': matched_category}])
            else:
                website_cat_id = website_cat_ids[0]

            # Create or fetch POS category
            pos_cat_ids = models.execute_kw(
                DB_NAME, uid, PASSWORD,
                'pos.category', 'search',
                [[['name', '=', matched_category]]])

            if not pos_cat_ids:
                pos_cat_id = models.execute_kw(
                    DB_NAME, uid, PASSWORD,
                    'pos.category', 'create',
                    [{'name': matched_category}])
            else:
                pos_cat_id = pos_cat_ids[0]

        # Only update if different
        update_vals = {}
        if current_cat != category_id:
            update_vals['categ_id'] = category_id

        update_vals['public_categ_ids'] = [(6, 0, [website_cat_id])]
        update_vals['pos_categ_ids'] = [(6, 0, [pos_cat_id])]
        models.execute_kw(
            DB_NAME, uid, PASSWORD,
            'product.template', 'write',
            [[product['id']], update_vals])
        updated_count += 1
        if updated_count % 100 == 0 and updated_count != 0:
            logging.info(f"Updated {updated_count} products")

    logging.info(f"Total products updated: {updated_count}")


if __name__ == '__main__':
    create_find_categories()
