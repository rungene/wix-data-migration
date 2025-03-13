import os
import requests
import csv
import logging
from PIL import Image
from io import BytesIO
import re

# Configure logging
logging.basicConfig(
    filename="image_download.log",  # Save logs to a file
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def download_and_compress_images(csv_file, output_folder, max_width=800,
                                 quality=85):
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    updated_rows = []

    # Open the CSV file
    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError("CSV file appears to be empty or"
                             "has an invalid format.")
        # Add new column
        fieldnames = reader.fieldnames + ['sanitized_name']

        # Loop through each row in the CSV
        for row in reader:
            product_name = row["name"].replace(" ", "_").lower()
            product_name = sanitize_filename(product_name)
            # Add sanitised name to the row
            row['sanitized_name'] = (
                product_name + '.webp' if not
                product_name.endswith('.webp') else product_name)
            updated_rows.append(row)

            media_items = row.get("media items", "")

            # Split the media items column into individual URLs
            media_urls = media_items.split(",") if media_items else []

            for idx, url in enumerate(media_urls):
                try:
                    url = url.strip()  # Remove any extra spaces
                    if url and url.startswith("http"):
                        response = requests.get(url)

                        if response.status_code == 200:
                            # Create a filename using the product name
                            # and index
                            filename = f"{product_name}_{idx + 1}.webp"
                            filepath = os.path.join(output_folder, filename)

                            # Ensure unique filename
                            counter = 1
                            while os.path.exists(filepath):
                                filename = (
                                    f"{product_name}_{idx + 1}_"
                                    f"{counter}.webp"
                                )
                                filepath = os.path.join(
                                            output_folder,
                                            filename
                                )
                                counter += 1

                            # Open the image using Pillow
                            image = Image.open(BytesIO(response.content))

                            # Resize image if it exceeds max width
                            if image.width > max_width:
                                aspect_ratio = image.height / image.width
                                new_height = int(max_width * aspect_ratio)
                                image = image.resize((max_width, new_height),
                                                     Image.Resampling.LANCZOS)

                            # Save the image with compression
                            image.save(filepath, format="WEBP",
                                       quality=quality)
                            logging.info(f"Downloaded and compressed: "
                                         f"{filename}")
                        else:
                            logging.warning(f"Failed to download {url}: "
                                            f"HTTP {response.status_code}")
                except Exception as e:
                    logging.error(f"Error processing image from {url}: {e}")

    with open(csv_file, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)


if __name__ == "__main__":
    # Specify the input CSV file and output folder for images
    input_csv = "products_with_absolute_urls.csv"
    output_folder = "compressed_images"

    # Call the function to download and compress images
    download_and_compress_images(input_csv, output_folder)
