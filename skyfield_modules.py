#
# Multi-Purpose APRS Daemon: Skyfield Modules
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: Find satellite positions and/or sun/moon rise/set
#

import datetime
import re
import requests
from skyfield import api, almanac
from skyfield.api import EarthSatellite

tle_data = {}   # create empty dict
tle_data_last_download = datetime.datetime.now()
import logging


def refresh_tle_file(tle_filename: str = "amateur.tle"):
    """
    Download the amateur radio satellite TLE data
    and save it to a local file.

    Parameters
    ==========
    tle_filename : 'str'
        This local file will hold the content
        from http://www.celestrak.com/NORAD/elements/amateur.txt
        Default is "amateur.tle"

    Returns
    =======
    success: 'bool'
        True if operation was successful
    """

    # This is the fixed name of the file that we are going to download
    tle_data_file_url = "http://www.celestrak.com/NORAD/elements/amateur.txt"
    global tle_data_last_download
    success: bool = False

    # try to get the file
    try:
        r = requests.get(tle_data_file_url)
    except:
        logging.debug(f"Cannot download TLE data from {tle_data_file_url}")
        r = None
    if r:
        if r.status_code == 200:
            try:
                with open(tle_filename, "wb") as f:
                    f.write(r.content)
                    f.close()
                    # Update the time stamp so that we know
                    # when this file was imported
                    tle_data_last_download = datetime.datetime.now()
                    success = True
            except:
                logging.debug(f"Cannot update TLE data to file {tle_filename}")
    return success


def read_tle_data(tle_filename: str = "amateur.tle"):
    """
    Imports the Celestrak TLE data from a local file.
    Create dictionary based on given data.
    TLE data consists of three lines:
    Line 1 - identifier (aka satellite name)
    Line 2 - TLE Data Line 1
    Line 3 - TLE Data Line 2

    The identifier will be provided in two different formats:

    satellite name (satellite ID)
    OR
    satellite name

    If the satellite ID is present, this function will prefer the satellite ID
    over the satellite name.
    If only the satellite name (but no ID) is present, then all space characters
    will be replaced with dashes.

    Parameters
    ==========
    tle_filename : 'str'
        local file that is to be parsed. File format:
        see http://www.celestrak.com/NORAD/elements/amateur.txt

    Returns
    =======
    success: 'bool'
        True if operation was successful
    tle_data: 'dict'
        dictionary which contains the parsed data. Global variable
    """

    success: bool = False
    global tle_data

    # Open the local file and read it
    try:
        with open(f"{tle_filename}", "r") as f:
            if f.mode == "r":
                lines = f.readlines()
                f.close()
    except:
        lines = None

    if lines:
        if len(lines) % 3 != 0:
            logging.debug(f"Invalid TLE file structure for file {tle_filename}")
            success = False
            return success, tle_data
        lc = 1
        tle_data.clear()
        # Retrieve the data and create the dictionary
        for tle_satellite in lines[0::3]:

            # Process the key. Try to extract the ID (if present).
            # Otherwise, replace all blanks with dashes
            tle_satellite = tle_satellite.rstrip()
            matches = re.search(r"^.*(\()(.*)(\))$", tle_satellite)
            if matches:
                tle_key = matches[2]
            else:
                tle_key = tle_satellite.replace(" ", "-")
            # Convenience mapping
            if tle_key == "ZARYA":
                tle_key = "ISS"
            # Get the actual TLE data
            tle_line1 = lines[lc].rstrip()
            tle_line2 = lines[lc + 1].rstrip()
            lc += 3
            tle_data[f"{tle_key}"] = {
                "tle_satellite": tle_satellite,
                "tle_line1": tle_line1,
                "tle_line2": tle_line2,
            }
    # Did we manage to download something?
    success: bool = True if len(tle_data) != 0 else False
    return success, tle_data


def get_tle_data(satellite_name: str, tle_data_ttl: int = 1):
    """
    Try to look up the given (partial) satellite name
    and return its TLE data. Prior to performing the lookup,
    we will first check if the data is older than x days (TTL parameter)
    If this is the case, then the file and the internal dictionary
    will be refreshed prior to running the lookup


    Parameters
    ==========
    satellite_name: 'str'
        Name of the satellite that is to be searched.
        ID or (if ID not present) dash-ed name
    tle_data_ttl: 'int'
        time-to-live life span of the TLE data in days

    Returns
    =======
    success: 'bool'
        True if operation was successful
    tle_data_line1: 'str'
        TLE data line 1 (or 'None' if not found)
    tle_data_line2: 'str'
        TLE data line 2 (or 'None' if not found)
    """
    success: bool = False
    global tle_data, tle_data_last_download

    tle_data_line1 = tle_data_line2 = tle_satellite = None
    satellite_name = satellite_name.upper()
    # Convenience mapping :-)
    if satellite_name == "ZARYA":
        satellite_name = "ISS"

    # check if the file's time-to-live period has expired
    ttl_expired: bool = False
    if tle_data_last_download:
        last_download = datetime.datetime.now() - tle_data_last_download
        if last_download.days > tle_data_ttl:
            ttl_expired = True
    # in case the variable was initialized with 'None'
    else:
        ttl_expired = True

    # Re-acquire and re-read new data if the TLE data has expired
    if ttl_expired:
        success = refresh_tle_file("amateur.tle")
        if not success:
            return success, None, None, None
        success, tle_data = read_tle_data("amateur.tle")
        if not success:
            return success, None, None, None

    if satellite_name in tle_data:
        tle_satellite = tle_data[satellite_name]["tle_satellite"]
        tle_data_line1 = tle_data[satellite_name]["tle_line1"]
        tle_data_line2 = tle_data[satellite_name]["tle_line2"]
        success = True
    return success, tle_satellite, tle_data_line1, tle_data_line2


def get_next_satellite_pass_for_latlon(
    latitude: float,
    longitude: float,
    requested_date: datetime.datetime,
    tle_satellite_name: str,
    elevation: float = 0.0,
):
    """
    Determine the next pass of the ISS for a given set
    of coordinates for a certain date

    Parameters
    ==========
    latitude : 'float'
        Latitude value
    longitude : 'float'
        Longitude value
    requested_date: class 'datetime'
        Datestamp for the given calculation
    tle_satellite_name: 'str'
        Name of the satellite whose pass we want to
        calculate (see http://www.celestrak.com/NORAD/elements/amateur.txt)
    elevation : 'float'
        Elevation in meters above sea levels
        Default is 0 (sea level)

    Returns
    =======
    rise_time: 'Datetime'
        Rise time
    rise_azimuth: 'float'
        Rise azimuth
    maximum_time: 'Datetime'
        maximum time
    maximum_altitude: 'float'
        Maximul altitude
    set_time: 'Datetime'
        Set time
    set_azimuth: 'float'
        Set azimuth

    """

    # Try to get the satellite information from the dictionary
    # Return error settings if not found
    success, tle_satellite, tle_data_line1, tle_data_line2 = get_tle_data(
        tle_satellite_name
    )
    if not success:
        return False, None, None, None, None, None, None

    ts = api.load.timescale()
    satellite = EarthSatellite(tle_data_line1, tle_data_line2, tle_satellite, ts)

    pos = api.Topos(
        latitude_degrees=latitude, longitude_degrees=longitude, elevation_m=elevation
    )

    today = requested_date
    tomorrow = requested_date + datetime.timedelta(days=1)

    t = ts.utc(
        year=today.year,
        month=today.month,
        day=today.day,
        hour=today.hour,
        minute=today.minute,
        second=today.second,
    )
    days = t - satellite.epoch
    logging.debug("{:.3f} days away from epoch".format(days))

    t0 = ts.utc(today.year, today.month, today.day, today.hour, today.minute, today.second)
    t1 = ts.utc(tomorrow.year, tomorrow.month, tomorrow.day, tomorrow.hour, tomorrow.minute, tomorrow.second)

    t, events = satellite.find_events(pos, t0, t1, altitude_degrees=10.0)
    for ti, event in zip(t, events):
        name = ("rise above 10°", "culminate", "set below 10°")[event]
        print(ti.utc_strftime("%Y %b %d %H:%M:%S"), name)

    # return True, rise_time, rise_azimuth, maximum_altitude_time, maximum_altitude, set_time, set_azimuth, duration


def get_sun_moon_rise_set_for_latlon(
    latitude: float,
    longitude: float,
    requested_date: datetime.datetime,
    elevation: float = 0.0,
):
    """
    Determine sunrise/sunset and moonrise/moonset for a given set of coordinates
    for a certain date

    Parameters
    ==========
    latitude : 'float'
        Latitude value
    longitude : 'float'
        Longitude value
    requested_date: class 'datetime'
        Datestamp for the given calculation
    elevation : 'float'
        Elevation in meters above sea levels
        Default is 0 (sea level)

    Returns
    =======
    sunrise: 'datetime'
        Datetime object of the next sunrise
        for the given coordinates and date
        Timezone = UTC
    sunset: 'datetime'
        Datetime object of the next sunset
        for the given coordinates and date
        Timezone = UTC
    moonrise: 'datetime'
        Datetime object of the next moonrise
        for the given coordinates and date
        Timezone = UTC
    moonset: 'datetime'
        Datetime object of the next moonset
        for the given coordinates and date
        Timezone = UTC
    """

    ts = api.load.timescale()
    eph = api.load("de421.bsp")

    sunrise = sunset = moonrise = moonset = None

    today = requested_date
    tomorrow = requested_date + datetime.timedelta(days=1)

    pos = api.Topos(
        latitude_degrees=latitude, longitude_degrees=longitude, elevation_m=elevation
    )

    t0 = ts.utc(today.year, today.month, today.day)
    t1 = ts.utc(tomorrow.year, tomorrow.month, tomorrow.day)
    t, y = almanac.find_discrete(t0, t1, almanac.sunrise_sunset(eph, pos))

    for ti, yi in zip(t, y):
        if yi:
            sunrise = ti.utc_datetime()
        else:
            sunset = ti.utc_datetime()

    f = almanac.risings_and_settings(eph, eph["Moon"], pos)
    t, y = almanac.find_discrete(t0, t1, f)

    for ti, yi in zip(t, y):
        if yi:
            moonrise = ti.utc_datetime()
        else:
            moonset = ti.utc_datetime()
    return sunrise, sunset, moonrise, moonset


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(module)s -%(levelname)s - %(message)s')

    logging.debug(
        get_sun_moon_rise_set_for_latlon(51.838860, 8.326871, datetime.datetime.now() + datetime.timedelta(days=1), 74.0)
    )

    tle_data_last_download = None
    logging.debug("Download TLE Data")
    refresh_tle_file()
    logging.debug("Import TLE Data")
    success, tle_data = read_tle_data()
    logging.debug("Get TLE data for Es'Hail2")
    logging.debug(get_tle_data("ES'HAIL-2"))
    logging.debug("Get next ISS pass")
    thedate = datetime.datetime.now()
    logging.debug(
        get_next_satellite_pass_for_latlon(
            51.838890, 8.326747, thedate + datetime.timedelta(days=0), "ISS", 74.0
        )
    )
