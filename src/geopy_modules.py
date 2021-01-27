#
# Multi-Purpose APRS Daemon: Geopy modules
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: uses Geopy /Nominatim in order to translate e.g. city/street/address
# to lat/lon and vice versa
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

from iso3166 import countries
from geopy.geocoders import Nominatim
import us
import logging
import mpad_config
import requests
import random
import time


def get_geocode_geopy_data(query_data: dict, language: str = "en"):
    """
    Issue a GeoPy 'geocode' request (e.g. qyery for an address,
    zip code etc) and return lat/lon to the user
    ==========
    query_data : 'dict'
        dictionary (geopy syntax) which contains the desired geopy query
    language: 'str'
        iso3166-2 language code

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
    geolocator = Nominatim(user_agent=mpad_config.mpad_default_user_agent)

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

    Returns
    =======
    success: 'bool'
        True if query was successful
    response_data: 'dict'
        Response dict with city, country, ...
    """

    city = country = zipcode = state = street = street_number = county = None

    # Geopy Nominatim user agent
    geolocator = Nominatim(user_agent=mpad_config.mpad_default_user_agent)

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


def get_osm_special_phrase_data(
    latitude: float,
    longitude: float,
    special_phrase: str,
    number_of_results: int = 1,
):
    """
    Get human-readable address data for a lat/lon combination
    ==========
    latitude: 'float'
        User's latitude cooordinates
    longitude: 'float'
        User's longitude coordinates
    special_phrase: 'str'
        One (1) entry from the list of valid OSM special
        special phrases that we are going to send to OSM.
        https://wiki.openstreetmap.org/wiki/Nominatim/Special_Phrases/EN
        We do not perform any validation here but send the string 'as is'
    number_of_results: 'int'
        if OSM provides more than one result, we return a maximum of n results
        back to the user. The actual number of results depends on the outcome
        of the OSM query and can even be zero if no entries were found

    Returns
    =======
    success: 'bool'
        True if at least one entry was found and added to the output list
    special_phrase_results: 'List'
        Contains the data that we have received from OSM
    """
    special_phrase_results = []

    headers = {"User-Agent": mpad_config.mpad_default_user_agent}
    success = False
    resp = None

    "https://nominatim.openstreetmap.org/search?format=jsonv2&q=fuel%20near%2051.82467,9.451&limit=1"

    try:
        resp = requests.get(
            f"https://nominatim.openstreetmap.org/search?format=jsonv2&q={special_phrase}%20near%20{latitude},{longitude}&limit={number_of_results}",
            headers=headers,
        )
    except:
        resp = None
    if resp:
        if resp.status_code == 200:
            json_content = resp.json()
            # We may have more than one result, so let's iterate
            for element in json_content:
                osm_type = osm_id = None
                if "osm_type" in element:
                    osm_type = element["osm_type"]
                if "osm_id" in element:
                    osm_id = element["osm_id"]

                # build the OSM detail query
                # see https://nominatim.org/release-docs/latest/api/Lookup/
                osm_type = osm_type.lower()
                if osm_type == "way":
                    osm_query_id = f"W{osm_id}"
                elif osm_type == "relation":
                    osm_type = f"R{osm_id}"
                else:
                    osm_type = f"N{osm_id}"  # assume that "Node"

                # https://operations.osmfoundation.org/policies/nominatim/ requires us
                # to obey to its usage policy. We need to make sure that between each
                # request to OSM that there will be a random sleep period between 1001
                # and 2000 msec
                sleep_time = random.uniform(1.2, 3)
                time.sleep(sleep_time)

                # Now perform the detail query
                try:
                    resp = requests.get(
                        f"https://nominatim.openstreetmap.org/lookup?osm_ids={osm_type}&format=json",
                        headers=headers,
                    )
                except:
                    resp = None
                if resp:
                    if resp.status_code == 200:
                        json_content = resp.json()
                        for element in json_content:
                            house_number = road = town = postcode = amenity = None
                            latitude = longitude = 0.0

                            if "lat" in element:
                                latitude = element["lat"]
                                try:
                                    latitude = float(latitude)
                                except ValueError:
                                    latitude = 0.0
                            if "lon" in element:
                                longitude = element["lon"]
                                try:
                                    longitude = float(longitude)
                                except ValueError:
                                    longitude = 0.0

                            if "address" in element:
                                address_body = element["address"]
                                if "house_number" in address_body:
                                    house_number = address_body["house_number"]
                                if "amenity" in address_body:
                                    amenity = address_body["amenity"]
                                if "road" in address_body:
                                    road = address_body["road"]
                                if "town" in address_body:
                                    town = address_body["town"]
                                if "postcode" in address_body:
                                    postcode = address_body["postcode"]
                                special_phrase_entry = {
                                    "amenity": amenity,
                                    "house_number": house_number,
                                    "road": road,
                                    "town": town,
                                    "postcode": postcode,
                                    "latitude": latitude,
                                    "longitude": longitude,
                                }
                                special_phrase_results.append(special_phrase_entry)
                                success = True
    return success, special_phrase_results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
    )
    logger = logging.getLogger(__name__)

    #    logger.info(get_reverse_geopy_data(latitude=37.7790262, longitude=-122.4199061))
    #    city = "Mountain View"
    #    state = "CA"
    #    country = "US"
    #    geopy_query = {"city": city, "state": state, "country": country}
    #    logger.info(get_geocode_geopy_data(query_data=geopy_query))

    logger.info(
        get_osm_special_phrase_data(
            latitude=51.82467,
            longitude=9.451,
            special_phrase="fuel",
            number_of_results=3,
        )
    )
