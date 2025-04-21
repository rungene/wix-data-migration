import csv
import xmlrpc.client
import base64
import os
import logging
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('ODOO_URL')
db = os.getenv('DB_NAME')
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
# Configure logging
logging.basicConfig(
    filename="upload_images_to_odoo.log",  # Save logs to a file
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))

uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

# Find the view by its name

view_name = 'web.brand_promotion_message'  # The view name to reactivate

view_id = models.execute_kw(db, uid, password, 'ir.ui.view', 'search',
                            [[('key', '=', view_name),
                              ('active', '=', False)]])

if view_id:

    # Reactivate the view

    models.execute_kw(db, uid, password, 'ir.ui.view',
                      'write', [view_id, {'active': True}])

    print(f"View {view_name} reactivated successfully.")

else:
    print(f"View {view_name} not found or already active.")
