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
from utility_modules import build_full_pathname
import csv
import json
from pprint import pformat
from utility_modules import check_if_file_exists
from mpad_config import (
    mpad_tle_amateur_satellites_filename,
    mpad_satellite_frequencies_filename,
    mpad_satellite_data_filename,
)
from messaging_modules import send_apprise_message

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def download_and_write_local_tle_file(
    tle_filename: str = mpad_tle_amateur_satellites_filename,
    apprise_config_file: str = None,
):
    """
    Download the amateur radio satellite TLE data
    and save it to a local file.

    Parameters
    ==========
    tle_filename : 'str'
        This local file will hold the content
        from http://www.celestrak.com/NORAD/elements/amateur.txt
        Default is "tle_amateur_satellites.txt"
    apprise_config_file: 'str'
        Optional Apprise config file name which will be used in case
        of errors, telling MPAD's host that the file could not get downloaded
        (e.g. URL change, URL down, ...)

    Returns
    =======
    success: 'bool'
        True if operation was successful
    """

    # This is the fixed name of the file that we are going to download
    file_url = "http://www.celestrak.com/NORAD/elements/amateur.txt"
    absolute_path_filename = build_full_pathname(file_name=tle_filename)
    success: bool = False

    # try to get the file
    try:
        r = requests.get(file_url)
    except:
        logger.info(msg=f"Cannot download TLE data from {file_url}")
        r = None
    if r:
        if r.status_code == 200:
            try:
                with open(absolute_path_filename, "wb") as f:
                    f.write(r.content)
                    f.close()
                    success = True
            except:
                logger.info(
                    msg=f"Cannot update TLE data to file {absolute_path_filename}"
                )

    # Generate an Apprise message in case we were unable to download the file
    if not success and apprise_config_file:
        # send_apprise_message will check again if the file exists or not
        # Therefore, we can skip any further detection steps here
        send_apprise_message(
            message_header="MPAD External Dependency Error",
            message_body=f"Unable to download TLE file file from '{file_url}'",
            apprise_config_file=apprise_config_file,
            message_attachment=None,
        )
    return success


def download_and_write_local_satfreq_file(
    satfreq_filename: str = mpad_satellite_frequencies_filename,
    apprise_config_file: str = None,
):
    """
    Download the amateur radio satellite frequency data
    and save it to a local file.

    Parameters
    ==========
    satfreq_filename : 'str'
        This local CSV file will hold the content
        from http://www.ne.jp/asahi/hamradio/je9pel/satslist.csv
        Default name is "satellite_frequencies.csv"
    apprise_config_file: 'str'
        Optional Apprise config file name which will be used in case
        of errors, telling MPAD's host that the file could not get downloaded
        (e.g. URL change, URL down, ...)

    Returns
    =======
    success: 'bool'
        True if operation was successful
    """

    file_url = "http://www.ne.jp/asahi/hamradio/je9pel/satslist.csv"
    success = False
    absolute_path_filename = build_full_pathname(file_name=satfreq_filename)

    try:
        r = requests.get(file_url)
    except:
        logger.info(msg=f"Cannot download satellite frequency data from {file_url}")
        r = None
    if r:
        if r.status_code == 200:
            try:
                with open(absolute_path_filename, "wb") as f:
                    f.write(r.content)
                    f.close()
                    success = True
            except:
                logger.info(
                    msg=f"Cannot write satellite frequency csv file {absolute_path_filename} to disc"
                )

    # Generate an Apprise message in case we were unable to download the file
    if not success and apprise_config_file:
        # send_apprise_message will check again if the file exists or not
        # Therefore, we can skip any further detection steps here
        send_apprise_message(
            message_header="MPAD External Dependency Error",
            message_body=f"Unable to download satellite frequency csv file from '{file_url}'",
            apprise_config_file=apprise_config_file,
            message_attachment=None,
        )

    return success


def read_local_tle_file(tle_filename: str = mpad_tle_amateur_satellites_filename):
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
    absolute_path_filename = build_full_pathname(file_name=tle_filename)
    lines = None

    # Open the local file and read it

    if check_if_file_exists(absolute_path_filename):
        try:
            with open(f"{absolute_path_filename}", "r") as f:
                if f.mode == "r":
                    lines = f.readlines()
                    f.close()
        except:
            lines = None
    else:
        logger.info(msg=f"Celestrak TLE file '{absolute_path_filename}' does not exist")

    if lines:
        if len(lines) % 3 != 0:
            logger.info(msg=f"Invalid TLE file structure for file {tle_filename}")
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
            # Ensure that the key is always in uppercase
            tle_key = tle_key.upper()

            # Convenience mapping :-)
            if tle_key == "ZARYA":
                tle_key = "ISS"

            # Get the actual TLE data
            tle_line1 = lines[lc].rstrip()
            tle_line2 = lines[lc + 1].rstrip()
            lc += 3
            tle_data[f"{tle_key}"] = {
                "satellite_name": tle_satellite,
                "tle_line1": tle_line1,
                "tle_line2": tle_line2,
            }
    # Did we manage to download something?
    success: bool = True if len(tle_data) != 0 else False
    return success, tle_data


def read_local_satfreq_file(
    satfreq_filename: str = mpad_satellite_frequencies_filename,
):
    """
    Reads the local amateur radio satellite frequency data
    from disc, transforms the data and creates a dictionary
    out of it.

    Parameters
    ==========
    satfreq_filename : 'str'
        This local CSV file holds the content
        from http://www.ne.jp/asahi/hamradio/je9pel/satslist.csv
        Default name is "satellite_frequencies.csv"

    Returns
    =======
    success: 'bool'
        True if operation was successful
    satellite_dictionary: 'dict'
        satellite dictionary, containing all satellites that
        we have found data for. Each satellite can have 1..n
        entries. Each entry can have different data fields.
        Primary key = satellite ID (not satellite name)
    """
    success = False
    absolute_path_filename = build_full_pathname(file_name=satfreq_filename)
    satellite_dictionary = {}

    if check_if_file_exists(absolute_path_filename):
        try:
            with open(absolute_path_filename) as csvfile:
                csv_object = csv.reader(csvfile, delimiter=";")
                for row in csv_object:
                    # Some rows from the CSV cannot be imported; we skip those
                    if len(row) > 6:
                        satellite_name = row[0].strip()
                        # Find the satellite NAME (contained in the brackets). If
                        # found, remove it from the string. Remainder is the
                        # satellit ID. This solution works for the majority
                        # of the entries in the list
                        regex_string = r"(\()(.*)(\))$"
                        matches = re.findall(
                            pattern=regex_string,
                            string=satellite_name,
                            flags=re.IGNORECASE,
                        )
                        if matches:
                            # This solution is far from ideal but the source file has way too many different formats
                            # so we'll try to get at least some of that data
                            satellite_key = re.sub(
                                pattern=regex_string,
                                repl="",
                                string=satellite_name,
                                flags=re.IGNORECASE,
                            ).strip()
                        else:
                            # if brackets are missing, assime satellite ID = satellite name
                            satellite_key = satellite_name.replace(" ", "-")

                        # Convert to UpperCase. This file may provide some
                        # sats in upper/lowercase; TLE data however is always in uppercase
                        satellite_key = satellite_key.upper()

                        # extract uplink/downloing frequencies etc
                        # do not convert to float but treat them as
                        # string; some entries contain more than one
                        # frequency value for e.g. uplink
                        uplink = row[2].strip()
                        uplink = uplink if len(uplink) != 0 else None
                        downlink = row[3].strip()
                        downlink = downlink if len(downlink) != 0 else None
                        beacon = row[4].strip()
                        beacon = beacon if len(beacon) != 0 else None
                        satellite_mode = row[5].strip()
                        satellite_mode = (
                            satellite_mode if len(satellite_mode) != 0 else None
                        )

                        # Create a dictionary entry for that single uplink/downlink entry
                        # Each satellite can have 1..n of such entries
                        satellite_element = {
                            # "satellite_name": satellite_name,
                            "uplink": uplink,
                            "downlink": downlink,
                            "beacon": beacon,
                            "satellite_mode": satellite_mode,
                        }
                        # We store these entries in a list
                        # if our satellite already exists in the final
                        # dictionary, get the existing list so we can
                        # add the new entry to it. Otherwise, create a
                        # new empty list.
                        # Finally, add the new entry
                        if satellite_key in satellite_dictionary:
                            satellite_data = satellite_dictionary[satellite_key]
                        else:
                            satellite_data = []
                        satellite_data.append(satellite_element)
                        satellite_dictionary[satellite_key] = satellite_data
            success = True
        except:
            success = False
    else:
        logger.info(
            msg=f"Satellite frequency data file '{absolute_path_filename}' does not exist"
        )
    return success, satellite_dictionary


def update_local_mpad_satellite_data(apprise_config_file: str = None):
    """
    Wrapper method for importing both TLE and Satellite Frequency data,
    blending the data records (whereas possible) and write the JSON content
    to a local file.

    This method is used by MPAD's scheduler process.

    If the satellite frequency file cannot be found or cannot be downloaded, the
    TLE file is still out main priority. As we read both files in a sequential manner,
    there shouldn't be any issues, though.

    Parameters
    ==========

    Returns
    =======
    success: 'bool'
        True if request was successful
    """

    logger.info(msg="Generating local satellite frequencies database")
    download_and_write_local_satfreq_file(apprise_config_file=apprise_config_file)
    logger.info(msg="Generating local TLE database")
    download_and_write_local_tle_file(apprise_config_file=apprise_config_file)
    logger.info(msg="Creating blended satellite database version")
    success, json_satellite_data = create_native_satellite_data()
    if success:
        logger.info(msg="Writing blended satellite database to disc")
        success = write_mpad_satellite_data_to_disc(
            mpad_satellite_json=json_satellite_data
        )
    return success


def create_native_satellite_data():
    """
    Based on the satellite ID (not the satellite name), try
    to enrich the TLE dictionary with the matching satellite
    frequency data. Ultimately, dump the dict to a JSON string

    Parameters
    ==========

    Returns
    =======
    success: 'bool'
        True if operation was successful
    tle_data: 'str'
        dict content, dumped to a JSON string object
        data is ready to be written to a file
    """

    success = False
    # read the local TLE data and store the content in a dict variable
    success, tle_data = read_local_tle_file()
    if success:
        # read the satellite frequency data and store the content
        # in a dict variable
        success, satfreq_data = read_local_satfreq_file()
        if success:
            # Iterate through the TLE satellite ID's
            # These entries are our master
            for tle_satellite in tle_data:
                # Does the TLE satellite ID exist in the
                # satellite frequency database?
                if tle_satellite in satfreq_data:
                    # Yes, get the frequency entries from that
                    # dict and amend the TLE entry
                    satfreq_json = satfreq_data[tle_satellite]
                    tle_json = tle_data[tle_satellite]
                    tle_json["frequencies"] = satfreq_json
                    tle_data[tle_satellite] = tle_json
        # TLE data needs to be present - frequency data
        # is rather optional. As long as we can download
        # the TLE data, assume a positive status
        success = True
    else:
        tle_data = {}

    # dump the TLE entry to a string so that we
    # can write the file to disc
    return success, json.dumps(tle_data)


def write_mpad_satellite_data_to_disc(
    mpad_satellite_json: str,
    mpad_satellite_filename: str = mpad_satellite_data_filename,
):
    """
    writes the processed satellite data in enriched MPAD format
    to disc and returns the operation's status
    Enriched format contains TLE data plus frequencies;

    Parameters
    ==========
    mpad_satellite_json: 'str'
        json string which contains the enriched satellite data
    mpad_satellite_filename: 'str'
        file name of the native MPAD satellite data

    Returns
    =======
    success: 'bool'
        True if operation was successful
    """
    success = False
    absolute_path_filename = build_full_pathname(file_name=mpad_satellite_filename)
    try:
        with open(f"{absolute_path_filename}", "w") as f:
            f.write(mpad_satellite_json)
            f.close()
        success = True
    except:
        logger.info(
            msg=f"Cannot write native satellite data to local disc file '{absolute_path_filename}'"
        )
    return success


def read_mpad_satellite_data_from_disc(
    mpad_satellite_filename: str = mpad_satellite_data_filename,
):
    """
    reads the pre-processed satellite data in enriched MPAD format
    (JSON) from disc, then returns the operation's status
    and a dict object which contains the JSON data
    Enriched format contains TLE data plus frequencies

    Parameters
    ==========
    mpad_satellite_filename: 'str'
        file name of the native MPAD satellite data

    Returns
    =======
    success: 'bool'
        True if operation was successful
    mpad_satellite_data: 'dict'
        dictionary, containing the enriched satellite data
    """
    success = False
    absolute_path_filename = build_full_pathname(file_name=mpad_satellite_filename)
    mpad_satellite_data = {}  # create empty dict
    if check_if_file_exists(absolute_path_filename):
        try:
            with open(f"{absolute_path_filename}", "r") as f:
                if f.mode == "r":
                    mpad_satellite_data_json = f.read()
                    f.close()
                    mpad_satellite_data = json.loads(mpad_satellite_data_json)
                    success = True
        except:
            logger.info(
                msg=f"Cannot read MPAD satellite data file '{absolute_path_filename}' from disc"
            )
            success = False
    else:
        logger.info(
            msg=f"MPAD satellite data file '{absolute_path_filename}' does not exist"
        )
    return success, mpad_satellite_data


def get_tle_data(satellite_id: str):
    """
    Try to look up the given (partial) satellite name
    and return its TLE data.

    Parameters
    ==========
    satellite_id: 'str'
        ID of the satellite that is to be searched.
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

    success, satellite_data = read_mpad_satellite_data_from_disc()
    if success:
        satellite_id = satellite_id.upper()
        # Convenience mapping :-)
        if satellite_id == "ZARYA":
            satellite_id = "ISS"

        if satellite_id in satellite_data:
            tle_satellite = satellite_data[satellite_id]["satellite_name"]
            tle_data_line1 = satellite_data[satellite_id]["tle_line1"]
            tle_data_line2 = satellite_data[satellite_id]["tle_line2"]
            success = True
        else:
            success = False
    return success, tle_satellite, tle_data_line1, tle_data_line2


def get_satellite_frequency_data(satellite_id: str):
    """
    Try to look up the given (partial) satellite name
    and return its satellite frequency data whereas present

    Parameters
    ==========
    satellite_id: 'str'
        Name of the satellite that is to be searched.
        ID or (if ID not present) dash-ed name

    Returns
    =======
    success: 'bool'
        True if operation was successful
    satellite_name: 'str'
        Name of the satellite (if found)
    frequency_data: 'list'
        List item, containing 0..n dict entries of
        satellite_data
    """
    success: bool = False
    frequency_data = []
    satellite_name = None

    success, satellite_data = read_mpad_satellite_data_from_disc()
    if success:
        satellite_id = satellite_id.upper()
        # Convenience mapping :-)
        if satellite_id == "ZARYA":
            satellite_id = "ISS"

        if satellite_id in satellite_data:
            satellite_name = satellite_data[satellite_id]["satellite_name"]
            if "frequencies" in satellite_data[satellite_id]:
                frequency_data = satellite_data[satellite_id]["frequencies"]
            success = True
        else:
            success = False
    return success, satellite_name, frequency_data


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
        satellite_id=tle_satellite_name
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
        # logger.info(msg="{:.3f} days away from epoch".format(days))

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
    pass
