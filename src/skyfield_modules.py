#
# Multi-Purpose APRS Daemon: Skyfield Modules
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: Find satellite positions and/or sun/moon rise/set
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

import datetime
import re
import requests
from skyfield import api, almanac
from skyfield.api import EarthSatellite
import logging
from math import floor, ceil
from pprint import pformat

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def update_local_tle_file(tle_filename: str = "tle_amateur_satellites.txt"):
    """
    Download the amateur radio satellite TLE data
    and save it to a local file.

    Parameters
    ==========
    tle_filename : 'str'
        This local file will hold the content
        from http://www.celestrak.com/NORAD/elements/amateur.txt
        Default is "tle_amateur_satellites.txt"

    Returns
    =======
    success: 'bool'
        True if operation was successful
    """

    # This is the fixed name of the file that we are going to download
    tle_data_file_url = "http://www.celestrak.com/NORAD/elements/amateur.txt"
    success: bool = False

    # try to get the file
    try:
        r = requests.get(tle_data_file_url)
    except:
        logger.info(f"Cannot download TLE data from {tle_data_file_url}")
        r = None
    if r:
        if r.status_code == 200:
            try:
                with open(tle_filename, "wb") as f:
                    f.write(r.content)
                    f.close()
                    success = True
            except:
                logger.info(f"Cannot update TLE data to file {tle_filename}")
    return success


def read_local_tle_file(tle_filename: str = "tle_amateur_satellites.txt"):
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
        dictionary which contains the parsed data
    """

    success: bool = False
    tle_data = {}

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
            logger.info(f"Invalid TLE file structure for file {tle_filename}")
            success = False
            return success, tle_data
        lc = 1
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


def get_tle_data(satellite_name: str):
    """
    Try to look up the given (partial) satellite name
    and return its TLE data.

    Parameters
    ==========
    satellite_name: 'str'
        Name of the satellite that is to be searched.
        ID or (if ID not present) dash-ed name

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
    tle_data_line1 = tle_data_line2 = tle_satellite = None

    success, tle_data = read_local_tle_file()
    if success:
        satellite_name = satellite_name.upper()
        # Convenience mapping :-)
        if satellite_name == "ZARYA":
            satellite_name = "ISS"

        if satellite_name in tle_data:
            tle_satellite = tle_data[satellite_name]["tle_satellite"]
            tle_data_line1 = tle_data[satellite_name]["tle_line1"]
            tle_data_line2 = tle_data[satellite_name]["tle_line2"]
            success = True
        else:
            success = False
    return success, tle_satellite, tle_data_line1, tle_data_line2


def get_next_satellite_pass_for_latlon(
    latitude: float,
    longitude: float,
    requested_date: datetime.datetime,
    tle_satellite_name: str,
    elevation: float = 0.0,
    number_of_results: int = 1,
    visible_passes_only: bool = False,
    altitude_degrees: float = 10.0,
    units: str = "metric",
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
        Start-datestamp for the given calculation
    tle_satellite_name: 'str'
        Name of the satellite whose pass we want to
        calculate (see http://www.celestrak.com/NORAD/elements/amateur.txt)
    elevation : 'float'
        Elevation in meters above sea levels
        Default is 0 (sea level)
    number_of_results: int
        default: 1, supports up to 5 max results
    visible_passes_only: bool
        If True, then show only visible passes to the user
    altitude_degrees: float
        default: 10.0 degrees
    units: str
        units of measure, either metric or imperial

    Returns
    =======
    success: bool
        False in case an error has occurred

    """

    assert 1 <= number_of_results <= 5
    assert units in ["metric", "imperial"]

    satellite_response_data = {}

    rise_time = (
        rise_azimuth
    ) = maximum_time = maximum_altitude = set_time = set_azimuth = None

    # Try to get the satellite information from the dictionary
    # Return error settings if not found
    success, tle_satellite, tle_data_line1, tle_data_line2 = get_tle_data(
        tle_satellite_name
    )
    if success:
        ts = api.load.timescale()
        eph = api.load("de421.bsp")

        satellite = EarthSatellite(tle_data_line1, tle_data_line2, tle_satellite, ts)

        pos = api.Topos(
            latitude_degrees=latitude,
            longitude_degrees=longitude,
            elevation_m=elevation,
        )

        today = requested_date
        tomorrow = requested_date + datetime.timedelta(days=10)

        #
        # t = ts.utc(
        #    year=today.year,
        #    month=today.month,
        #    day=today.day,
        #    hour=today.hour,
        #    minute=today.minute,
        #    second=today.second,
        # )
        # days = t - satellite.epoch
        # logger.info("{:.3f} days away from epoch".format(days))

        t0 = ts.utc(
            today.year, today.month, today.day, today.hour, today.minute, today.second
        )
        t1 = ts.utc(
            tomorrow.year,
            tomorrow.month,
            tomorrow.day,
            tomorrow.hour,
            tomorrow.minute,
            tomorrow.second,
        )

        t, events = satellite.find_events(
            pos, t0, t1, altitude_degrees=altitude_degrees
        )

        events_dictionary = {}

        found_rise = False
        for ti, event in zip(t, events):
            #            name = ("rise above 10°", "culminate", "set below 10°")[event]
            #            print(ti.utc_strftime("%Y %b %d %H:%M:%S"), name)

            # create a datetime object out of the skyfield date/time-stamp
            # we don't really need the microsecond information but keeping this data
            # should make our dictionary key unique :-)
            timestamp = datetime.datetime(
                year=ti.utc.year,
                month=ti.utc.month,
                day=ti.utc.day,
                hour=ti.utc.hour,
                minute=ti.utc.minute,
                second=floor(ti.utc.second),
                microsecond=floor(1000000 * (ti.utc.second - floor(ti.utc.second))),
            )
            is_sunlit = satellite.at(ti).is_sunlit(eph)
            difference = satellite - pos
            topocentric = difference.at(ti)
            alt, az, distance = topocentric.altaz()
            above_horizon = True if alt.degrees > 0 else False

            # (re)calculate km distance in miles if the user has requested imperial units
            _div = 1.0
            if units == "imperial":
                _div = 1.609  # change km to miles

            # 'event' values: '0' = rise above, '1' = culminate, '2' = set below
            # at the point in time for which the user has requested the data
            # there might happen a flyby (meaning that we receive a '1'/'2'
            # even as first event). We are going to skip those until we receive
            # the first '0' event
            if event == 0 or found_rise:
                events_dictionary[timestamp] = {
                    "event": event,
                    "above_horizon": above_horizon,
                    "altitude": ceil(altitude_degrees),
                    "azimuth": ceil(az.degrees),
                    "distance": floor(
                        distance.km / _div
                    ),  # Change km to miles if necessary
                    "is_sunlit": is_sunlit,
                }
                found_rise = True

        # We now have a dictionary that is a) in the correct order and b) starts with a '0' event
        # Try to process the data and build the dictionary that will contain
        # the blended data

        is_visible = False
        rise_date = culmination_date = set_date = datetime.datetime.min
        alt = az = dst = 0.0

        count = 0

        for event_datetime in events_dictionary:
            event_item = events_dictionary[event_datetime]
            event = event_item["event"]
            above_horizon = event_item["above_horizon"]
            altitude = event_item["altitude"]
            azimuth = event_item["azimuth"]
            distance = event_item["distance"]
            is_sunlit = event_item["is_sunlit"]

            if event == 0:  # rise
                rise_date = event_datetime
                if is_sunlit:
                    is_visible = True
            elif event == 1:  # culmination
                culmination_date = event_datetime
                alt = altitude
                az = azimuth
                dst = distance
                if is_sunlit:
                    is_visible = True
            elif event == 2:  # set
                set_date = event_datetime
                if is_sunlit:
                    is_visible = True
                # we should now have all of the required data for creating
                # a full entry. Now check if we need to add it
                if is_visible or not visible_passes_only:
                    satellite_response_data[rise_date] = {
                        "culmination_date": culmination_date,
                        "set_date": set_date,
                        "altitude": alt,
                        "azimuth": az,
                        "distance": dst,
                        "is_visible": is_visible,
                    }
                    # Increase entry counter and end for loop
                    # if we have enough results
                    count = count + 1
                    if count >= number_of_results:
                        break
                # Otherwise, we are going to reset our work variables for
                # the next loop that we are going to enter
                is_visible = False
                rise_date = culmination_date = set_date = datetime.datetime.min
                alt = az = dst = 0.0
    return success, satellite_response_data


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
    logger.info(
        get_sun_moon_rise_set_for_latlon(
            latitude=51.838860,
            longitude=8.326871,
            requested_date=datetime.datetime.now() + datetime.timedelta(days=1),
            elevation=74.0,
        )
    )

    #    update_local_tle_file()

    #    logger.info("Get TLE data for Es'Hail2")
    #    logger.info(get_tle_data("ES'HAIL-2"))
    logger.info("Get next ISS pass")
    thedate = datetime.datetime.utcnow()
    logger.info(
        pformat(
            get_next_satellite_pass_for_latlon(
                latitude=51.838890,
                longitude=8.326747,
                requested_date=thedate + datetime.timedelta(days=0),
                tle_satellite_name="ISS",
                elevation=74.0,
                number_of_results=5,
                visible_passes_only=True,
            )
        )
    )
