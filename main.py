import wifimgr
import network
import utime
import ntptime
import time
import ujson
import bme280
import urequests
import config
import sys
import machine

from machine import Pin, I2C

DEBUGGING = False
LOGGING = True


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


def read_sensor(sensor, station: str) -> str:
    # TODO add Station in dynamic way
    values = {
        "timestamp": get_timestamp(),
        "station": station,
        "temperature": float(sensor.temperature),
        "humidity": float(sensor.humidity),
        "pressure": float(sensor.pressure),
    }
    return ujson.dumps(values)


def transmit_data(json_values: str):
    if not isinstance(json_values, str):
        return

    if DEBUGGING:
        url = "http://192.168.1.20:8080/measurements/climate"
    else:
        url = "https://apiserver.lab.oliviermichaelis.dev/measurements/climate"

    response = None
    try:
        response = urequests.post(url=url, data=json_values)
        if response.status_code != 200:
            raise BadRequestException("Error: status code: " + str(response.status_code) + ", expected: 200")
        print("successful request: ", json_values)
        response.close()
    except ValueError as err:
        print("Error: ", err)
    except OSError as err:
        print("Error: ", err)
    except NotImplementedError as err:
        print("Error: ", err)
    except BadRequestException as err:
        print(response.text)
        response.close()
        print(err)


def main():
    wlan = wifimgr.get_connection()
    if wlan is None:
        print("Could not initialize the network connection.")
        while True:
            utime.sleep(1)
            pass

    station = config.get_setting("station")

    # wlan is a working network.WLAN(STA_IF) instance.
    # deactivate AP after it has been used to configure the network connection
    ap = network.WLAN(network.AP_IF)
    ap.active(False)

    # set time to UTC time
    ntptime.settime()
    last_ntp_sync = utime.time()

    # Initialize I2C pins
    i2c = I2C(scl=Pin(22), sda=Pin(21), freq=10000)
    bme = bme280.BME280(i2c=i2c)

    while True:
        # dirty hack to make sure the local clock stays in sync with the ntp server pool.ntp.org.
        # Resync every 10min with the upstream ntp server in order to mitigate time shift.
        # Resetting the time is no problem, since time shift should never be larger than delay of sensor readings.
        if abs(utime.time() - last_ntp_sync) > 60 * 10:
            ntptime.settime()
            last_ntp_sync = utime.time()
            print("Local time has been synced with pool.ntp.org")
        transmit_data(read_sensor(bme, station))
        time.sleep(60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise
    except Exception as err:
        if LOGGING:
            with open("syslog.txt", "a") as f:
                f.write(str(utime.localtime()) + str(err) + '\n')
        # In case of an unexpected error, reset the controller
        time.sleep(10)
        machine.reset()
