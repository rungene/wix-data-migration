# Wix to Custom Solution Data Migration

This project provides a solution for migrating product data from a Wix website to a custom system. It includes a Python script to fetch product data from Wix using exposed HTTP functions and a Node.js script to convert internal Wix media URLs to absolute URLs using the Wix SDK.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Setup Instructions](#setup-instructions)
3. [Usage](#usage)
4. [How It Works](#how-it-works)
5. [Known Issues](#known-issues)
6. [Contributing](#contributing)
7. [License](#license)

---

## Prerequisites

- Python 3.8
- Node.js 23
- `requests` Python package
- A Wix site with Velo (Wix's development platform) enabled and an exposed [HTTP function](https://dev.wix.com/docs/develop-websites/articles/coding-with-velo/integrations/exposing-services/write-an-http-function) for fetching product data

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/wix-data-migration.git
   cd wix-data-migration
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure Node.js is installed:**
   ```bash
   node -v
   ```
   If Node.js is not installed, download and install it from [Node.js official site](https://nodejs.org/).

4. **Ensure the Wix SDK is installed in your Node.js project:**
   ```bash
   npm install @wix/sdk
   ```

## Usage

### Step 1: Fetch Data from Wix

1. Open the `fetch_wix_data.py` script.
2. Set the `API_URL` variable to point to your Wix site's exposed HTTP function(You can use env file).
   ```python
   API_URL = "https://your-wix-site/_functions/products"
   ```
3. Run the Python script to fetch the data and save it to a CSV file:
   ```bash
   python fetch_wix_data.py
   ```
   This script will create a `products.csv` file with product data.

### Step 2: Convert Media URLs

1. Open the `convertUrl.js` script.
2. Ensure it correctly reads input from `stdin` and uses the Wix SDK to generate absolute URLs.
3. Run the Python script that processes the CSV file and calls the Node.js script for URL conversion:
   ```bash
   python absolute_urls.py
   ```

### Step 3: Import Data to your custom solution

1. Once the `products_with_absolute_urls.csv` file is generated, use Odoo's import feature to upload the product data.

## How It Works

1. **Data Fetching**: The Python script `fetch_wix_data.py` sends a GET request to the exposed Wix HTTP function and retrieves product data in JSON format.
2. **Saving to CSV**: The data is saved in a CSV file with fields required by your custom solution.
3. **Media URL Conversion**: The Python script `process_media_urls.py` reads the CSV file, extracts media URLs, and calls the Node.js script `convertUrl.js` using `subprocess`. The Node.js script uses the Wix SDK to convert internal URLs to absolute URLs.

## Known Issues

- Ensure the Wix HTTP function returns data in the expected format.
- Large datasets may cause performance issues during URL conversion.
- The Node.js script expects properly formatted input; invalid JSON input will cause errors.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-name`).
3. Commit your changes (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature-name`).
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Happy migrating! If you encounter any issues, feel free to open an issue on GitHub.

