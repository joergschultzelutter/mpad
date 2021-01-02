#
# Multi-Purpose APRS Daemon: Repeatermap Modules
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: Downloads raw data set from repeatermap.org, updates
# the data set and then permits the user to look for e.g. the
# nearest c4fm repeater in the 2m band
#

import requests
import json
import math
from geo_conversion_modules import (
    convert_maidenhead_to_latlon,
    convert_latlon_to_maidenhead,
)
from utility_modules import check_if_file_exists
from geo_conversion_modules import Haversine
import logging


def download_repeatermap_raw_data_and_write_it_to_disc(
    url: str = "http://www.repeatermap.de/api.php",
    repeatermap_raw_data_file: str = "repeatermap.raw",
):
    """
    Downloads the repeatermap.de data and write it to a file 'as is'
    That file needs to be post-processed at a later point in time

    Parameters
    ==========
    url: 'str'
        Source URL where we will get the data from.
    repeatermap_raw_data_file: 'str'
        Filename of the target file which will hold the raw data

    Returns
    =======
    success: 'bool'
        True if operation was successful
    """
    success = False
    resp = requests.get(url)
    if resp.status_code == 200:
        try:
            with open(f"{repeatermap_raw_data_file}", "w") as f:
                f.write(resp.text)
                f.close()
            success = True
        except:
            logging.debug(
                f"Cannot write repeatermap.de data to local disc file '{repeatermap_raw_data_file}'"
            )
    return success


def read_repeatermap_raw_data_from_disk(
    repeatermap_raw_data_file: str = "repeatermap.raw",
):
    """
    Read the repeatermap.de raw data from disc.
    Return the file's content to the user as a JSON string for further processing

    Parameters
    ==========
    repeatermap_raw_data_file: 'str'
        Filename of the file which contains the raw data from repeatermap.de

    Returns
    =======
    success: 'bool'
        True if operation was successful
    repeatermap_raw_json_content: 'str'
        Contains the file's raw JSON content (otherwise 'None')
    """
    success = False
    repeatermap_raw_json_content = None
    try:
        with open(f"{repeatermap_raw_data_file}", "r") as f:
            if f.mode == "r":
                repeatermap_raw_json_content = f.read()
                f.close()
                success = True
    except:
        logging.debug(f"Cannot read '{repeatermap_raw_data_file}' from disc")
    return success, repeatermap_raw_json_content


def calculate_band_name(frequency: float):
    """
    Used to guesstimate the human-readable name of the amateur radio band for
    the given frequency. Again - this is just a guess and nowhere accurate
    (e.g. differences between ITU regions are disregarded)

    Parameters
    ==========
    frequency: 'float'
        Frequency in MHz

    Returns
    =======
    success: 'bool'
        True if operation was successful
    human_readable_band_name: 'str'
        Human-readable band name for the given frequency, e.g. '2m'
        'None' if no entry was found
    """

    human_readable_band_name = None
    success = False
    band_dictionary = {
        "2200m": {"from": 0.13, "to": 0.14},
        "630m": {"from": 0.47, "to": 0.48},
        "160m": {"from": 1.8, "to": 2.0},
        "80m": {"from": 3.5, "to": 4.0},
        "60m": {"from": 5.0, "to": 5.9},
        "40m": {"from": 7.0, "to": 7.3},
        "30m": {"from": 10.0, "to": 10.2},
        "20m": {"from": 14.0, "to": 14.4},
        "17m": {"from": 18.0, "to": 18.2},
        "15m": {"from": 21.0, "to": 22.0},
        "12m": {"from": 24.0, "to": 25.0},
        "10m": {"from": 28.0, "to": 30.0},
        "6m": {"from": 50.0, "to": 54.0},
        "4m": {"from": 70.0, "to": 71.0},
        "2m": {"from": 144.0, "to": 148.0},
        "1.25m": {"from": 219.0, "to": 225.0},
        "70cm": {"from": 420.0, "to": 450.0},
        "33cm": {"from": 900.0, "to": 930.0},
        "23cm": {"from": 1200.0, "to": 1300.0},
        "13cm": {"from": 2300.0, "to": 2500.0},
        "9cm": {"from": 3300.0, "to": 3500.0},
        "6cm": {"from": 5600.0, "to": 5900.0},
        "5cm": {"from": 5600.0, "to": 6000.0},
        "3cm": {"from": 10000.0, "to": 10500.0},
        "2cm": {"from": 24000.0, "to": 24300.0},
        "6mm": {"from": 47000.0, "to": 47200.0},
        "4mm": {"from": 76000.0, "to": 78200.0},
        "2,5mm": {"from": 122000.0, "to": 123000.0},
        "2mm": {"from": 134000.0, "to": 141000.0},
        "1.2mm": {"from": 241000.0, "to": 250000.0},
    }
    for band in band_dictionary:
        if band_dictionary[band]["from"] <= frequency <= band_dictionary[band]["to"]:
            human_readable_band_name = band
            success = True
            break

    return success, human_readable_band_name


def create_enriched_mpad_repeatermap_data(repeatermap_raw_json_content: str):
    """
    Processes the raw repeatermap data, enrich it with additional content and
    return the JSON tuple to the user for further processing
    Enrichment process contains:
    - removal of unused data from the original raw data file
    - calculate lat/lon from Maidenhead coordinates
    where lat/lon are not present
    - capitalize the 'mode' (C4FM, DStar) info for normalised data storage
    - calculate human-readable band name based on given frequency (note: this
    value will be a guesstimate

    Parameters
    ==========
    repeatermap_raw_json_content: 'str'
        Raw JSON data from repeatermap.de

    Returns
    =======
    success: 'bool'
        True if operation was successful
    mpad_repeatermap_json: 'str'
        Contains the MPAD-specific JSON dictionary format
        (or 'None' if there was an error)
    """
    success = False
    mpad_repeater_dict = {}  # Create empty dict
    try:
        raw_repeatermap_dictionary = json.loads(repeatermap_raw_json_content)
        success = True
    except:
        return False, None

    mpad_repeater_dict.clear()

    for raw_entry in raw_repeatermap_dictionary["relais"]:
        mode = rx_frequency = tx_frequency = elevation = None
        latitude = longitude = remarks = qth = repeater_id = None
        locator = callsign = band_name = None
        if "id" in raw_entry:
            repeater_id = raw_entry["id"]
        if "mode" in raw_entry:
            mode = raw_entry["mode"]
            mode = mode.upper()
        if "rx" in raw_entry:
            rx_frequency = raw_entry["rx"]
        if "tx" in raw_entry:
            tx_frequency = raw_entry["tx"]
        if "el" in raw_entry:
            elevation = raw_entry["el"]
        if "lat" in raw_entry:
            latitude = raw_entry["lat"]
        if "lon" in raw_entry:
            longitude = raw_entry["lon"]
        if "remarks" in raw_entry:
            remarks = raw_entry["remarks"]
        if "qth" in raw_entry:
            qth = raw_entry["qth"]
        if "call" in raw_entry:
            callsign = raw_entry["call"]
        if rx_frequency:
            # get the human readable band name
            success, band_name = calculate_band_name(rx_frequency)
            if not success:
                band_name = ""
        if "locator" in raw_entry:
            locator = raw_entry["locator"]
            if not latitude or not longitude:
                latitude, longitude = convert_maidenhead_to_latlon(locator)
        # Build locator from lat/lon if not present
        if not locator:
            if latitude and longitude:
                locator = convert_latlon_to_maidenhead(
                    latitude=latitude, longitude=longitude
                )
        # don't add MMDVM hotspots
        if id and "mmdvm" not in remarks.lower() and "hotspot" not in remarks.lower():
            mpad_repeater_dict[f"{repeater_id}"] = {
                "locator": locator,
                "latitude": latitude,
                "longitude": longitude,
                "mode": mode,
                "rx_frequency": rx_frequency,
                "tx_frequency": tx_frequency,
                "band_name": band_name,
                "elevation": elevation,
                "remarks": remarks,
                "qth": qth,
                "callsign": callsign,
            }

    mpad_repeatermap_json = json.dumps(mpad_repeater_dict)
    success = True
    return success, mpad_repeatermap_json


def write_mpad_repeatermap_data_to_disc(
    mpad_repeatermap_json: str, mpad_repeatermap_filename: str = "repeatermap.mpad"
):
    """
    writes the processed repeatermap data in enriched MPAD format
    to disc and returns the operation's status

    Parameters
    ==========
    mpad_repeatermap_json: 'str'
        json string which contains the enriched repeatermap data
    mpad_repeatermap_filename: 'str'
        file name of the native MPAD repeatermap data

    Returns
    =======
    success: 'bool'
        True if operation was successful
    """
    success = False
    try:
        with open(f"{mpad_repeatermap_filename}", "w") as f:
            f.write(mpad_repeatermap_json)
            f.close()
        success = True
    except:
        logging.debug(
            f"Cannot write native repeatermap data to local disc file '{mpad_repeatermap_filename}'"
        )
    return success


def read_mpad_repeatermap_data_from_disc(
    mpad_repeatermap_filename: str = "repeatermap.mpad",
):
    """
    Read the MPAD preprocessed repeatermap file from disc
    and return the JSON string if the file was found

    Parameters
    ==========
    mpad_repeatermap_filename: 'str'
        file name of the native MPAD repeatermap data

    Returns
    =======
    success: 'bool'
        True if operation was successful
    mpad_repeatermap: 'dict'
        dictionary which contains the preprocessed repeatermap data
        (or empty dictionary if nothing was found)
    """
    success = False
    mpad_repeatermap = {}  # create empty dict
    if check_if_file_exists(mpad_repeatermap_filename):
        try:
            with open(f"{mpad_repeatermap_filename}", "r") as f:
                if f.mode == "r":
                    mpad_repeatermap_json = f.read()
                    f.close()
                    success = True
                    mpad_repeatermap = json.loads(mpad_repeatermap_json)
        except:
            logging.debug(f"Cannot read '{mpad_repeatermap_filename}' from disc")
    return success, mpad_repeatermap


def get_nearest_repeater(
    latitude: float,
    longitude: float,
    mpad_repeatermap_dictionary: dict,
    mode: str = None,
    band: str = None,
    units: str = "metric",
):
    """
    For a given set of lat/lon cooordinates, return nearest
    relais from the repeatermap.de relais list

    Parameters
    ==========
    latitude: 'float'
        Latitude of the user's position
    longitude: 'float'
        Longitude of the user's position
    mpad_repeatermap_dictionary: 'dict'
        dictionary which contains the enriched repeatermap data
        (add lat/lon where not present and add band (e.g. 2m))
    mode: 'str'
        optional query parameter. Can be used for querying e.g. for DSTAR, C4FM, ...
    band: 'str'
        optional query parameter. Can be used for querying e.g. for 2m, 70cm, ...
    units: 'str'
        either "imperial" or "metric". Default: "metric"

    Returns
    =======
    success: 'bool'
        True if request was successful
    nearest_repeater: 'dict'
        Either empty (if success=False) or contains the data for the nearest repeater
    """

    nearest_repeater_id = None
    nearest_repeater = []
    success = False
    nearest = 12000

    # apply some convenience settings
    if mode:
        mode = mode.upper()
    if band:
        band = band.lower()
    if mode == "D-STAR":
        mode = "DSTAR"

    # convert lat/lon degrees to radians
    lat1 = latitude * 0.0174533
    lon1 = longitude * 0.0174533

    # loop through all of the ICAO stations and calculate the distance from $lat/$lon
    # remember the one that is closest.
    for repeater in mpad_repeatermap_dictionary:
        lat2 = mpad_repeatermap_dictionary[repeater]["latitude"] * 0.0174533
        lon2 = mpad_repeatermap_dictionary[repeater]["longitude"] * 0.0174533

        # use equirectangular approximation of distance
        x = (lon2 - lon1) * math.cos((lat1 + lat2) / 2)
        y = lat2 - lat1
        # 3959 is radius of the earth in miles
        d = math.sqrt(x * x + y * y) * 3959
        # if this station is nearer than the previous nearest, hang onto it
        if d < nearest:
            # if the user has selected additional query parameters, check them too
            if mode:
                mode_from_dict = mpad_repeatermap_dictionary[repeater]["mode"]
                if mode != mode_from_dict:
                    continue
            if band:
                band_from_dict = mpad_repeatermap_dictionary[repeater]["band_name"]
                if band != band_from_dict:
                    continue
            nearest = d
            nearest_repeater_id = repeater

    # Did we find something?
    if nearest_repeater_id:

        # Yes; extract the content from the dictionary
        locator = mpad_repeatermap_dictionary[nearest_repeater_id]["locator"]
        latitude_repeater = mpad_repeatermap_dictionary[nearest_repeater_id]["latitude"]
        longitude_repeater = mpad_repeatermap_dictionary[nearest_repeater_id][
            "longitude"
        ]
        mode = mpad_repeatermap_dictionary[nearest_repeater_id]["mode"]
        rx_frequency = mpad_repeatermap_dictionary[nearest_repeater_id]["rx_frequency"]
        tx_frequency = mpad_repeatermap_dictionary[nearest_repeater_id]["tx_frequency"]
        band = mpad_repeatermap_dictionary[nearest_repeater_id]["band_name"]
        elevation = mpad_repeatermap_dictionary[nearest_repeater_id]["elevation"]
        remarks = mpad_repeatermap_dictionary[nearest_repeater_id]["remarks"]
        qth = mpad_repeatermap_dictionary[nearest_repeater_id]["qth"]
        callsign = mpad_repeatermap_dictionary[nearest_repeater_id]["callsign"]

        # Calculate distance/bearing/direction between user's position and repeater position
        distance, bearing, direction = Haversine(
            latitude, longitude, latitude_repeater, longitude_repeater, units
        )
        # Round both distance and bearing values
        distance = round(distance)
        bearing = round(bearing)

        # set the unit of measure for the distance variable
        distance_uom = "km"
        if units == "imperial":
            distance_uom = "mi"

        # Build the 'list' response object
        nearest_repeater = {
            "id": nearest_repeater_id,
            "locator": locator,
            "latitude": latitude_repeater,
            "longitude": longitude_repeater,
            "mode": mode,
            "band": band,
            "rx_frequency": rx_frequency,
            "tx_frequency": tx_frequency,
            "elevation": elevation,
            "remarks": remarks,
            "qth": qth,
            "callsign": callsign,
            "distance": distance,
            "distance_uom": distance_uom,
            "bearing": bearing,
            "direction": direction,
        }

        # set the success marker
        success = True

    return success, nearest_repeater


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
    )
    download_repeatermap_raw_data_and_write_it_to_disc()
    success, repeatermap_dot_de_content = read_repeatermap_raw_data_from_disk()
    if success:
        success, local_repeatermap_json = create_enriched_mpad_repeatermap_data(
            repeatermap_dot_de_content
        )
        if success:
            success = write_mpad_repeatermap_data_to_disc(local_repeatermap_json)

    success, mpad_repeater_dictionary = read_mpad_repeatermap_data_from_disc()
    if success:
        success, nearest_repeater = get_nearest_repeater(
            latitude=51.8458575,
            longitude=8.2997425,
            mpad_repeatermap_dictionary=mpad_repeater_dictionary,
            mode="dstar",
            band="70cm",
        )
        if success:
            logging.debug(nearest_repeater)
        else:
            logging.debug("Nothing found!")