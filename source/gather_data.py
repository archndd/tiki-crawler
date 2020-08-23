#!/bin/python3 
from bs4 import BeautifulSoup
import requests, json, logging, os, re
import urllib.request
from utils import CURRENTDATE, ABS_PATH


class PriceBook:
    tiki_api_url_template = "https://tiki.vn/api/v2/products/{}"
    tiki_url_template = "https://tiki.vn/"
    fields = ["name", "url_path"]
    price_fields = ["price", "list_price", "discount", "discount_rate"]
    category_fields = ["id", "name"]
    author_fields = ["id", "name"]
    brand_fields = ["id", "name"]

    def __init__(self):
        self.json_filename = os.path.join(ABS_PATH, "data.json")
        self.logger = logging.getLogger("gather_data.PriceBook")

        with open(self.json_filename, 'r') as json_file:
            try:
                self.data = json.load(json_file)
            except json.decoder.JSONDecodeError:
                self.data = {}

    def insert_product(self, product_url, force=False, log=""):
        product_id = re.search(r"p(\d+)\.html", product_url).group(1)
        if product_id not in self.data or force:
            response = requests.get(self.tiki_api_url_template.format(product_id))
            if response.status_code == 200:
                product_data = json.loads(response.text)
                if product_data["inventory_status"] == "available":
                    tmp = {}
                    for f in self.fields:
                        tmp[f] = product_data.get(f, '')

                    tmp["categories"] = {}
                    for cf in self.category_fields:
                        tmp["categories"][cf] = product_data["categories"].get(cf, '')
                    if tmp["categories"]["id"] != '':
                        tmp["categories"]["id"] = int(tmp["categories"]["id"])

                    # TODO better author brand name
                    if "authors" in product_data:
                        tmp["author"] = {}
                        for af in self.author_fields:
                            tmp["author"][af] = product_data["authors"][0].get(af, "")
                        if tmp["author"]["id"] != '':
                            tmp["author"]["id"] = int(tmp["author"]["id"])
                    elif "brand" in product_data:
                        tmp["brand"] = {}
                        for bf in self.author_fields:
                            tmp["brand"][bf] = product_data["brand"][0].get(bf, "")
                        if tmp["brand"]["id"] != '':
                            tmp["brand"]["id"] = int(tmp["brand"]["id"])
                    # elif tmp["categoties"]["id"] == 

                    tmp["price"] = {}
                    if CURRENTDATE not in tmp["price"]:
                        tmp["price"][CURRENTDATE] = {}
                        for cf in self.price_fields:
                            tmp["price"][CURRENTDATE][cf] = int(product_data.get(cf, 0))


                    if "thumbnail_url" in product_data:
                        jpg_path = os.path.join(ABS_PATH, "thumbnails", "{}.jpg".format(product_id))
                        urllib.request.urlretrieve(product_data["thumbnail_url"], jpg_path)
                        tmp["thumbnail"] = jpg_path

                    self.data[product_id] = tmp
                    return True, product_id
                else:
                    self.logger.warning("{} not available".format(product_data["name"]))
            else:
                self.logger.warning("Getting {} failed".format(product_url))
        return False, None

    def insert_from_file(self, file_path):
        with open(file_path) as file:
            for line in file.read().split('\n'):
                if line:
                    # TODO
                    self.insert_product(line, True)

    def delete_product(self, product_id, log=""):
        temp_prod = self.data[product_id]
        self.logger.warning("DELETE: {url} - {title}\n{log}".format(url=temp_prod["url_path"], title=temp_prod["name"], log=log))
        del self.data[product_id]

    def update(self):
        for product_id in list(self.data.keys()):
            response = requests.get(self.tiki_api_url_template.format(product_id))
            if response.status_code == 200:
                product_data = json.loads(response.text)
                if product_data["inventory_status"] != "available":
                    del self.data[product_id]
                else:
                    tmp = self.data[product_id]
                    if CURRENTDATE not in tmp["price"]:
                        tmp["price"][CURRENTDATE] = {}
                        for f in self.price_fields:
                            tmp["price"][CURRENTDATE][f] = product_data.get(f, '')
            else:
                self.logger.warning("Getting {} failed".format(self.data[product_id]["url_path"]))
        self.dump_to_json()

    def dump_to_json(self):
        self.logger.info("Dumping to json")
        with open(self.json_filename, 'w') as json_file:
            json.dump(self.data, json_file, indent=4)

    def print_data(self):
        print(json.dumps(self.data, indent=4))

    def __getitem__(self, product_id):
        return self.data[product_id]


if __name__ == "__main__": 
    logger = logging.getLogger('gather_data')
    logger.setLevel(logging.DEBUG)
    # create a file handler
    handler = logging.FileHandler(os.path.join(ABS_PATH, 'app.log'))
    handler.setLevel(logging.DEBUG)
    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(handler)

    price_book = PriceBook()
    # price_book.insert_from_file(os.path.join(ABS_PATH, "watching_list"))
    price_book.update()
    price_book.dump_to_json()

