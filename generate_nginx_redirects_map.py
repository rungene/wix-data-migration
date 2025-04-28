import csv
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    filename="generate_nginx_redirects.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()
DOMAIN = os.getenv('DOMAIN')


def generate_nginx_redirects_map(csv_file, output_file, domain):
    counter = 0
    with open(csv_file, mode="r", encoding="utf-8") as infile, \
         open(output_file, mode="w", encoding="utf-8") as outfile:

        reader = csv.DictReader(infile)

        outfile.write("# This 'map' defines redirects based on request URI\n")
        outfile.write("map $request_uri $redirect_target {\n")
        outfile.write("    default \"\";\n")
        for row in reader:
            old_url = row["old_url"].strip()
            new_url = row["new_url"].strip()

            if new_url != "NOT FOUND":
                outfile.write(f'    {old_url} {domain}{new_url};\n')
                counter += 1
                if counter % 100 == 0 and counter != 0:
                    logging.info(f'{counter} redirects written so far')

        outfile.write('}\n')

    logging.info(f"{Counter} redirects saved to {output_file}")


if __name__ == "__main__":
    generate_nginx_redirects_map("redirect_mapping.csv",
                                 "nginx_redirects.conf", DOMAIN)
