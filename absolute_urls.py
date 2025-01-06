import csv
import subprocess
import json
import ast

# File names
input_file = 'products.csv'
output_file = 'products_with_absolute_urls.csv'

# Call the JavaScript script for URL conversion
def convert_media_url(wix_internal_url):
    """
    Calls JavaScript SDK to convert a Wix internal URL to an absolute URL.
    """
    if not wix_internal_url:
        return ''

    try:
        # Call Node.js script
        result = subprocess.run(
            ['node', "convertUrl.js"],
            input=wix_internal_url.encode('utf-8'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return result.stdout.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        print(f'Error in URL conversion: {e.stderr.decode("utf-8")}')
        return wix_internal_url


# Process the media items field
def process_media_items(media_items):
    """
    Process the media items string and return absolute URLS.
    """
    if not media_items:
        return ""

    try:
        # Use ast.literal_eval to convert the string into Python list
        items = ast.literal_eval(media_items)
        # Parse JSON string
       # items = json.loads(items)
        if not isinstance(items, list):
            print('Unexpected media items format:', media_items)
            return ""
        # Extract and convert the src of each media item
        absolute_urls = [convert_media_url(item.get('src', '')) for item in items]
        return ','.join(absolute_urls)
    except (ValueError, SyntaxError) as e:
        print(f'Error decoding media items JSON: {e}')
        return ""

# Process CSV
def process_csv(input_file, output_file):
    """
    Process the input csv file, write output csv file with the same headers
    but change the media items to absolute urls
    """
    with open(input_file, mode='r', encoding='utf-8') as infile, \
        open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        headers = reader.fieldnames

        # Ensure the output file includes the same headers 
        writer = csv.DictWriter(outfile, fieldnames=headers)
        writer.writeheader()

        for row in reader:
            # Process and update the media items columns
            row['media items'] = process_media_items(row.get('media items', ''))
            writer.writerow(row)

    print(f'Processed data saved to {output_file}')

if __name__ == '__main__':
    process_csv(input_file, output_file)
