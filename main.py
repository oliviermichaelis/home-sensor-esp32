import wifimgr
import network
import utime
import ntptime
import time
import ujson
import bme280
import urequests

from machine import Pin, I2C


class BadRequestException(Exception):
    pass


def pad_left(s : str, width) -> str:
    s = str(s)
    if len(s) < width:
        return ("0" * (width - len(s))) + s
    else:
        return s


def get_timestamp() -> str:
    localtime = utime.localtime()
    timestamp = pad_left(localtime[0], 4) + pad_left(localtime[1], 2) + pad_left(localtime[2], 2)
    timestamp += pad_left(localtime[3], 2) + pad_left(localtime[4], 2) + pad_left(localtime[5], 2)
    return timestamp


def read_sensor() -> str:
    # TODO add Station
    values = {
        "Timestamp": get_timestamp(),
        "Temperature": bme.temperature,
        "Humidity": bme.humidity,
        "Pressure": bme.pressure,
    }
    return ujson.dumps(values)


def transmit_data(json_values: str):
    if not isinstance(json_values, str):
        return

    url = "https://apiserver.lab.oliviermichaelis.dev/measurements/climate"

    headers = {
        "Content-Type": "application/json"
    }

    response = None
    try:
        response = urequests.post(url=url, json=json_values, headers=headers)
        if response.status_code != 200:
            raise BadRequestException("Error: status code: " + str(response.status_code) + ", expected: 200")
        print("successful request: ", json_values)
        # print(response)
        response.close()
    except ValueError as err:
        print("Error: ", err)
    except OSError as err:
        print("Error: ", err)
    except NotImplementedError as err:
        print("Error: ", err)
    except BadRequestException as err:
        response.close()
        print("Error: ", err)


wlan = wifimgr.get_connection()
if wlan is None:
    print("Could not initialize the network connection.")
    while True:
        pass


# wlan is a working network.WLAN(STA_IF) instance.
# deactivate AP after it has been used to configure the network connection
ap = network.WLAN(network.AP_IF)
# TODO deactivate AP

# set time to UTC time
ntptime.settime()
last_ntp_sync = utime.time()

# Initialize I2C pins
i2c = I2C(scl=Pin(14), sda=Pin(13), freq=10000)
bme = bme280.BME280(i2c=i2c)

while True:
    # dirty hack to make sure the local clock stays in sync with the ntp server pool.ntp.org.
    # Resync every 10min with the upstream ntp server in order to mitigate time shift.
    # Resetting the time is no problem, since time shift should never be larger than delay of sensor readings.
    if utime.time() - last_ntp_sync > 60 * 10:
        ntptime.settime()
        last_ntp_sync = utime.time()
        print("Local time has been synced with pool.ntp.org")
    transmit_data(read_sensor())
    time.sleep(10)
