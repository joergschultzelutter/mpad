#
# Multi-Purpose APRS Daemon: Geo Conversion Modules
# Author: Joerg Schultze-Lutter, 2020
#
# Various geocoordinate conversion routines
#

import utm
import maidenhead
from mgrs import MGRStoLL, LLtoMGRS
from math import radians, cos, sin, asin, sqrt, atan2, degrees
import logging


def convert_latlon_to_utm(latitude: float, longitude: float):
    """
    Convert latitude / longitude coordinates to UTM
    (Universal Transverse Mercator) coordinates

    Parameters
    ==========
    latitude : 'float'
        Latitude value
    longitude : 'float'
        Longitude value

    Returns
    =======
    zone_number: 'int'
        UTM zone number for the given set of lat/lon coordinates
    zone_letter: 'str'
        UTM zone letter for the given set of lat/lon coordinates
    easting: 'int'
        UTM easting coordinates for the given set of lat/lon coordinates
    northing: 'int'
        UTM northing coordinates for the given set of lat/lon coordinates
    """

    easting, northing, zone_number, zone_letter = utm.from_latlon(latitude, longitude)
    easting: int = round(easting)
    northing: int = round(northing)
    return zone_number, zone_letter, easting, northing


def convert_utm_to_latlon(
    zone_number: int,
    zone_letter: str,
    easting: int,
    northing: int,
    output_precision: int = 6,
):
    """
    Convert TM (Universal Transverse Mercator) coordinates
    to latitude / longitude

    Parameters
    ==========
    zone_number: 'int'
        UTM zone number for the given set of lat/lon coordinates
    zone_letter: 'str'
        UTM zone letter for the given set of lat/lon coordinates
    easting: 'int'
        UTM easting coordinates for the given set of lat/lon coordinates
    northing: 'int'
        UTM northing coordinates for the given set of lat/lon coordinates
    output_precision: 'int'
        Rounds the lat/lon value after the given position after the comma

    Returns
    =======
    latitude : 'float'
        Latitude value
    longitude : 'float'
        Longitude value
    """

    latitude, longitude = utm.to_latlon(easting, northing, zone_number, zone_letter)
    latitude: float = round(latitude, output_precision)
    longitude: float = round(longitude, output_precision)

    return latitude, longitude


def convert_latlon_to_maidenhead(
    latitude: float, longitude: float, output_precision: int = 4
):
    """
    Convert latitude / longitude coordinates to Maidenhead coordinates

    Parameters
    ==========
    latitude : 'float'
        Latitude value
    longitude : 'float'
        Longitude value
    output_precision: 'int'
        Output precision for lat/lon

    Returns
    =======
    maidenhead_coordinates: 'str'
        Maidenhead coordinates for the given lat/lon with
        the specified precision
    """

    maidenhead_coordinates: str = maidenhead.to_maiden(
        latitude, longitude, precision=output_precision
    )
    return maidenhead_coordinates


def convert_maidenhead_to_latlon(
    maidenhead_coordinates: str, output_precision: int = 6
):
    """
    Convert latitude / longitude coordinates to Maidenhead coordinates

    Parameters
    ==========
    maidenhead_coordinates: 'str'
        Maidenhead coordinates for the given lat/lon with
        the specified precision
    output_precision: 'int'
        Output precision for the lat/lon values (rounding)

    Returns
    =======
    latitude : 'float'
        Latitude value
    longitude : 'float'
        Longitude value
    """
    assert len(maidenhead_coordinates) % 2 == 0

    latitude, longitude = maidenhead.to_location(maidenhead_coordinates)
    latitude: float = round(latitude, output_precision)
    longitude: float = round(longitude, output_precision)
    return latitude, longitude


def convert_latlon_to_mgrs(latitude: float, longitude: float):
    """
    Convert latitude / longitude coordinates to MGRS (Military Grid
    Reference System) coordinates

    Parameters
    ==========
    latitude : 'float'
        Latitude value
    longitude : 'float'
        Longitude value

    Returns
    =======
    mgrs_coordinates: 'str'
        MGRS coordinates for the given set of lat/lon coordinates
    """

    mgrs_coordinates: str = LLtoMGRS(latitude, longitude)
    return mgrs_coordinates


def convert_mgrs_to_latlon(mgrs_coordinates: str, output_precision: int = 6):
    """
    Convert MGRS (Military Grid Reference System) coordinates
    to latitude / longitude coordinates

    Parameters
    ==========
    mgrs_coordinates: 'str'
        MGRS coordinates for the given set of lat/lon coordinates
    output_precision: 'int'
        Output precision for the Maidenhead calculation

    Returns
    =======
    latitude : 'float'
        Latitude value
    longitude : 'float'
        Longitude value
    """

    response = MGRStoLL(mgrs_coordinates)
    latitude = round(response["lat"], output_precision)
    longitude = round(response["lon"], output_precision)
    return latitude, longitude


def convert_latlon_to_dms(latitude: float, longitude: float, output_precision: int = 4):
    """
    Convert latitude / longitude coordinates
    to DMS (Degrees, Minutes, Seconds) coordinates

    Parameters
    ==========
    latitude : 'float'
        Latitude value
    longitude : 'float'
        Longitude value
    output_precision: 'int'
        Output precision for '_deg_sec' values

    Returns
    =======
    latitude_deg: 'int'
        latitude degrees for the given set of lat/lon coordinates
    latitude_min: 'int'
        latitude minutes for the given set of lat/lon coordinates
    latitude_sec: 'int'
        latitude seconds for the given set of lat/lon coordinates
    latitude_heading: 'str'
        latitude heading ('N','S') for the given set of lat/lon coordinates
    longitude_deg: 'int'
        longitude_deg degrees for the given set of lat/lon coordinates
    longitude_deg_min: 'int'
        longitude_deg minutes for the given set of lat/lon coordinates
    longitude_deg_sec: 'int'
        longitude_deg seconds for the given set of lat/lon coordinates
    longitude_deg_heading: 'str'
        longitude_deg heading ('E','W') for the given set of
        lat/lon coordinates
    """

    is_positive_lat = latitude >= 0
    is_positive_lon = longitude >= 0

    latitude = abs(latitude)
    longitude = abs(longitude)

    latitude_min, latitude_sec = divmod(latitude * 3600, 60)
    latitude_deg, latitude_min = divmod(latitude_min, 60)
    longitude_min, longitude_sec = divmod(longitude * 3600, 60)
    longitude_deg, longitude_min = divmod(longitude_min, 60)

    latitude_deg = latitude_deg if is_positive_lat else -latitude_deg
    longitude_deg = longitude_deg if is_positive_lon else -longitude_deg

    latitude_heading: str = "S" if latitude_deg < 0 else "N"
    latitude_deg: int = int(abs(latitude_deg))
    latitude_min: int = int(latitude_min)
    latitude_sec: float = round(latitude_sec, output_precision)

    longitude_heading: str = "W" if longitude_deg < 0 else "E"
    longitude_deg: int = int(abs(longitude_deg))
    longitude_min: int = int(longitude_min)
    longitude_sec: float = round(longitude_sec, output_precision)

    return (
        latitude_deg,
        latitude_min,
        latitude_sec,
        latitude_heading,
        longitude_deg,
        longitude_min,
        longitude_sec,
        longitude_heading,
    )


def convert_dms_to_latlon(
    latitude_deg: float,
    latitude_min: float,
    latitude_sec: float,
    latitude_heading: str,
    longitude_deg: float,
    longitude_min: float,
    longitude_sec: float,
    longitude_heading: str,
):
    """
    Convert DMS (Degrees, Minutes, Seconds) coordinates to
    latitude / longitude coordinates

    Parameters
    ==========
    latitude_deg: 'int'
        latitude degrees for the given set of lat/lon coordinates
    latitude_min: 'int'
        latitude minutes for the given set of lat/lon coordinates
    latitude_sec: 'int'
        latitude seconds for the given set of lat/lon coordinates
    latitude_heading: 'str'
        latitude heading ('N','S') for the given set of
        lat/lon coordinates
    longitude_deg: 'int'
        longitude_deg degrees for the given set of lat/lon coordinates
    longitude_min: 'int'
        longitude minutes for the given set of lat/lon coordinates
    longitude_sec: 'int'
        longitude seconds for the given set of lat/lon coordinates
    longitude_heading: 'str'
        longitude_deg heading ('E','W') for the given set of
        lat/lon coordinates

    Returns
    =======
    latitude : 'float'
        Latitude value
    longitude : 'float'
        Longitude value
    """

    latitude_heading = latitude_heading.upper()
    longitude_heading = longitude_heading.upper()

    assert latitude_heading in ["N", "S"]
    assert longitude_heading in ["E", "W"]

    latitude = latitude_deg + latitude_min / 60 + latitude_sec / (60 * 60)
    longitude = longitude_deg + longitude_min / 60 + longitude_sec / (60 * 60)

    latitude: float = latitude if latitude_heading == "N" else -latitude
    longitude: float = longitude if longitude_heading == "E" else -longitude

    return latitude, longitude


def Haversine(
    latitude1: float,
    longitude1: float,
    latitude2: float,
    longitude2: float,
    units: str = "metric",
):
    """
    Calculate distance between two points (degrees)
    using the Haversine formula

    Parameters
    ==========
    latitude1 : 'float'
        Latitude value point 1
    longitude1 : 'float'
        Longitude value point 1
    latitude2 : 'float'
        Latitude value point 2
    longitude2 : 'float'
        Longitude value point 2
    units: 'str'
        Can either be 'metric' or 'imperial'

    Returns
    =======
    distance : 'float'
        distance between the given coordinates in km or miles
        (dependent on requested 'units' parameter)
    bearing: 'float'
        bearing in degrees
    heading: 'str'
        human-readable bearing value (e.g. 'N','SSW' etc)
    """

    units = units.lower()
    assert units in ["imperial", "metric"]

    headings = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]

    # convert decimal degrees to radians
    longitude1, latitude1, longitude2, latitude2 = map(
        radians, [longitude1, latitude1, longitude2, latitude2]
    )

    # Calculate distance in km
    dlon = longitude2 - longitude1
    dlat = latitude2 - latitude1
    a = sin(dlat / 2) ** 2 + cos(latitude1) * cos(latitude2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))

    # Earth radius in km
    r = 6371
    distance = c * r

    # change to miles if user has requested imperial system
    if units == "imperial":
        distance *= 0.621371

    bearing = atan2(
        sin(longitude2 - longitude1) * cos(latitude2),
        cos(latitude1) * sin(latitude2)
        - sin(latitude1) * cos(latitude2) * cos(longitude2 - longitude1),
    )
    bearing = degrees(bearing)
    bearing = (bearing + 360) % 360

    pos = round(bearing / (360.0 / len(headings)))
    heading = headings[pos % len(headings)]

    return distance, bearing, heading


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(module)s -%(levelname)s- %(message)s')

    logging.debug(convert_latlon_to_utm(48, -122))
    logging.debug(convert_utm_to_latlon(10, "U", 574595, 5316784))

    logging.debug(convert_latlon_to_maidenhead(51.838720, 08.326819))
    logging.debug(convert_maidenhead_to_latlon("JO41du91"))

    logging.debug(convert_latlon_to_mgrs(51.838720, 08.326819))
    logging.debug(convert_mgrs_to_latlon("32UMC5362043315"))

    logging.debug(convert_latlon_to_dms(51.838720, 08.326819))
    logging.debug(convert_dms_to_latlon(48, 0, 0, "N", 122, 0, 0, "W"))

    logging.debug(Haversine(51.8458575, 8.2997425, 51.96564, 9.79817, "metric"))
