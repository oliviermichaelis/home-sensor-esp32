import wifimgr
import network
import ujson
import socket

# ap_ssid = "ESP-AP"
# ap_password = "wifimanager"
# ap_authmode = 3     # WPA2
# ap_interface = network.WLAN(network.AP_IF)

CONFIG_FILE = "config.json"

# server_socket = None
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


def get_setting(key : str):
    if not bool(configuration):
        _read_config()
    return configuration.get(key)

# def start_ap(port=80):
#     ap_interface.active(True)
#     global server_socket
#
#     addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
#     wifimgr.stop()
#
#     ap_interface.config(essid=ap_ssid, password=ap_password, authmode=ap_authmode)
#
#     server_socket = socket.socket()
#     server_socket.bind(addr)
#     server_socket.listen(1)
#
#     print('Connect to WiFi ssid ' + ap_ssid + ', default password: ' + ap_password)
#     print('and access the ESP via your favorite web browser at 192.168.4.1.')
#     print('Listening on:', addr)
#
#
