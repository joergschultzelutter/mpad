#
# Multi-Purpose APRS Daemon: CWOP data retrieval
# Author: Joerg Schultze-Lutter, 2020
# Reimplements portions of Martin Nile's WXBOT code (KI6WJP)
#
# Purpose: Get nearest CWOP data report
#

import requests
import re
from bs4 import BeautifulSoup


def get_cwop_findu(cwop_id: str, units: str = 'metric'):
    """Convert latitude / longitude coordinates to UTM (Universal Transverse Mercator) coordinates

    Parameters
    ==========
    cwop_id : 'str'
        CWOP ID whose data is to be retrieved
    units : 'str'
        Unit of measure. Can either be 'metric' or 'imperial'

    Returns
    =======
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
    cwop_id = cwop_id.upper()
    units = units.lower()
    assert units in ['imperial', 'metric']

    success: bool = False

    time = temp = wind_direction = wind_speed = wind_gust = rain_1h = rain_24h = rain_mn = humidity = air_pressure = None

    resp = requests.get(f"http://www.findu.com/cgi-bin/wx.cgi?call={cwop_id}&last=1&units={units}")
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, features="html.parser")
        matches = re.search(r"\b(Sorry, no weather reports found)\b", soup.get_text(), re.IGNORECASE)
        if not matches:
            # Tabelle parsen; Regex funktioniert nicht immer sauber
            table = soup.find("table")
            output_rows = []
            for table_row in table.findAll('tr'):
                columns = table_row.findAll('td')
                output_row = []
                for column in columns:
                    output_row.append(column.text.strip())
                output_rows.append(output_row)
            if len(output_rows) > 0:
                if len(output_rows[0]) >= 10:
                    time = output_rows[1][0]
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
    return cwop_id, time, \
           temp, \
           wind_direction, \
           wind_speed, \
           wind_gust, \
           rain_1h, \
           rain_24h, \
           rain_mn, \
           humidity, \
           air_pressure, \
           success


def get_nearest_cwop_findu(latitude: float, longitude: float, units: str = 'metric'):
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

    cwop_id = time = temp = wind_direction = wind_speed = wind_gust = rain_1h = rain_24h = rain_mn = humidity = air_pressure = None

    resp = requests.get(f"http://www.findu.com/cgi-bin/wxnear.cgi?lat={latitude}&lon={longitude}&noold=1&limits=1")
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, features="html.parser")
        matches = re.search(r"\b(sorry)\b", soup.get_text(), re.IGNORECASE)
        if not matches:
            # Tabelle parsen; Regex funktioniert nicht immer sauber
            table = soup.find("table")
            output_rows = []
            for table_row in table.findAll('tr'):
                columns = table_row.findAll('td')
                output_row = []
                for column in columns:
                    output_row.append(column.text.strip())
                output_rows.append(output_row)
            if (len(output_rows) > 0):
                if (len(output_rows[0]) >= 13):
                    # erneuter Call notwendig, da wxnear keine Units unterstützt
                    return get_cwop_findu(output_rows[1][0], units)

    return cwop_id, time, temp, wind_direction, wind_speed, wind_gust, rain_1h, rain_24h, rain_mn, humidity, air_pressure, success


if __name__ == '__main__':
    print(get_nearest_cwop_findu(51.838720, 08.326819, "metric"))
    print(get_cwop_findu("AT166", "metric"))
