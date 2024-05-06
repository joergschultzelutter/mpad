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

import mpad_config
from geopy_modules import get_osm_special_phrase_data, get_reverse_geopy_data

from utility_modules import make_pretty_aprs_messages, read_program_config
from airport_data_modules import get_metar_data
from skyfield_modules import (
    get_sun_moon_rise_set_for_latlon,
    get_next_satellite_pass_for_latlon,
    get_satellite_frequency_data,
)
from geo_conversion_modules import (
    convert_latlon_to_maidenhead,
    convert_latlon_to_mgrs,
    convert_latlon_to_utm,
    convert_latlon_to_dms,
    haversine,
)
from dapnet_modules import send_dapnet_message

from repeater_modules import get_nearest_repeater
from funstuff_modules import get_fortuneteller_message
from email_modules import send_email_position_report
from radiosonde_modules import get_radiosonde_landing_prediction

import datetime
import logging
import math

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


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
        logger.info("Running output worker generate_output_message_wx()")
        success, output_list = generate_output_message_wx(
            response_parameters=response_parameters,
        )
    elif what in ("metar", "taf"):
        logger.info("Running output worker generate_output_message_metar()")
        success, output_list = generate_output_message_metar(
            response_parameters=response_parameters
        )
    elif what == "help":
        logger.info("Running output worker generate_output_message_help()")
        success, output_list = generate_output_message_help()
    elif what == "cwop_by_latlon":
        logger.info("Running output worker generate_output_message_cwop_by_latlon()")
        success, output_list = generate_output_message_cwop_by_latlon(
            response_parameters=response_parameters
        )
    elif what == "cwop_by_cwop_id":
        logger.info("Running output worker generate_output_message_cwop_by_cwop_id()")
        success, output_list = generate_output_message_cwop_by_cwop_id(
            response_parameters=response_parameters
        )
    elif what == "riseset":
        logger.info("Running output worker generate_output_message_riseset()")
        success, output_list = generate_output_message_riseset(
            response_parameters=response_parameters
        )
    elif what == "satpass" or what == "vispass":
        logger.info("Running output worker generate_output_message_satpass()")
        success, output_list = generate_output_message_satpass(
            response_parameters=response_parameters
        )
    elif what == "satfreq":
        logger.info("Running output worker generate_output_message_satfreq()")
        success, output_list = generate_output_message_satfreq(
            response_parameters=response_parameters
        )
    elif what == "repeater":
        logger.info("Running output worker generate_output_message_repeater()")
        success, output_list = generate_output_message_repeater(
            response_parameters=response_parameters
        )
    elif what == "whereis":
        logger.info("Running output worker generate_output_message_whereis()")
        success, output_list = generate_output_message_whereis(
            response_parameters=response_parameters
        )
    elif what == "osm_special_phrase":
        logger.info(
            "Running output worker generate_output_message_osm_special_phrase()"
        )
        success, output_list = generate_output_message_osm_special_phrase(
            response_parameters=response_parameters
        )
    elif what == "dapnet" or what == "dapnethp":
        logger.info("Running output worker generate_output_message_dapnet()")
        success, output_list = generate_output_message_dapnet(
            response_parameters=response_parameters
        )
    elif what == "sonde":
        logger.info("Running output worker generate_output_message_radiosonde()")
        success, output_list = generate_output_message_radiosonde(
            response_parameters=response_parameters
        )
    elif what == "fortuneteller":
        logger.info("Running output worker generate_output_message_fortuneteller()")
        success, output_list = generate_output_message_fortuneteller(
            response_parameters=response_parameters
        )
    elif what == "email_position_report":
        logger.info(
            "Running output worker generate_output_message_email_position_report()"
        )
        success, output_list = generate_output_message_email_position_report(
            response_parameters=response_parameters
        )
    else:
        success = False
        output_list = [
            "Output parser has encountered an unknown action command",
        ]
        logger.info(
            msg=f"Unable to generate output message; unknown 'what' command '{what}': {response_parameters}"
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
    force_outgoing_unicode_messages = response_parameters[
        "force_outgoing_unicode_messages"
    ]

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
            weather_tuple=myweather,
            units=units,
            human_readable_text=human_readable_message,
            when=when,
            when_dt=when_daytime,
            force_outgoing_unicode_messages=force_outgoing_unicode_messages,
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
    Generate a METAR and/or TAF report for a specific airport (ICAO code)

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

    # now get the action command which was requested by the user
    # value can only be "metar" or "taf"
    _what = response_parameters["what"]

    # and get info on whether the user wants both ME
    when_daytime = response_parameters["when_daytime"]
    _full = True if when_daytime == "full" else False

    success, metar_response = get_metar_data(
        icao_code=icao_code, keyword=_what, full_msg=_full
    )
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
    output_list = mpad_config.help_text_array
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
    what = response_parameters["what"]
    when = response_parameters["when"]
    number_of_results = response_parameters["number_of_results"]
    date_offset = response_parameters["date_offset"]
    hour_offset = response_parameters["hour_offset"]
    units = response_parameters["units"]
    message_callsign = response_parameters["message_callsign"]

    visible_passes_only = True if what == "vispass" else False

    vis_text = "vis " if visible_passes_only else ""
    passes_text = "pass"  # we'll change this to plural if there is more than 1 result

    # Determine the correct timestamp:
    # First, we will get the current UTC time
    # If an hourly offset was specified, we will add this to the current datestamp
    # If no hourly offset was specified:
    # if our date is set to the future, add the additional days to the date and
    # then set the time information to zero
    # if additional time information was specified, set it accordingly
    # As always, ALL of these settings (including the 'relative' ones like
    # "night" refer to UTC.
    request_datestamp = datetime.datetime.utcnow()
    if when == "hour":
        request_datestamp += datetime.timedelta(hours=hour_offset)
    else:
        if date_offset > 0:
            request_datestamp += datetime.timedelta(days=date_offset)
            ds = datetime.datetime(
                year=request_datestamp.year,
                month=request_datestamp.month,
                day=request_datestamp.day,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            request_datestamp = ds
        if when_daytime != "full":
            ds = datetime.datetime(
                year=request_datestamp.year,
                month=request_datestamp.month,
                day=request_datestamp.day,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
            if when_daytime == mpad_config.mpad_str_morning:
                ds += datetime.timedelta(hours=3)
            elif when_daytime == mpad_config.mpad_str_daytime:
                ds += datetime.timedelta(hours=12)
            elif when_daytime == mpad_config.mpad_str_evening:
                ds += datetime.timedelta(hours=17)
            elif when_daytime == mpad_config.mpad_str_night:
                ds += datetime.timedelta(hours=22)
            request_datestamp = ds

    success, satellite_response_data = get_next_satellite_pass_for_latlon(
        latitude=latitude,
        longitude=longitude,
        requested_date=request_datestamp,
        tle_satellite_name=satellite,
        elevation=altitude,
        units=units,
        number_of_results=number_of_results,
        visible_passes_only=visible_passes_only,
    )
    output_list = []
    list_number = 1
    if not success:
        output_list = make_pretty_aprs_messages(
            message_to_add=f"Unable to determine sat pass data for '{satellite}'",
            destination_list=output_list,
        )
    else:
        dictlen = len(satellite_response_data)
        if dictlen == 0:
            output_list = make_pretty_aprs_messages(
                message_to_add=f"'{satellite}':", destination_list=output_list
            )
            output_list = make_pretty_aprs_messages(
                message_to_add="cannot find satpasses for your loc.",
                destination_list=output_list,
            )
        else:
            if dictlen > 1:
                passes_text = "passes"
            output_list = make_pretty_aprs_messages(
                message_to_add=f"{satellite} {vis_text}{passes_text} for {message_callsign} UTC",
                destination_list=output_list,
            )
            for rise_date in satellite_response_data:
                culmination_date = satellite_response_data[rise_date][
                    "culmination_date"
                ]
                set_date = satellite_response_data[rise_date]["set_date"]
                is_visible = satellite_response_data[rise_date]["is_visible"]
                altitude = math.ceil(satellite_response_data[rise_date]["altitude"])
                azimuth = math.ceil(satellite_response_data[rise_date]["azimuth"])
                distance = round(satellite_response_data[rise_date]["distance"])
                distance_uom = "km"
                if units == "imperial":
                    distance_uom = "mi"
                rise_text = "Rise" if list_number == 1 else "R"
                culm_text = "Culm" if list_number == 1 else "C"
                set_text = "Set" if list_number == 1 else "S"
                deg_text = " deg" if list_number == 1 else ""
                uom_text = distance_uom if list_number == 1 else ""
                visible_text = "Vis " if list_number == 1 else "Vs "

                if dictlen != 1:
                    output_list = make_pretty_aprs_messages(
                        message_to_add=f"#{list_number}", destination_list=output_list
                    )
                    list_number += 1
                output_list = make_pretty_aprs_messages(
                    message_to_add=f"{rise_text} {rise_date.strftime('%d-%b %H:%M')}",
                    destination_list=output_list,
                )
                output_list = make_pretty_aprs_messages(
                    message_to_add=f"{culm_text} {culmination_date.strftime('%H:%M')}",
                    destination_list=output_list,
                )
                output_list = make_pretty_aprs_messages(
                    message_to_add=f"{set_text} {set_date.strftime('%H:%M')}",
                    destination_list=output_list,
                )
                output_list = make_pretty_aprs_messages(
                    message_to_add=f"Alt {altitude}{deg_text}",
                    destination_list=output_list,
                )
                output_list = make_pretty_aprs_messages(
                    message_to_add=f"Az {azimuth}{deg_text}",
                    destination_list=output_list,
                )
                output_list = make_pretty_aprs_messages(
                    message_to_add=f"Dst {distance}{uom_text}",
                    destination_list=output_list,
                )
                if not visible_passes_only:
                    visible = "Y" if is_visible else "N"
                    output_list = make_pretty_aprs_messages(
                        message_to_add=f"{visible_text}{visible}",
                        destination_list=output_list,
                    )
    success = True  # always True
    return success, output_list


def generate_output_message_satfreq(response_parameters: dict):
    """
    Generate the satellite frequency report

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
    success = False

    output_list = []
    list_number = 1
    success, satellite_name, frequency_data = get_satellite_frequency_data(
        satellite_id=satellite
    )
    if not success:
        output_list = make_pretty_aprs_messages(
            message_to_add=f"Cannot find satellite '{satellite}'",
            destination_list=output_list,
        )
    else:
        dictlen = len(frequency_data)
        if dictlen == 0:
            output_list = make_pretty_aprs_messages(
                message_to_add=f"'{satellite}'", destination_list=output_list
            )
            output_list = make_pretty_aprs_messages(
                message_to_add="has no frequency data",
                destination_list=output_list,
            )
        else:
            output_list = make_pretty_aprs_messages(
                message_to_add=f"'{satellite}' Freq:",
                destination_list=output_list,
            )
            for frequency in frequency_data:
                uplink = frequency["uplink"]
                downlink = frequency["downlink"]
                beacon = frequency["beacon"]
                satellite_mode = frequency["satellite_mode"]

                uplink_text = "Uplink" if list_number == 1 else "Up"
                downlink_text = "Downlink" if list_number == 1 else "Dn"
                beacon_text = "Beacon" if list_number == 1 else "Bcn"
                mode_text = "Mode" if list_number == 1 else "Md"

                if dictlen != 1:
                    output_list = make_pretty_aprs_messages(
                        message_to_add=f"#{list_number}", destination_list=output_list
                    )
                    list_number += 1
                if uplink:
                    output_list = make_pretty_aprs_messages(
                        message_to_add=f"{uplink_text} {uplink}",
                        destination_list=output_list,
                    )
                if downlink:
                    output_list = make_pretty_aprs_messages(
                        message_to_add=f"{downlink_text} {downlink}",
                        destination_list=output_list,
                    )
                if beacon:
                    output_list = make_pretty_aprs_messages(
                        message_to_add=f"{beacon_text} {beacon}",
                        destination_list=output_list,
                    )
                if satellite_mode:
                    output_list = make_pretty_aprs_messages(
                        message_to_add=f"{mode_text} {satellite_mode}",
                        destination_list=output_list,
                    )
    success = True  # always True
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

    # For certain datetime events, Skyfield cannot always find
    # either sunrise and/or sunset
    # For such cases, ensure that the pretty-printer is not used
    if sunrise and sunset:
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

    if sunrise and not sunset:
        output_list = make_pretty_aprs_messages(
            message_to_add="GMT sunrise", destination_list=output_list
        )
        output_list = make_pretty_aprs_messages(
            message_to_add=datetime.datetime.strftime(sunrise, "%H:%M"),
            destination_list=output_list,
        )

    if sunset and not sunrise:
        output_list = make_pretty_aprs_messages(
            message_to_add="GMT sunset", destination_list=output_list
        )
        output_list = make_pretty_aprs_messages(
            message_to_add=datetime.datetime.strftime(sunset, "%H:%M"),
            destination_list=output_list,
        )

    # For certain datetime events, Skyfield cannot always find
    # either moonrise and/or moonset
    # For such cases, ensure that the pretty-printer is not used

    if moonset and moonrise:
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

    if moonset and not moonrise:
        output_list = make_pretty_aprs_messages(
            message_to_add="mn_set", destination_list=output_list
        )
        output_list = make_pretty_aprs_messages(
            message_to_add=datetime.datetime.strftime(moonset, "%H:%M"),
            destination_list=output_list,
        )

    if moonrise and not moonset:
        output_list = make_pretty_aprs_messages(
            message_to_add="mn_rise", destination_list=output_list
        )
        output_list = make_pretty_aprs_messages(
            message_to_add=datetime.datetime.strftime(moonrise, "%H:%M"),
            destination_list=output_list,
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


def generate_output_message_radiosonde(response_parameters: dict):
    """
    Tries to determine a radiosonde landing coordinates based on its aprs.fi data

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
    aprsdotfi_api_key = response_parameters["aprsdotfi_api_key"]
    human_readable_message = response_parameters["human_readable_message"]
    users_latitude = response_parameters["users_latitude"]
    users_longitude = response_parameters["users_longitude"]
    units = response_parameters["units"]
    language = response_parameters["language"]
    force_outgoing_unicode_messages = response_parameters[
        "force_outgoing_unicode_messages"
    ]

    output_list = []

    (
        success,
        landing_latitude,
        landing_longitude,
        landing_timestamp,
        landing_url,
    ) = get_radiosonde_landing_prediction(
        aprsfi_callsign=message_callsign, aprsdotfi_api_key=aprsdotfi_api_key
    )
    if success:
        output_list = make_pretty_aprs_messages(
            message_to_add=human_readable_message,
            destination_list=output_list,
            force_outgoing_unicode_messages=force_outgoing_unicode_messages,
        )
        output_list = make_pretty_aprs_messages(
            message_to_add="Lat/Lon", destination_list=output_list
        )
        output_list = make_pretty_aprs_messages(
            message_to_add=f"{landing_latitude}/{landing_longitude}",
            destination_list=output_list,
        )
        output_list = make_pretty_aprs_messages(
            message_to_add=f"{landing_timestamp.strftime('%d-%b %H:%M')}UTC",
            destination_list=output_list,
        )

        if landing_latitude != users_latitude and landing_longitude != users_longitude:
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
                latitude2=landing_latitude,
                longitude2=landing_longitude,
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
        grid = convert_latlon_to_maidenhead(
            latitude=landing_latitude, longitude=landing_longitude
        )
        output_list = make_pretty_aprs_messages(
            message_to_add=f"Grid {grid}", destination_list=output_list
        )

        success, response_data = get_reverse_geopy_data(
            latitude=landing_latitude, longitude=landing_longitude, language=language
        )
        if success:
            address = response_data["address"]
            output_list = make_pretty_aprs_messages(
                message_to_add=f"Addr: {address}",
                destination_list=output_list,
                force_outgoing_unicode_messages=force_outgoing_unicode_messages,
            )
    else:
        output_list = make_pretty_aprs_messages(
            message_to_add=f"Cannot predict landing parameters for '{message_callsign}'"
        )
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
    force_outgoing_unicode_messages = response_parameters[
        "force_outgoing_unicode_messages"
    ]

    # all of the following data was reverse-lookup'ed and can be 'None'
    city = response_parameters["city"]
    state = response_parameters["state"]
    zipcode = response_parameters["zipcode"]
    country = response_parameters["country"]
    district = response_parameters["district"]
    address = response_parameters["address"]
    country_code = response_parameters["country_code"]
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

    # add OSM location information (e.g. street, city, state)
    output_list = make_pretty_aprs_messages(
        message_to_add=f"Addr: {address}",
        destination_list=output_list,
        force_outgoing_unicode_messages=force_outgoing_unicode_messages,
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
    force_outgoing_unicode_messages = response_parameters[
        "force_outgoing_unicode_messages"
    ]

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

            output_list = make_pretty_aprs_messages(
                message_to_add="{location}",
                destination_list=output_list,
                force_outgoing_unicode_messages=force_outgoing_unicode_messages,
            )

            output_list = make_pretty_aprs_messages(
                message_to_add=f"Dst {distance} {distance_uom}",
                destination_list=output_list,
            )
            output_list = make_pretty_aprs_messages(
                message_to_add=f"{bearing} deg {direction}",
                destination_list=output_list,
            )
            # Both repeater frequency and shift are in Hz. Let's convert to MHz
            repeater_frequency = round(repeater_frequency / 1000000, 4)
            repeater_shift = round(repeater_shift / 1000000, 4)
            if repeater_shift != 0:
                output_list = make_pretty_aprs_messages(
                    message_to_add=f"{repeater_frequency:0.4f}{repeater_shift:+0.1f} MHz",
                    destination_list=output_list,
                )
            else:
                output_list = make_pretty_aprs_messages(
                    message_to_add=f"{repeater_frequency:0.4f} MHz",
                    destination_list=output_list,
                )

            if encode:
                output_list = make_pretty_aprs_messages(
                    message_to_add=f"Enc {encode}", destination_list=output_list
                )

            if decode:
                output_list = make_pretty_aprs_messages(
                    message_to_add=f"Dec {decode}", destination_list=output_list
                )

            # Comments can be empty
            if comments:
                output_list = make_pretty_aprs_messages(
                    message_to_add=f"{comments}",
                    destination_list=output_list,
                    force_outgoing_unicode_messages=force_outgoing_unicode_messages,
                )
            #
            # "band' and 'mode' are only added to the outgoing message if the user
            # has NOT requested these as input parameters. We can save a few bytes per
            # message and if the user has e.g. requested c4fm on 70cm via keywords,
            # we don't need to deliver this information as part of the resulting data.
            # However, if the user has NOT requested band and/or mode, we will output
            # the data to the user so that the user knows if e.g. these values are
            # valid for c4fm, d-star, ....
            if not repeater_mode:
                output_list = make_pretty_aprs_messages(
                    message_to_add=f"{mode}", destination_list=output_list
                )
            #            if not repeater_band:
            #                output_list = make_pretty_aprs_messages(f"{band}", output_list)

            output_list = make_pretty_aprs_messages(
                message_to_add=f"{locator}", destination_list=output_list
            )
    else:
        output_list = make_pretty_aprs_messages(
            message_to_add="Cannot locate nearest repeater for your query parameter set"
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
    force_outgoing_unicode_messages = response_parameters[
        "force_outgoing_unicode_messages"
    ]

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
                    message_to_add=amenity,
                    destination_list=output_list,
                    force_outgoing_unicode_messages=force_outgoing_unicode_messages,
                )
            if road:
                output_list = make_pretty_aprs_messages(
                    message_to_add=road,
                    destination_list=output_list,
                    force_outgoing_unicode_messages=force_outgoing_unicode_messages,
                )
            if house_number:
                output_list = make_pretty_aprs_messages(
                    message_to_add=house_number,
                    destination_list=output_list,
                    force_outgoing_unicode_messages=force_outgoing_unicode_messages,
                )
            if city:
                output_list = make_pretty_aprs_messages(
                    message_to_add=city,
                    destination_list=output_list,
                    force_outgoing_unicode_messages=force_outgoing_unicode_messages,
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


def generate_output_message_fortuneteller(response_parameters: dict):
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
    language = response_parameters["language"]
    force_outgoing_unicode_messages = response_parameters[
        "force_outgoing_unicode_messages"
    ]

    output_list = make_pretty_aprs_messages(
        message_to_add=get_fortuneteller_message(language=language),
        force_outgoing_unicode_messages=force_outgoing_unicode_messages,
    )
    success = True
    return success, output_list


def generate_output_message_email_position_report(response_parameters: dict):
    """
    Send an email position report based on the user's current location

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

    output_list = send_email_position_report(response_parameters=response_parameters)

    success = True  # Always 'True' as we also return error messages to the user
    return success, output_list


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


if __name__ == "__main__":
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
