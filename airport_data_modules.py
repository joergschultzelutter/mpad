#
# Multi-Purpose APRS Daemon: Airport Data Modules
# Author: Joerg Schultze-Lutter, 2020
# Reimplements parts of the WXBOT code from Martin Nile (KI6WJP)
#
# Purpose: Find nearest airport (or based on the given airport code)
#

import requests
from bs4 import BeautifulSoup
import re
import math
import logging

# icao https://www.aviationweather.gov/docs/metar/stations.txt

icao_dict = {}  # create empty dict
iata_dict = {}  # create empty dict


def read_icao_and_iata_data(icao_filename: str = "stations.txt"):
    """
    Imports the ICAO/IATA data from a local file. Creates dictionaries for
    IATA-ICAO mapping and IATA-lat/lon mapping

    Parameters
    ==========
    icao_filename : 'str'
        local file that is to be parsed. File format:
        see https://www.aviationweather.gov/docs/metar/stations.txt

    Returns
    =======
    iata_dict: 'dict'
        global dictionary mapping between ICAO-Code (3 chars) and IATA-Code
        (4 chars) for all cases where such a mapping exists
    icao_dict: 'dict'
        global dictionary. References IATA-Code (4 chars) to lat/lon,
        METAR capability and the actual airport name
    """

    # Open the local file and read it
    try:
        with open(f"{icao_filename}", "r") as f:
            if f.mode == "r":
                lines = f.readlines()
                f.close()
    except:
        lines = None

    # If the file did contain content, then parse it
    if lines:
        # delete the current dictionaries
        icao_dict.clear()
        iata_dict.clear()

        # Start to parse the file content. The data that we want to digest
        # comes in lines of at least 63 chars and does not start with an
        # exclamation mark. Apart from that, everything is fixed file format

        for line in lines:
            line = line.rstrip()
            if len(line) > 63:
                if line[0] != "!" and line[0:11] != "CD  STATION":
                    # Extract all fields
                    icao = line[20:24]
                    icao = icao.strip()
                    iata = line[26:29]
                    iata = iata.strip()
                    latdeg = line[39:41]
                    latmin = line[42:44]
                    latns = line[44:45]
                    londeg = line[47:50]
                    lonmin = line[51:53]
                    lonns = line[53:54]
                    airport_name = line[3:19]
                    metar = line[62:63]

                    # set to 'METAR capable if content is present
                    if metar in ["X", "Z"]:
                        metar = True
                    else:
                        metar = False

                    # Convert DMS coordinates latitude
                    latitude = int(latdeg) + int(latmin) * (1 / 60)
                    if latns == "S":
                        latitude = latitude * -1

                    # Convert DMS coordinates latitude
                    longitude = int(londeg) + int(lonmin) * (1 / 60)
                    if lonns == "W":
                        longitude = longitude * -1

                    # Create IATA - ICAO relationship in dictionary
                    # if ICAO entry exists
                    if len(iata) != 0:
                        iata_dict[f"{iata}"] = {"icao": f"{icao}"}

                    # Create an entry for the IATA data
                    if len(icao) != 0:
                        icao_dict[f"{icao}"] = {
                            "latitude": latitude,
                            "longitude": longitude,
                            "metar_capable": metar,
                            "airport_name": airport_name,
                        }

    return iata_dict, icao_dict


def get_metar_data(icao_code: str):
    """
    Get METAR and TAF data for a given ICAO code.
    TAF data is already downloaded but currently ignored.
    May need to be switched to https://api.met.no/weatherapi/ at
    a later point in time

    Parameters
    ==========
    icao_code : 'str'
        4-character ICAO code of the airport whose
        METAR data is to be downloaded.

    Returns
    =======
    success: 'bool'
        True if operation was successful
    response: 'str'
        METAR string for the given airport
        (or "NOTFOUND" if no data was found)
    """

    # dictionary exists but is empty? Then read content from disc
    # ignore any errors; in that case, the modes simply won't work
    if not icao_dict or not iata_dict:
        read_icao_and_iata_data()

    resp = requests.get(
        f"https://www.aviationweather.gov/"
        f"adds/metars/?station_ids={icao_code}"
        f"&std_trans=standard&chk_metars=on"
        f"&hoursStr=most+recent+only&submitmet=Submit"
    )
    response: str = "NOTFOUND"
    success: bool = False
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text, features="html.parser")
        meintext = re.sub(" {2,}", " ", soup.get_text())

        matches = re.search(r"\b(sorry)\b", meintext, re.IGNORECASE)
        if not matches:
            pos = meintext.find(icao_code)
            if pos != -1:
                remainder = meintext[pos:]
                blah = remainder.splitlines()
                response = blah[0]
                success = True
    return success, response


def validate_iata(iata_code: str):
    """
    Validate the given 3-character IATA Code. Return associated ICAO code
    plus lat/lon/METAR if IATA code was found

    Parameters
    ==========
    iata_code : 'str'
        3-character IATA code of the airport whose METAR data
        is to be downloaded

    Returns
    =======
    success: 'bool'
        True if operation was successful
    latitude: 'float'
        Latitude of the airport (or 0.0 if not found)
    longitude: 'float'
        Longitude of the airport (or 0.0 if not found)
    metar_capable: 'bool'
        Identifies if the airport is METAR capable or not
        (True = METAR capable)
    icao_code: 'str'
        ICAO airport code for the given IATA code (the
        original iata code is not returned)
    """

    latitude: float = 0.0
    longitude: float = 0.0
    metar_capable: bool = False
    success: bool = False
    icao_code: str = None

    # dictionary exists but is empty? Then read content from disc
    # ignore any errors; in that case, the modes simply won't work
    if not icao_dict or not iata_dict:
        read_icao_and_iata_data()

    iata_code = iata_code.upper()
    if iata_code in iata_dict:
        if iata_code in iata_dict:
            icao_code = iata_dict[iata_code]["icao"]
            success, latitude, longitude, metar_capable, icao_code = validate_icao(
                icao_code
            )

    return success, latitude, longitude, metar_capable, icao_code


def validate_icao(icao_code: str):
    """
    Validate the given 4-character ICAO Code.
    Return lat/lon/METAR if IATA code was found

    Parameters
    ==========
    icao_code : 'str'
        4-character ICAO code of the airport
        whose METAR data is to be downloaded.

    Returns
    =======
    success: 'bool'
        True if operation was successful
    latitude: 'float'
        Latitude of the airport (or 0.0 if not found)
    longitude: 'float'
        Longitude of the airport (or 0.0 if not found)
    metar_capable: 'bool'
        Identifies if the airport is METAR capable or not
        (True = METAR capable)
    icao_code: 'str'
        ICAO airport code, Same as input parameter
    """
    latitude: float = 0.0
    longitude: float = 0.0
    metar_capable: bool = False
    success: bool = False

    # dictionary exists but is empty? Then read content from disc
    # ignore any errors; in that case, the modes simply won't work
    if not icao_dict or not iata_dict:
        read_icao_and_iata_data()

    icao_code = icao_code.upper()
    if icao_code in icao_dict:
        latitude = icao_dict[icao_code]["latitude"]
        longitude = icao_dict[icao_code]["longitude"]
        metar_capable = icao_dict[icao_code]["metar_capable"]
        success = True

    return success, latitude, longitude, metar_capable, icao_code


def refresh_icao_file(icaoiata_filename: str = "stations.txt"):
    """
    Imports the ICAO/IATA data from the web and saves it to a local file.

    Parameters
    ==========
    icaoiata_filename : 'str'
        This local file will hold the content
        from https://www.aviationweather.gov/docs/metar/stations.txt.
        Default filename is "stations.txt"

    Returns
    =======
    success: 'bool'
        True if operation was successful
    """

    # This is the fixed name of the URL Source that we are going to download
    file_url = "https://www.aviationweather.gov/docs/metar/stations.txt"
    success: bool = False

    # try to get the file
    try:
        r = requests.get(file_url)
    except:
        logging.debug(f"Cannot download ICAO data from {file_url}")
        r = None
    if r:
        if r.status_code == 200:
            try:
                with open(icaoiata_filename, "wb") as f:
                    f.write(r.content)
                    f.close()
                    success = True
            except:
                logging.debug(f"Cannot update ICAO data to file {icaoiata_filename}")
    return success


def get_nearest_icao(latitude: float, longitude: float):
    """
    For a given set of lat/lon cooordinates, return nearest
    METAR-capable ICAO code to the user

    Parameters
    ==========
    latitude: 'float'
        Latitude of the user's position
    longitude: 'float'
        Longitude of the user's position

    Returns
    =======
    nearesticao: 'str'
        ICAO code of the nearest METAR-capable airport
        (or 'None' if nothing was found)
    """

    nearesticao: str = None
    nearest = 12000

    # dictionary exists but is empty? Then read content from disc
    # ignore any errors; in that case, the modes simply won't work
    if not icao_dict or not iata_dict:
        read_icao_and_iata_data()

    # convert lat/lon degrees to radians
    lat1 = latitude * 0.0174533
    lon1 = longitude * 0.0174533

    # loop through all of the ICAO stations and calculate the distance from $lat/$lon
    # remember the one that is closest.
    for icao_elem in icao_dict:
        lat2 = icao_dict[icao_elem]["latitude"] * 0.0174533
        lon2 = icao_dict[icao_elem]["longitude"] * 0.0174533
        metar_capable = icao_dict[icao_elem]["metar_capable"]

        # use equirectangular approximation of distance
        x = (lon2 - lon1) * math.cos((lat1 + lat2) / 2)
        y = lat2 - lat1
        # 3959 is radius of the earth in miles
        d = math.sqrt(x * x + y * y) * 3959
        # if this station is nearer than the previous nearest, hang onto it
        if d < nearest and metar_capable:
            nearest = d
            nearesticao = icao_elem
    return nearesticao


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(module)s -%(levelname)s - %(message)s')
    logging.debug(get_metar_data("EDDF"))
    logging.debug(validate_iata("FRA"))
    logging.debug(validate_icao("EDDF"))
    logging.debug(refresh_icao_file())
    logging.debug(get_nearest_icao(51.538882, 8.32679))
