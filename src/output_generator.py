#
# Multi-Purpose APRS Daemon: Output generator
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: Generate the output that is to be sent to the user
# (based on the successfully parsed content's input message)
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

from openweathermap_modules import (
    get_daily_weather_from_openweathermapdotorg,
    parse_daily_weather_from_openweathermapdotorg,
)
from cwop_modules import (
    get_cwop_findu,
    get_nearest_cwop_findu,
)

from geopy_modules import get_osm_special_phrase_data

from utility_modules import make_pretty_aprs_messages, read_program_config
from airport_data_modules import get_metar_data
from skyfield_modules import get_sun_moon_rise_set_for_latlon
from geo_conversion_modules import (
    convert_latlon_to_maidenhead,
    convert_latlon_to_mgrs,
    convert_latlon_to_utm,
    convert_latlon_to_dms,
    haversine,
)
from dapnet_modules import send_dapnet_message

from repeater_modules import get_nearest_repeater

import datetime
import logging
import math

###
# Help text that the user receives in case he has requested help
help_text_array = [
    "(default=wx for pos of sending callsign). Position commands:",
    "city,state;country OR city,state OR city;country OR zip;country OR",
    "zip with/wo country OR grid|mh+4..6 char OR lat/lon OR callsign",
    "time: mon..sun(day),today,tomorrow.Extra: mtr|metric imp|imperial",
]


def create_cwop_content(cwop_dict: dict):
    """
    Function for generating the content from CWOP data
    (we need to do this for the two avalilable use cases,
    cwop_by_lat_lon and cwop_by_id. However, the data that we will
    send to the user is the same.

    Parameters
    ==========
    cwop_dict: 'dict'
        Response dictionary from MPAD's CWOP functions.

    Returns
    =======
    output_list: 'list'
        List which contains the formatted output of the data that we are going
        to send back to the user
    """

    # Get the values from the dictionary. All
    # values with the exception of 'time' are strings
    # and are processed as is for simplicity reasons
    cwop_id = cwop_dict["cwop_id"]
    time = cwop_dict["time"]
    temp = cwop_dict["temp"]
    temp_uom = cwop_dict["temp_uom"]
    wind_direction = cwop_dict["wind_direction"]
    wind_speed = cwop_dict["wind_speed"]
    wind_gust = cwop_dict["wind_gust"]
    speedgust_uom = cwop_dict["speedgust_uom"]
    rain_1h = cwop_dict["rain_1h"]
    rain_24h = cwop_dict["rain_24h"]
    rain_mn = cwop_dict["rain_mn"]
    rain_uom = cwop_dict["rain_uom"]
    humidity = cwop_dict["humidity"]
    humidity_uom = cwop_dict["humidity_uom"]
    air_pressure = cwop_dict["air_pressure"]
    air_pressure_uom = cwop_dict["air_pressure_uom"]

    # shorten the output date if there is none
    # reminder: these are strings
    if rain_1h == "0.00":
        rain_1h = "0.0"
    if rain_24h == "0.00":
        rain_24h = "0.0"
    if rain_mn == "0.00":
        rain_mn = "0.0"

    # Prepare the output content. Special use case:
    # We need to declare a dummy list here as some -or all-
    # of these elements are missing (and we don't know which ones will that be)
    # Therefore, we cannot rely on make_pretty_aprs_messages returning a list to
    # us at all times.
    output_list = []
    # we ignore the 'human_readable_message' variable at this point
    # as it did not yet contain the respective CWOP ID
    if cwop_id:
        output_list = make_pretty_aprs_messages(
            message_to_add=f"CWOP {cwop_id}", destination_list=output_list
        )
    if time:
        output_list = make_pretty_aprs_messages(
            message_to_add=datetime.datetime.strftime(time, "%d-%b-%y"),
            destination_list=output_list,
        )
    if temp:
        output_list = make_pretty_aprs_messages(
            message_to_add=f"{temp}{temp_uom}", destination_list=output_list
        )
    if wind_direction:
        output_list = make_pretty_aprs_messages(
            message_to_add=f"{wind_direction}deg", destination_list=output_list
        )
    if wind_speed:
        output_list = make_pretty_aprs_messages(
            message_to_add=f"Spd {wind_speed}{speedgust_uom}",
            destination_list=output_list,
        )
    if wind_gust:
        output_list = make_pretty_aprs_messages(
            message_to_add=f"Gust {wind_gust}{speedgust_uom}",
            destination_list=output_list,
        )
    if humidity:
        output_list = make_pretty_aprs_messages(
            message_to_add=f"Hum {humidity}{humidity_uom}",
            destination_list=output_list,
        )
    if air_pressure:
        output_list = make_pretty_aprs_messages(
            message_to_add=f"Pres {air_pressure}{air_pressure_uom}",
            destination_list=output_list,
        )
    if rain_1h:
        output_list = make_pretty_aprs_messages(
            message_to_add=f"Rain({rain_uom}) 1h={rain_1h}",
            destination_list=output_list,
        )
    if rain_24h:
        output_list = make_pretty_aprs_messages(
            message_to_add=f", 24h={rain_24h}",
            destination_list=output_list,
            add_sep=False,
        )
    if rain_mn:
        output_list = make_pretty_aprs_messages(
            message_to_add=f", mn={rain_mn}",
            destination_list=output_list,
            add_sep=False,
        )

    return output_list


def generate_output_message(response_parameters: dict):
    """
    Evaluate the input parser's output and gather the data the user
    wants to receive. If this function is called, then the parser
    process was successful - we no longer need to check the status

    Parameters
    ==========
    response_parameters: 'dict'
        Dictionary of the data from the input processor's analysis on the user's data

    Returns
    =======
    success: 'bool'
        True if operation was successful. Will only be false in case of a
        fatal error as we need to send something back to the user (even
        if that message is a mere error text)
    output_message: 'list'
        List, containing the message text(s) that we will send to the user
        This is plain text list without APRS message ID's
    """

    # Start the process by extracting the action parameter
    # Read: What is it that the user wants from us?

    what = response_parameters["what"]

    # Now evaluate the action command call an associated subroutine
    # which will extract the relevant information from the input parser's
    # response parameters and then build the final outgoing message.
    #
    # each of these functions will return:
    # -a boolean status which is a general indicator if something was wrong
    # -a list object which contains the ready-to-send messages to the end user
    if what == "wx":
        success, output_list = generate_output_message_wx(
            response_parameters=response_parameters,
        )
    elif what == "metar":
        success, output_list = generate_output_message_metar(
            response_parameters=response_parameters
        )
    elif what == "help":
        success, output_list = generate_output_message_help()
    elif what == "cwop_by_latlon":
        success, output_list = generate_output_message_cwop_by_latlon(
            response_parameters=response_parameters
        )
    elif what == "cwop_by_cwop_id":
        success, output_list = generate_output_message_cwop_by_cwop_id(
            response_parameters=response_parameters
        )
    elif what == "riseset":
        success, output_list = generate_output_message_riseset(
            response_parameters=response_parameters
        )
    #    elif what == "satpass":
    #        success, output_list = generate_output_message_satpass(
    #            response_parameters=response_parameters
    #        )
    elif what == "repeater":
        success, output_list = generate_output_message_repeater(
            response_parameters=response_parameters
        )
    elif what == "whereis":
        success, output_list = generate_output_message_whereis(
            response_parameters=response_parameters
        )
    elif what == "osm_special_phrase":
        success, output_list = generate_output_message_osm_special_phrase(
            response_parameters=response_parameters
        )
    elif what == "dapnet" or what == "dapnethp":
        success, output_list = generate_output_message_dapnet(
            response_parameters=response_parameters
        )
    else:
        success = False
        output_list = [
            "Output parser has encountered an unknown action command",
        ]
        logger = logging.getLogger(__name__)
        logger.info(
            f"Unable to generate output message; unknown 'what' command '{what}': {response_parameters}"
        )

    return success, output_list


def generate_output_message_wx(response_parameters: dict):
    """
    Action keyword "wx": generate the wx report for the requested coordinates

    Parameters
    ==========
    response_parameters: 'dict'
        Dictionary of the data from the input processor's analysis on the user's data

    Returns
    =======
    success: 'bool'
        True if operation was successful. Will only be false in case of a
        fatal error as we need to send something back to the user (even
        if that message is a mere error text)
    output_list: 'list'
        List, containing the message text(s) that we will send to the user
        This is plain text list without APRS message ID's
    """
    latitude = response_parameters["latitude"]
    longitude = response_parameters["longitude"]
    units = response_parameters["units"]
    when = response_parameters["when"]
    when_daytime = response_parameters["when_daytime"]
    date_offset = response_parameters["date_offset"]
    hour_offset = response_parameters["hour_offset"]
    language = response_parameters["language"]
    altitude = response_parameters["altitude"]
    human_readable_message = response_parameters["human_readable_message"]
    openweathermapdotorg_api_key = response_parameters["openweathermapdotorg_api_key"]

    # populate the correct offset & mode , dependent on
    # what the user wants (daily, hourly or current wx data)
    offset = date_offset
    access_mode = "day"
    if when == "hour":
        offset = hour_offset
        access_mode = "hour"
    if when == "now":
        offset = -1
        access_mode = "current"

    success, myweather, tz_offset, tz = get_daily_weather_from_openweathermapdotorg(
        latitude=latitude,
        longitude=longitude,
        units=units,
        offset=offset,
        openweathermap_api_key=openweathermapdotorg_api_key,
        language=language,
        access_mode=access_mode,
    )
    if success:
        if when == "hour":
            human_readable_message = f"in {offset}h " + human_readable_message
        elif when == "now":
            human_readable_message = (
                datetime.datetime.strftime(datetime.datetime.utcnow(), "%H:%M")
                + "UTC "
                + human_readable_message
            )

        output_list = parse_daily_weather_from_openweathermapdotorg(
            myweather, units, human_readable_message, when, when_daytime
        )

        # Add altitude from aprs.fi if present
        if altitude:
            altitude_uom = "m"
            altitude_value = round(altitude)

            if units == "imperial":
                altitude_uom = "ft"
                altitude_value = round(altitude * 3.28084)  # convert m to feet

            human_readable_address = f"Alt:{altitude_value}{altitude_uom}"
            output_list = make_pretty_aprs_messages(
                message_to_add=human_readable_address,
                destination_list=output_list,
            )
        return success, output_list
    else:
        success = True
        output_list = make_pretty_aprs_messages(
            message_to_add=f"{human_readable_message} - unable to get wx"
        )
        return success, output_list


def generate_output_message_metar(response_parameters: dict):
    """
    Generate a metar report for a specific airport (ICAO code)

    Parameters
    ==========
    response_parameters: 'dict'
        Dictionary of the data from the input processor's analysis on the user's data

    Returns
    =======
    success: 'bool'
        True if operation was successful. Will only be false in case of a
        fatal error as we need to send something back to the user (even
        if that message is a mere error text)
    output_message: 'list'
        List, containing the message text(s) that we will send to the user
        This is plain text list without APRS message ID's
    """
    #
    # METAR data?
    # At this point in time, we know for sure that the airport is METAR
    # capable. If we are still unable to retrieve that METAR data, then
    # output an error message to the user. The input parser's
    # human_readable_message field is ignored in order to
    # shorten the user message
    #
    icao_code = response_parameters["icao"]
    success, metar_response = get_metar_data(icao_code=icao_code)
    if success:
        output_list = make_pretty_aprs_messages(
            message_to_add=metar_response,
        )
        return success, output_list
    else:
        success = True
        output_list = make_pretty_aprs_messages(
            message_to_add=f"No METAR data present for {icao_code}"
        )
        return success, output_list


def generate_output_message_help():
    """
    Return instructions to the user

    Parameters
    ==========

    Returns
    =======
    success: 'bool'
        always True
    output_message: 'list'
        List, containing the message text(s) that we will send to the user
        This is plain text list without APRS message ID's
    """
    success = True
    output_list = help_text_array
    return success, output_list


def generate_output_message_satpass(response_parameters: dict):
    """
    Generate the satellite prediction data report

    Parameters
    ==========
    response_parameters: 'dict'
        Dictionary of the data from the input processor's analysis on the user's data

    Returns
    =======
    success: 'bool'
        True if operation was successful. Will only be false in case of a
        fatal error as we need to send something back to the user (even
        if that message is a mere error text)
    output_message: 'list'
        List, containing the message text(s) that we will send to the user
        This is plain text list without APRS message ID's
    """
    satellite = response_parameters["satellite"]
    latitude = response_parameters["latitude"]
    longitude = response_parameters["longitude"]
    altitude = response_parameters["altitude"]
    when_daytime = response_parameters["when_daytime"]
    when = response_parameters["when"]
    human_readable_message = response_parameters["human_readable_message"]

    output_list = ["Currently not implemented"]
    success = True
    return success, output_list


def generate_output_message_cwop_by_latlon(response_parameters: dict):
    """
    Generate a CWOP report for a specific lat/lon coordinates set

    Parameters
    ==========
    response_parameters: 'dict'
        Dictionary of the data from the input processor's analysis on the user's data

    Returns
    =======
    success: 'bool'
        True if operation was successful. Will only be false in case of a
        fatal error as we need to send something back to the user (even
        if that message is a mere error text)
    output_message: 'list'
        List, containing the message text(s) that we will send to the user
        This is plain text list without APRS message ID's
    """
    latitude = response_parameters["latitude"]
    longitude = response_parameters["longitude"]
    units = response_parameters["units"]
    message_callsign = response_parameters["message_callsign"]
    success, cwop_dict = get_nearest_cwop_findu(
        latitude=latitude, longitude=longitude, units=units
    )
    if success:
        # extract the response fields from the parsed message content
        output_list = create_cwop_content(cwop_dict)
        success = True
        return success, output_list
    else:
        output_list = make_pretty_aprs_messages(
            message_to_add=f"Unable to get nearest CWOP for {message_callsign}"
        )
        success = True
        return success, output_list


def generate_output_message_cwop_by_cwop_id(response_parameters: dict):
    """
    Generate a CWOP report for a specific cwop station

    Parameters
    ==========
    response_parameters: 'dict'
        Dictionary of the data from the input processor's analysis on the user's data

    Returns
    =======
    success: 'bool'
        True if operation was successful. Will only be false in case of a
        fatal error as we need to send something back to the user (even
        if that message is a mere error text)
    output_message: 'list'
        List, containing the message text(s) that we will send to the user
        This is plain text list without APRS message ID's
    """
    cwop_id = response_parameters["cwop_id"]
    units = response_parameters["units"]
    success, cwop_dict = get_cwop_findu(cwop_id=cwop_id, units=units)
    if success:
        # extract the response fields from the parsed message content
        output_list = create_cwop_content(cwop_dict)
        success = True
        return success, output_list
    else:
        output_list = make_pretty_aprs_messages(
            message_to_add=f"Unable to get CWOP for ID {cwop_id}"
        )
        success = True
        return success, output_list


def generate_output_message_riseset(response_parameters: dict):
    """
    Get sunrise/sunset and moonrise/moonset for latitude/longitude

    Parameters
    ==========
    response_parameters: 'dict'
        Dictionary of the data from the input processor's analysis on the user's data

    Returns
    =======
    success: 'bool'
        True if operation was successful. Will only be false in case of a
        fatal error as we need to send something back to the user (even
        if that message is a mere error text)
    output_message: 'list'
        List, containing the message text(s) that we will send to the user
        This is plain text list without APRS message ID's
    """
    latitude = response_parameters["latitude"]
    longitude = response_parameters["longitude"]
    altitude = response_parameters["altitude"]
    date_offset = response_parameters["date_offset"]
    human_readable_message = response_parameters["human_readable_message"]

    requested_date = datetime.datetime.now() + datetime.timedelta(days=date_offset)

    sunrise, sunset, moonrise, moonset = get_sun_moon_rise_set_for_latlon(
        latitude=latitude,
        longitude=longitude,
        requested_date=requested_date,
        elevation=altitude,
    )
    output_list = make_pretty_aprs_messages(message_to_add=human_readable_message)
    output_list = make_pretty_aprs_messages(
        message_to_add=datetime.datetime.strftime(requested_date, "%d-%b"),
        destination_list=output_list,
    )
    output_list = make_pretty_aprs_messages(
        message_to_add="GMT sun_rs", destination_list=output_list
    )
    output_list = make_pretty_aprs_messages(
        message_to_add=datetime.datetime.strftime(sunrise, "%H:%M"),
        destination_list=output_list,
    )
    output_list = make_pretty_aprs_messages(
        message_to_add=datetime.datetime.strftime(sunset, "-%H:%M"),
        destination_list=output_list,
        add_sep=False,
    )
    output_list = make_pretty_aprs_messages(
        message_to_add="mn_sr", destination_list=output_list
    )
    output_list = make_pretty_aprs_messages(
        message_to_add=datetime.datetime.strftime(moonset, "%H:%M"),
        destination_list=output_list,
    )
    output_list = make_pretty_aprs_messages(
        message_to_add=datetime.datetime.strftime(moonrise, "-%H:%M"),
        destination_list=output_list,
        add_sep=False,
    )
    success = True
    return success, output_list


def generate_output_message_dapnet(response_parameters: dict):
    """
    Forward a message to DAPNET and return the status to the user

    Parameters
    ==========
    response_parameters: 'dict'
        Dictionary of the data from the input processor's analysis on the user's data

    Returns
    =======
    success: 'bool'
        True if operation was successful. Will only be false in case of a
        fatal error as we need to send something back to the user (even
        if that message is a mere error text)
    output_message: 'list'
        List, containing the message text(s) that we will send to the user
        This is plain text list without APRS message ID's
    """
    message_callsign = response_parameters["message_callsign"]
    users_callsign = response_parameters["users_callsign"]
    dapnet_message = response_parameters["dapnet_message"]
    dapnet_login_callsign = response_parameters["dapnet_login_callsign"]
    dapnet_login_passcode = response_parameters["dapnet_login_passcode"]

    # Check if the user wants to send a high priority call
    what = response_parameters["what"]
    dapnet_priority_call = False
    if what == "dapnethp":
        dapnet_priority_call = True

    success, response = send_dapnet_message(
        from_callsign=users_callsign,
        to_callsign=message_callsign,
        message=dapnet_message,
        dapnet_login_callsign=dapnet_login_callsign,
        dapnet_login_passcode=dapnet_login_passcode,
        dapnet_high_priority_message=dapnet_priority_call,
    )
    output_list = make_pretty_aprs_messages(message_to_add=response)

    success = True  # Always 'True' as we also return error messages to the user
    return success, output_list


def generate_output_message_whereis(response_parameters: dict):
    """
    Generate a 'whereis' output (coords, address etc) for a specific lat/lon

    Parameters
    ==========
    response_parameters: 'dict'
        Dictionary of the data from the input processor's analysis on the user's data

    Returns
    =======
    success: 'bool'
        True if operation was successful. Will only be false in case of a
        fatal error as we need to send something back to the user (even
        if that message is a mere error text)
    output_message: 'list'
        List, containing the message text(s) that we will send to the user
        This is plain text list without APRS message ID's
    """

    # This variable will be set to true if lat/lon differ from
    # user's lat/lon, meaning that these callsigns might represent
    # different identities (based on their positions)
    # False = we run the 'whereami' mode
    # True = we run the 'whereis' mode
    _whereis_mode = False

    # https://en.wikipedia.org/wiki/Address.
    # https://wiki.openstreetmap.org/wiki/Name_finder/Address_format
    # This is a list of countries where the
    # street number has to be listed before the street name.
    # example:
    # US: 555 Test Way
    # DE: Test Way 555 (default format)
    #
    street_number_precedes_street = [
        "AU",
        "CA",
        "FR",
        "HK",
        "IE",
        "IN",
        "IL",
        "JP",
        "LU",
        "MY",
        "NZ",
        "OM",
        "PH",
        "SA",
        "SG",
        "LK",
        "TW",
        "TH",
        "US",
        "GB",
        "UK",
    ]

    latitude = response_parameters["latitude"]
    longitude = response_parameters["longitude"]
    altitude = response_parameters["altitude"]
    human_readable_message = response_parameters["human_readable_message"]
    users_latitude = response_parameters["users_latitude"]
    users_longitude = response_parameters["users_longitude"]
    units = response_parameters["units"]
    lasttime = response_parameters["lasttime"]
    if not isinstance(lasttime, datetime.datetime):
        lasttime = datetime.datetime.min

    # all of the following data was reverse-lookup'ed and can be 'None'
    city = response_parameters["city"]
    state = response_parameters["state"]
    zipcode = response_parameters["zipcode"]
    country = response_parameters["country"]
    county = response_parameters["county"]
    street = response_parameters["street"]
    street_number = response_parameters["street_number"]

    output_list = make_pretty_aprs_messages(message_to_add=human_readable_message)

    grid = convert_latlon_to_maidenhead(latitude=latitude, longitude=longitude)
    output_list = make_pretty_aprs_messages(
        message_to_add=f"Grid {grid}", destination_list=output_list
    )

    (
        lat_deg,
        lat_min,
        lat_sec,
        lat_hdg,
        lon_deg,
        lon_min,
        lon_sec,
        lon_hdg,
    ) = convert_latlon_to_dms(latitude=latitude, longitude=longitude)

    human_readable_address = (
        f"DMS {lat_hdg}{lat_deg:02d}.{lat_min:02d}'{round(lat_sec,1):02.1f}"
    )
    human_readable_address += (
        f"/{lon_hdg}{lon_deg:02d}.{lon_min:02d}'{round(lon_sec,1):02.1f}"
    )

    output_list = make_pretty_aprs_messages(
        message_to_add=human_readable_address,
        destination_list=output_list,
    )

    distance_string = bearing_string = direction_string = None

    # calculate distance, heading and bearing if message call sign position
    # differs from our own call sign's position
    if latitude != users_latitude and longitude != users_longitude:

        # We have different identities and switch from "whereami" mode
        # to the "whereis" mode where we will also calculate the distance,
        # heading and direction between these two positions
        _whereis_mode = True

        # Calculate distance, bearing and heading
        # latitude1/longitude1 = the user's current position
        # latitude2/longitude2 = the desired target position
        distance, bearing, heading = haversine(
            latitude1=users_latitude,
            longitude1=users_longitude,
            latitude2=latitude,
            longitude2=longitude,
            units=units,
        )
        distance_uom = "km"
        if units == "imperial":
            distance_uom = "mi"

        output_list = make_pretty_aprs_messages(
            message_to_add=f"Dst {math.ceil(distance)} {distance_uom}",
            destination_list=output_list,
        )

        output_list = make_pretty_aprs_messages(
            message_to_add=f"Brg {round(bearing)}deg", destination_list=output_list
        )

        output_list = make_pretty_aprs_messages(
            message_to_add=f"{heading}", destination_list=output_list
        )

    if altitude:
        altitude_uom = "m"
        altitude_value = round(altitude)

        if units == "imperial":
            altitude_uom = "ft"
            altitude_value = round(altitude * 3.28084)  # convert m to feet

        human_readable_address = f"Alt {altitude_value}{altitude_uom}"
        output_list = make_pretty_aprs_messages(
            message_to_add=human_readable_address,
            destination_list=output_list,
        )

    zone_number, zone_letter, easting, northing = convert_latlon_to_utm(
        latitude=latitude, longitude=longitude
    )
    output_list = make_pretty_aprs_messages(
        message_to_add=f"UTM {zone_number}{zone_letter} {easting} {northing}",
        destination_list=output_list,
    )

    mgrs = convert_latlon_to_mgrs(latitude=latitude, longitude=longitude)
    output_list = make_pretty_aprs_messages(
        message_to_add=f"MGRS {mgrs}", destination_list=output_list
    )

    output_list = make_pretty_aprs_messages(
        message_to_add=f"LatLon {latitude}/{longitude}",
        destination_list=output_list,
    )

    human_readable_address = None
    if city:
        human_readable_address = city
        if zipcode:
            human_readable_address += f", {zipcode}"
        if country:
            human_readable_address += f", {country}"
    else:
        if county:
            human_readable_address = county
        if zipcode:
            human_readable_address += f", {zipcode}"
        if country:
            human_readable_address += f", {country}"

    if human_readable_address:
        output_list = make_pretty_aprs_messages(
            message_to_add=human_readable_address, destination_list=output_list
        )

    human_readable_address = None
    if street:
        human_readable_address = street
        if street_number:
            # per https://en.wikipedia.org/wiki/Address, we try to honor the native format
            # for those countries who list the street number before the street name
            if country in street_number_precedes_street:
                human_readable_address = f"{street_number} " + human_readable_address
            else:
                human_readable_address = human_readable_address + f" {street_number}"
    if human_readable_address:
        output_list = make_pretty_aprs_messages(
            message_to_add=human_readable_address, destination_list=output_list
        )

    if _whereis_mode:
        human_readable_address = None
        # Check if we have some "lasttime" information that we can provide the user with
        if lasttime is not datetime.datetime.min:
            human_readable_address = (
                f"Last heard {lasttime.strftime('%Y-%m-%d %H:%M')} UTC"
            )
            output_list = make_pretty_aprs_messages(
                message_to_add=human_readable_address, destination_list=output_list
            )

    success = True
    return success, output_list


def generate_output_message_repeater(response_parameters: dict):
    """
    Generate a 'nearest repeater' inquiry for a specific lat/lon

    Parameters
    ==========
    response_parameters: 'dict'
        Dictionary of the data from the input processor's analysis on the user's data

    Returns
    =======
    success: 'bool'
        True if operation was successful. Will only be false in case of a
        fatal error as we need to send something back to the user (even
        if that message is a mere error text)
    output_message: 'list'
        List, containing the message text(s) that we will send to the user
        This is plain text list without APRS message ID's
    """
    latitude = response_parameters["latitude"]
    longitude = response_parameters["longitude"]
    units = response_parameters["units"]
    repeater_band = response_parameters["repeater_band"]
    repeater_mode = response_parameters["repeater_mode"]
    number_of_results = response_parameters["number_of_results"]

    # Static file solution; needs dynamic refresh
    success, nearest_repeater_list = get_nearest_repeater(
        latitude=latitude,
        longitude=longitude,
        mode=repeater_mode,
        band=repeater_band,
        units=units,
        number_of_results=number_of_results,
    )
    # success = we have at least one dict entry in our list
    if success:

        number_of_actual_results = len(nearest_repeater_list)
        entry = 0

        # We need a predefined local list variable as we are going to iterate
        # multiple times through our search results
        output_list = []

        # now iterate through the dictionaries in our list
        for nearest_repeater in nearest_repeater_list:
            # Increase the output counter
            entry = entry + 1

            # now extract all entries from the dictionary
            locator = nearest_repeater["locator"]
            latitude = nearest_repeater["latitude"]
            longitude = nearest_repeater["longitude"]
            mode = nearest_repeater["mode"]
            band = nearest_repeater["band"]
            repeater_frequency = nearest_repeater["repeater_frequency"]
            repeater_shift = nearest_repeater["repeater_shift"]
            elevation = nearest_repeater["elevation"]
            comments = nearest_repeater["comments"]
            location = nearest_repeater["location"]
            callsign = nearest_repeater["callsign"]
            distance = nearest_repeater["distance"]
            distance_uom = nearest_repeater["distance_uom"]
            bearing = nearest_repeater["bearing"]
            direction = nearest_repeater["direction"]
            encode = nearest_repeater["encode"]
            decode = nearest_repeater["decode"]

            # Add an identification header (#1,#2,#3 ...)
            # if we have more than one result that we
            # have to return to the user
            if number_of_actual_results > 1:
                output_list = make_pretty_aprs_messages(
                    message_to_add=f"#{entry}", destination_list=output_list
                )

            output_list = make_pretty_aprs_messages(f"{location}", output_list)

            output_list = make_pretty_aprs_messages(
                f"Dst {distance} {distance_uom}", output_list
            )
            output_list = make_pretty_aprs_messages(
                f"{bearing} deg {direction}", output_list
            )
            # Both repeater frequency and shift are in Hz. Let's convert to MHz
            repeater_frequency = round(repeater_frequency / 1000000, 4)
            repeater_shift = round(repeater_shift / 1000000, 4)
            if repeater_shift != 0:
                output_list = make_pretty_aprs_messages(
                    f"{repeater_frequency:0.4f}{repeater_shift:+0.1f} MHz", output_list
                )
            else:
                output_list = make_pretty_aprs_messages(
                    f"{repeater_frequency:0.4f} MHz", output_list
                )

            if encode:
                output_list = make_pretty_aprs_messages(f"Enc {encode}", output_list)

            if decode:
                output_list = make_pretty_aprs_messages(f"Dec {decode}", output_list)

            # Comments can be empty
            if comments:
                output_list = make_pretty_aprs_messages(f"{comments}", output_list)
            #
            # "band' and 'mode' are only added to the outgoing message if the user
            # has NOT requested these as input parameters. We can save a few bytes per
            # message and if the user has e.g. requested c4fm on 70cm via keywords,
            # we don't need to deliver this information as part of the resulting data.
            # However, if the user has NOT requested band and/or mode, we will output
            # the data to the user so that the user knows if e.g. these values are
            # valid for c4fm, d-star, ....
            if not repeater_mode:
                output_list = make_pretty_aprs_messages(f"{mode}", output_list)
            #            if not repeater_band:
            #                output_list = make_pretty_aprs_messages(f"{band}", output_list)

            output_list = make_pretty_aprs_messages(f"{locator}", output_list)
    else:
        output_list = make_pretty_aprs_messages(
            "Cannot locate nearest repeater for your query parameter set"
        )
        success = True  # The operation failed but we still have message that we want to send to the user
    return success, output_list


def generate_output_message_osm_special_phrase(response_parameters: dict):
    """
    Get the user's desired OSM 'special phrase' query and return the content to the user

    Parameters
    ==========
    response_parameters: 'dict'
        Dictionary of the data from the input processor's analysis on the user's data

    Returns
    =======
    success: 'bool'
        True if operation was successful. Will only be false in case of a
        fatal error as we need to send something back to the user (even
        if that message is a mere error text)
    output_message: 'list'
        List, containing the message text(s) that we will send to the user
        This is plain text list without APRS message ID's
    """
    latitude = response_parameters["latitude"]
    longitude = response_parameters["longitude"]
    number_of_results = response_parameters["number_of_results"]
    osm_special_phrase = response_parameters["osm_special_phrase"]
    units = response_parameters["units"]

    success, osm_data_list = get_osm_special_phrase_data(
        latitude=latitude,
        longitude=longitude,
        special_phrase=osm_special_phrase,
        number_of_results=number_of_results,
    )

    # We need a predefined local list variable as we are going to iterate
    # multiple times through our search results
    output_list = []

    if not success:
        output_list = make_pretty_aprs_messages(
            message_to_add=f"No results for '{osm_special_phrase}' found near your pos.",
            destination_list=output_list,
        )
    else:
        entry = 0
        number_of_actual_results = len(osm_data_list)
        for element in osm_data_list:
            # msg counter
            entry = entry + 1

            osm_latitude = element["latitude"]
            osm_longitude = element["longitude"]
            house_number = element["house_number"]
            amenity = element["amenity"]
            road = element["road"]
            city = element["city"]
            postcode = element["postcode"]

            # Calculate distance, bearing and heading to the target
            # latitude1/longitude1 = the user's current position
            # latitude2/longitude2 = the desired target position
            distance, bearing, heading = haversine(
                latitude1=latitude,
                longitude1=longitude,
                latitude2=osm_latitude,
                longitude2=osm_longitude,
                units=units,
            )

            # Add an identification header (#1,#2,#3 ...)
            # if we have more than one result that we
            # have to return to the user
            if number_of_actual_results > 1:
                output_list = make_pretty_aprs_messages(
                    message_to_add=f"#{entry}", destination_list=output_list
                )

            if amenity:
                output_list = make_pretty_aprs_messages(
                    message_to_add=amenity, destination_list=output_list
                )
            if road:
                output_list = make_pretty_aprs_messages(
                    message_to_add=road, destination_list=output_list
                )
            if house_number:
                output_list = make_pretty_aprs_messages(
                    message_to_add=house_number, destination_list=output_list
                )
            if city:
                output_list = make_pretty_aprs_messages(
                    message_to_add=city, destination_list=output_list
                )

            dst_uom = "km"
            if units == "imperial":
                dst_uom = "mi"

            output_list = make_pretty_aprs_messages(
                message_to_add=f"Dst {math.ceil(distance)} {dst_uom}",
                destination_list=output_list,
            )
            output_list = make_pretty_aprs_messages(
                message_to_add=f"Brg {round(bearing)} deg", destination_list=output_list
            )
            output_list = make_pretty_aprs_messages(
                message_to_add=heading, destination_list=output_list
            )

    success = True
    return success, output_list


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
    )
    logger = logging.getLogger(__name__)

    (
        success,
        aprsdotfi_api_key,
        openweathermap_api_key,
        aprsis_callsign,
        aprsis_passcode,
        dapnet_callsign,
        dapnet_passcode,
    ) = read_program_config()
    if success:
        logger.info("Further actions are executed here")
