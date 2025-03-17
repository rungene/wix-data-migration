import os
import shutil
import csv
import logging

# Configure logging
logging.basicConfig(
    filename="move_images.log",  # Save logs to a file
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def move_images(csv_file, source_folder, destination_folder):
    """
    Reads a CSV file, gets filenames from the 'sanitized_name' column,
    moves matching images from the source folder to the destination folder.
    """
    # Ensure destination folder exists
    os.makedirs(destination_folder, exist_ok=True)

    img_moved = 0
    try:
        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)  # Convert to list to check if empty

            if not rows:
                logging.warning(f"No data found in {csv_file}.")
                return

            for row in rows:
                filename = row.get("sanitized_name")  # Get filename from CSV
                if filename:
                    source_path = os.path.join(source_folder, filename)
                    destination_path = os.path.join(destination_folder,
                                                    filename)

                    if os.path.exists(source_path):
                        try:
                            shutil.move(source_path, destination_path)
                            img_moved += 1
                            if img_moved % 100 == 0:
                                logging.info(f"Images Moved: {img_moved}")
                        except Exception as e:
                            logging.error(f"Error moving {filename}: {e}")
                    else:
                        logging.warning(f"File not found: {filename}")

        logging.info(f"{img_moved} images moved to {destination_folder}")

    except Exception as e:
        logging.critical(f"Script failed: {e}")


if __name__ == "__main__":
    # Example usage
    csv_file = "products_with_absolute_urls.csv"
    source_folder = "compressed_images"
    destination_folder = "single_images"

    move_images(csv_file, source_folder, destination_folder)
