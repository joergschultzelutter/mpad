#
# Multi-Purpose APRS Daemon: Geopy modules
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: uses Geopy in order to translate e.g. city/street/address to lat/lon
# and vice versa
#

from iso3166 import countries
from geopy.geocoders import Nominatim
import us
import logging


def get_geocode_geopy_data(
    query_data: dict, language: str = "en", user_agent: str = "MultiPurposeAPRSDaemon"
):
    """
    Issue a GeoPy 'geocode' request (e.g. qyery for an address,
    zip code etc) and return lat/lon to the user
    ==========
    query_data : 'dict'
        dictionary (geopy syntax) which contains the desired geopy query
    language: 'str'
        iso3166-2 language code
    user_agent: 'str'
        User agent for the Geopy query

    Returns
    =======
    success: 'bool'
        True if query was successful
    latitude: 'float'
        Latitude for requested query (0.0 if entry was not found)
    longitude: 'float'
        Longitude for requested query (0.0 if entry was not found)
    """
    # Geopy Nominatim user agent
    geolocator = Nominatim(user_agent=user_agent)

    success = False
    latitude = longitude = 0.0
    location = None
    try:
        location = geolocator.geocode(query_data, exactly_one=True, language=language)
    except:
        location = None
    if location:
        latitude = location.latitude
        longitude = location.longitude
        success = True
    return success, latitude, longitude


def get_reverse_geopy_data(
    latitude: float,
    longitude: float,
    language: str = "en",
    user_agent: str = "MultiPurposeAPRSDaemon",
):
    """
    Get human-readable address data for a lat/lon combination
    ==========
    latitude: 'float'
        Latitude
    longitude: 'float'
        Longitude
    language: 'str'
        iso3166-2 language code
    user_agent: 'str'
        User agent for the Geopy query

    Returns
    =======
    success: 'bool'
        True if query was successful
    response_data: 'dict'
        Response dict with city, country, ...
    """

    city = country = zipcode = state = street = street_number = county = None

    # Geopy Nominatim user agent
    geolocator = Nominatim(user_agent=user_agent)

    success = False
    try:
        # Lookup with zoom level 18 (building)
        location = geolocator.reverse(
            f"{latitude} {longitude}", language=language, zoom=18
        )
    except TypeError:
        location = None
    if location:
        if "address" in location.raw:
            success = True
            if "city" in location.raw["address"]:
                city = location.raw["address"]["city"]
            if "town" in location.raw["address"]:
                city = location.raw["address"]["town"]
            if "village" in location.raw["address"]:
                city = location.raw["address"]["village"]
            if "hamlet" in location.raw["address"]:
                city = location.raw["address"]["hamlet"]
            if "county" in location.raw["address"]:
                county = location.raw["address"]["county"]
            if "country_code" in location.raw["address"]:
                country = location.raw["address"]["country_code"]
                country = country.upper()
            if "postcode" in location.raw["address"]:
                zipcode = location.raw["address"]["postcode"]
            if "road" in location.raw["address"]:
                street = location.raw["address"]["road"]
            if "house_number" in location.raw["address"]:
                street_number = location.raw["address"]["house_number"]
            if "state" in location.raw["address"]:
                state = location.raw["address"]["state"]
                if country == "US":  # State is returned in full; shorten it
                    try:
                        x = us.states.lookup(state)
                        state = x.abbr
                    except:
                        state = None
            if not city:
                if "man_made" in location.raw["address"]:
                    city = location.raw["address"]["man_made"]

    response_data = {
        "city": city,
        "state": state,
        "county": county,
        "country": country,
        "zipcode": zipcode,
        "street": street,
        "street_number": street_number,
    }

    return success, response_data


def validate_country(country: str):
    """
    Get human-readable address data for a lat/lon combination
    ==========
    country: 'str'
        Potential ISO3166-a2 country code

    Returns
    =======
    success: 'bool'
        True if country exists
    """
    success: bool = True
    try:
        countries.get(country)
    except KeyError as e:
        success = False
    return success


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(module)s -%(levelname)s- %(message)s')
    logger = logging.getLogger(__name__)

    logger.debug(get_reverse_geopy_data(37.7790262, -122.4199061))
