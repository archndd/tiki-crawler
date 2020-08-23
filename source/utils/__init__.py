import datetime
import json

CURRENTDATE = datetime.date.today().strftime("%d-%m-%Y")
with open('/home/duy/tiki_price/utils/config.json') as f:
    config = json.load(f)
    ABS_PATH =config["abs_path"]
