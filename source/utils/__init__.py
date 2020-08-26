import datetime
import json
import os

CURRENTDATE = datetime.date.today().strftime("%d-%m-%Y")
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")) as f:
    config = json.load(f)
    ABS_PATH =config["abs_path"]
