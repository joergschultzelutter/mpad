#
# Multi-Purpose APRS Daemon: CWOP data retrieval
# Author: Joerg Schultze-Lutter, 2020
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import requests
import re
from bs4 import BeautifulSoup
import datetime
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def get_cwop_findu(cwop_id: str, units: str = "metric"):
    """Convert latitude / longitude coordinates to UTM (Universal Transverse Mercator) coordinates

    Parameters
    ==========
    cwop_id : 'str'
        CWOP ID whose data is to be retrieved
    units : 'str'
        Unit of measure. Can either be 'metric' or 'imperial'

    Returns
    =======

    Returns a dict, consisting of the following fields:

    time : 'int'
        Unix timestamp
    temp: 'str'
        temperature in Celsius or Fahrenheit (dependent on 'units' parameter) ('None' if not found, see 'success' parameter)
    wind_direction: 'str'
        Wind direction (degrees) ('None' if not found, see 'success' parameter)
    wind_speed: 'str'
        Wind speed in km/h or mph (dependent on 'units' parameter) ('None' if not found, see 'success' parameter)
    wind_gust: 'str'
        Wind Gust in km/h or mph (dependent on 'units' parameter) ('None' if not found, see 'success' parameter)
    rain_1h: 'str'
        Rain in cm or inch within the last 1h (dependent on 'units' parameter) ('None' if not found, see 'success' parameter)
    rain_24h: 'str'
        Rain in cm or inch within the last 24h (dependent on 'units' parameter) ('None' if not found, see 'success' parameter)
    rain_mn: 'str'
        Rain in cm or inch minimal (dependent on 'units' parameter) ('None' if not found, see 'success' parameter)
    humidity: 'str'
        humidity in percent  ('None' if not found, see 'success' parameter)
    air_pressure: 'str'
        air pressure in mBar  ('None' if not found, see 'success' parameter)

    plus a separate parameter:

    success: 'bool'
        True if operation was successful
    """
    cwop_id = cwop_id.upper()
    units = units.lower()
    assert units in ["imperial", "metric"]

    success: bool = False

    time = temp = wind_direction = wind_speed = None
    wind_gust = rain_1h = rain_24h = rain_mn = None
    humidity = air_pressure = None
    my_timestamp = datetime.datetime.utcnow()

    humidity_uom = "%"
    air_pressure_uom = "mb"

    temp_uom = "C"
    speedgust_uom = "km/h"
    rain_uom = "cm"
    air_pressure_uom = "mb"
    if units == "imperial":
        temp_uom = "F"
        speedgust_uom = "mph"
        rain_uom = "in"

    resp = requests.get(
        f"http://www.findu.com/cgi-bin/wx.cgi?call={cwop_id}&last=1&units={units}"
    )
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, features="html.parser")
        matches = re.search(
            r"\b(Sorry, no weather reports found)\b", soup.get_text(), re.IGNORECASE
        )
        if not matches:
            # Tabelle parsen; Regex funktioniert nicht immer sauber
            table = soup.find("table")
            output_rows = []
            for table_row in table.findAll("tr"):
                columns = table_row.findAll("td")
                output_row = []
                for column in columns:
                    output_row.append(column.text.strip())
                output_rows.append(output_row)
            if len(output_rows) > 0:
                if len(output_rows[0]) >= 10:
                    time = output_rows[1][0]
                    time_year = int(time[0:4])
                    time_month = int(time[4:6])
                    time_day = int(time[6:8])
                    time_hh = int(time[8:10])
                    time_mm = int(time[10:12])
                    time_ss = int(time[12:14])
                    my_timestamp = datetime.datetime(
                        year=time_year,
                        month=time_month,
                        day=time_day,
                        hour=time_hh,
                        minute=time_mm,
                        second=time_ss,
                    )
                    temp = output_rows[1][1]
                    wind_direction = output_rows[1][2]
                    wind_speed = output_rows[1][3]
                    wind_gust = output_rows[1][4]
                    rain_1h = output_rows[1][5]
                    rain_24h = output_rows[1][6]
                    rain_mn = output_rows[1][7]
                    humidity = output_rows[1][8]
                    air_pressure = output_rows[1][9]
                    success = True
    cwop_response = {
        "cwop_id": cwop_id,
        "time": my_timestamp,
        "temp": temp,
        "temp_uom": temp_uom,
        "wind_direction": wind_direction,
        "wind_speed": wind_speed,
        "wind_gust": wind_gust,
        "speedgust_uom": speedgust_uom,
        "rain_1h": rain_1h,
        "rain_24h": rain_24h,
        "rain_mn": rain_mn,
        "rain_uom": rain_uom,
        "humidity": humidity,
        "humidity_uom": humidity_uom,
        "air_pressure": air_pressure,
        "air_pressure_uom": air_pressure_uom,
    }
    return success, cwop_response


def get_nearest_cwop_findu(latitude: float, longitude: float, units: str = "metric"):
    """Get nearest CWOP for a given set of coordinates

    Parameters
    ==========
    latitude : 'float'
        Latitude
    latitude : 'float'
        Longitude
    units : 'str'
        Unit of measure. Can either be 'metric' or 'imperial'

    Returns
    =======
    cwop_id : 'str'
        CWOP ID whose data is to be retrieved ('None' if not found, see 'success' parameter)
    time : 'str'
        time in YYYYMMDDHHMMSS ('None' if not found, see 'success' parameter)
    temp: 'str'
        temperature in Celsius or Fahrenheit (dependent on 'units' parameter) ('None' if not found, see 'success' parameter)
    wind_direction: 'str'
        Wind direction (degrees) ('None' if not found, see 'success' parameter)
    wind_speed: 'str'
        Wind speed in km/h or mph (dependent on 'units' parameter) ('None' if not found, see 'success' parameter)
    wind_gust: 'str'
        Wind Gust in km/h or mph (dependent on 'units' parameter) ('None' if not found, see 'success' parameter)
    rain_1h: 'str'
        Rain in cm or inch within the last 1h (dependent on 'units' parameter) ('None' if not found, see 'success' parameter)
    rain_24h: 'str'
        Rain in cm or inch within the last 24h (dependent on 'units' parameter) ('None' if not found, see 'success' parameter)
    rain_mn: 'str'
        Rain in cm or inch minimal (dependent on 'units' parameter) ('None' if not found, see 'success' parameter)
    humidity: 'str'
        humidity in percent  ('None' if not found, see 'success' parameter)
    air_pressure: 'str'
        air pressure in mBar  ('None' if not found, see 'success' parameter)
    success: 'bool'
        True if operation was successful
    """

    success = False

    time = temp = wind_direction = wind_speed = None
    wind_gust = rain_1h = rain_24h = rain_mn = None
    humidity = air_pressure = cwop_id = None
    my_timestamp = datetime.datetime.utcnow()

    humidity_uom = "%"
    air_pressure_uom = "mb"

    temp_uom = "C"
    speedgust_uom = "km/h"
    rain_uom = "cm"
    if units == "imperial":
        temp_uom = "F"
        speedgust_uom = "mph"
        rain_uom = "in"

    resp = requests.get(
        f"http://www.findu.com/cgi-bin/wxnear.cgi?lat={latitude}&lon={longitude}&noold=1&limits=1"
    )
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, features="html.parser")
        matches = re.search(r"\b(sorry)\b", soup.get_text(), re.IGNORECASE)
        if not matches:
            # Parse table
            table = soup.find("table")
            output_rows = []
            for table_row in table.findAll("tr"):
                columns = table_row.findAll("td")
                output_row = []
                for column in columns:
                    output_row.append(column.text.strip())
                output_rows.append(output_row)
            if len(output_rows) > 0:
                if len(output_rows[0]) >= 13:
                    # call findu again as the previous URL does not support units :-(
                    return get_cwop_findu(output_rows[1][0], units)
    # This code will only be triggered in the event of a failure
    cwop_response = {
        "cwop_id": cwop_id,
        "time": my_timestamp,
        "temp": temp,
        "temp_uom": temp_uom,
        "wind_direction": wind_direction,
        "wind_speed": wind_speed,
        "wind_gust": wind_gust,
        "speedgust_uom": speedgust_uom,
        "rain_1h": rain_1h,
        "rain_24h": rain_24h,
        "rain_mn": rain_mn,
        "rain_uom": rain_uom,
        "humidity": humidity,
        "humidity_uom": humidity_uom,
        "air_pressure": air_pressure,
        "air_pressure_uom": air_pressure_uom,
    }
    return success, cwop_response


if __name__ == "__main__":
    logger.info(get_nearest_cwop_findu(51.838720, 08.326819, "imperial"))
    logger.info(get_cwop_findu("AT166", "metric"))
