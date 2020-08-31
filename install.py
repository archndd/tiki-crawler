import os
import platform
import json

if platform.system() == 'Windows':
    path = os.environ["PROGRAMDATA"]
elif platform.system() == "Linux":
    path = os.path.join(os.environ["HOME"], '.local', 'share')

path = os.path.join(path, 'tiki-crawler')
os.makedirs(path)
os.makedirs(os.path.join(path, 'thumbnails'))

config = {"abs_path": path}
with open('config.json', 'w') as f:
    json.dump(config, f, indent=4)
