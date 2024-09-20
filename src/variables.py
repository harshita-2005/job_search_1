import json
from pkgutil import get_data

CONFIG = json.loads(get_data(
    'config', 'config.json').decode())