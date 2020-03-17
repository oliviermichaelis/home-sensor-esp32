import ujson

CONFIG_FILE = "config.json"

configuration = {}


def _read_config():
    global configuration
    try:
        with open(CONFIG_FILE) as f:
            configuration = ujson.load(f)
    except OSError as err:
        print(err)

    if not bool(configuration):
        raise OSError(CONFIG_FILE + " is missing")
    print(configuration)


def get_setting(key: str):
    if not bool(configuration):
        _read_config()
    return configuration.get(key)
