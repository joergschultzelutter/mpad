#
# Multi-Purpose APRS Daemon: Output generator
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: Generate the output that is to be sent to the user
# (based on the successfully parsed content's input message)
#

from openweathermap_modules import (
    get_daily_weather_from_openweathermapdotorg,
    parse_daily_weather_from_openweathermapdotorg,
)
from cwop_modules import (
    get_cwop_findu,
    get_nearest_cwop_findu,
)


from utility_modules import make_pretty_aprs_messages, read_program_config
from airport_data_modules import get_metar_data
from skyfield_modules import get_sun_moon_rise_set_for_latlon
from geo_conversion_modules import (
    convert_latlon_to_maidenhead,
    convert_latlon_to_mgrs,
    convert_latlon_to_utm,
    convert_latlon_to_dms,
)

from repeater_modules import read_mpad_repeatermap_data_from_disc, get_nearest_repeater

import datetime
import logging

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
    (we need to do this for the two use cases, but the
    data is the same)

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

    # Generate the output. We need to declare a dummy list here as some -or all-
    # of these elements are missing (and we don't know which ones will that be)
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


def generate_output_message(
    response_parameters: dict, openweathermapdotorg_api_key: str
):
    """
    Evaluate the input parser's output and gather the data the user
    wants to receive. If this function is called, then the parser
    process was successful - we no longer need to check the status

    Parameters
    ==========
    response_parameters: 'dict'
        Dictionary of the data from the input processor's analysis on the user's data
    openweathermapdotorg_api_key: 'str'
        API access key to openweathermap.org

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

    # Now evaluate the action command and extract the required fields
    # from the dictionary (dependent on the context)

    #
    # WX report?
    #
    if what == "wx":
        latitude = response_parameters["latitude"]
        longitude = response_parameters["longitude"]
        units = response_parameters["units"]
        when = response_parameters["when"]
        when_daytime = response_parameters["when_daytime"]
        date_offset = response_parameters["date_offset"]
        human_readable_message = response_parameters["human_readable_message"]
        success, myweather, tz_offset, tz = get_daily_weather_from_openweathermapdotorg(
            latitude=latitude,
            longitude=longitude,
            units=units,
            date_offset=date_offset,
            openweathermap_api_key=openweathermapdotorg_api_key,
        )
        if success:
            weather_forecast_array = parse_daily_weather_from_openweathermapdotorg(
                myweather, units, human_readable_message, when, when_daytime
            )
            return success, weather_forecast_array
        else:
            success = True
            output_list = make_pretty_aprs_messages(
                message_to_add=f"{human_readable_message} - unable to get wx"
            )
            return success, output_list

    #
    # General help?
    #
    if what == "help":
        success = True
        return success, help_text_array

    #
    # METAR data?
    # At this point in time, we know for sure that the airport is METAR
    # capable. If we are still unable to retrieve that METAR data, then
    # output the error message to the user
    # (human_readable_message) from imput parser is ignored in order to
    # shorten the user message
    #
    if what == "metar":
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
    #
    # Satellite pass?
    #
    if what == "satpass":
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

    #
    # CWOP data by lat/lon?
    #
    if what == "cwop_by_latlon":
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

    #
    # CWOP data by CWOP ID?
    #
    if what == "cwop_by_cwop_id":
        human_readable_message = response_parameters["human_readable_message"]
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

    #
    # Sunrise/Sunset and Moonrise/Moonset
    #
    if what == "riseset":
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

    #
    # 'Whereis' location information
    #
    if what == "whereis":
        latitude = response_parameters["latitude"]
        longitude = response_parameters["longitude"]
        altitude = response_parameters["altitude"]
        human_readable_message = response_parameters["human_readable_message"]
        when_daytime = response_parameters["when_daytime"]

        # human-readable data was reverse-lookup'ed and can be 'None'
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
            message_to_add=f"Grid:{grid}", destination_list=output_list
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
            f"DMS:{lat_hdg}{lat_deg:02d}.{lat_min:02d}'{round(lat_sec):02d}"
        )
        human_readable_address += (
            f", {lon_hdg}{lon_deg:02d}.{lon_min:02d}'{round(lon_sec):02d}"
        )

        output_list = make_pretty_aprs_messages(
            message_to_add=human_readable_address,
            destination_list=output_list,
        )

        zone_number, zone_letter, easting, northing = convert_latlon_to_utm(
            latitude=latitude, longitude=longitude
        )
        output_list = make_pretty_aprs_messages(
            message_to_add=f"UTM:{zone_number}{zone_letter} {easting} {northing}",
            destination_list=output_list,
        )

        mgrs = convert_latlon_to_mgrs(latitude=latitude, longitude=longitude)
        output_list = make_pretty_aprs_messages(
            message_to_add=f"MGRS:{mgrs}", destination_list=output_list
        )

        output_list = make_pretty_aprs_messages(
            message_to_add=f"LatLon:{latitude}/{longitude}",
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
                human_readable_address += f" {street_number}"
        if human_readable_address:
            output_list = make_pretty_aprs_messages(
                message_to_add=human_readable_address, destination_list=output_list
            )

        success = True
        return success, output_list

    #
    # Repeater data
    #
    if what == "repeater":
        latitude = response_parameters["latitude"]
        longitude = response_parameters["longitude"]
        units = response_parameters["units"]
        repeater_band = response_parameters["repeater_band"]
        repeater_mode = response_parameters["repeater_mode"]

        # Static file solution; needs dynamic refresh
        success, repeater_dict = read_mpad_repeatermap_data_from_disc()
        if success:
            success, nearest_repeater = get_nearest_repeater(
                latitude=latitude,
                longitude=longitude,
                mpad_repeatermap_dictionary=repeater_dict,
                mode=repeater_mode,
                band=repeater_band,
                units=units,
            )
            if success:
                locator = nearest_repeater["locator"]
                latitude = nearest_repeater["latitude"]
                longitude = nearest_repeater["longitude"]
                mode = nearest_repeater["mode"]
                band = nearest_repeater["band"]
                rx_frequency = nearest_repeater["rx_frequency"]
                tx_frequency = nearest_repeater["tx_frequency"]
                elevation = nearest_repeater["elevation"]
                remarks = nearest_repeater["remarks"]
                qth = nearest_repeater["qth"]
                callsign = nearest_repeater["callsign"]
                distance = nearest_repeater["distance"]
                distance_uom = nearest_repeater["distance_uom"]
                bearing = nearest_repeater["bearing"]
                direction = nearest_repeater["direction"]

                # Build the output message
                output_list = make_pretty_aprs_messages(f"Nearest repeater {qth}")
                output_list = make_pretty_aprs_messages(
                    f"{distance} {distance_uom}", output_list
                )
                output_list = make_pretty_aprs_messages(
                    f"{bearing} deg {direction}", output_list
                )
                output_list = make_pretty_aprs_messages(
                    f"Rx {rx_frequency}", output_list
                )
                output_list = make_pretty_aprs_messages(
                    f"Tx {tx_frequency}", output_list
                )
                # Remarks können leer sein
                if remarks:
                    output_list = make_pretty_aprs_messages(f"{remarks}", output_list)
                output_list = make_pretty_aprs_messages(f"{mode}", output_list)
                output_list = make_pretty_aprs_messages(f"{band}", output_list)
                output_list = make_pretty_aprs_messages(f"{locator}", output_list)
            else:
                output_list = make_pretty_aprs_messages(
                    "Cannot locate nearest repeater"
                )
                success = True
        else:
            output_list = make_pretty_aprs_messages(
                "Cannot read repeater directory from disc"
            )
            success = True
        return success, output_list

    # No keyword found
    success = False
    output_list = [
        "Sorry, I am unable to parse your request. I have logged a copy of",
        "your request to my log file which will help my author to understand",
        "what you asked me to do. Thank you",
    ]
    logging.debug(f"Unable to parse packet: {response_parameters}")

    return success, output_list


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
    )

    success, aprsdotfi_api_key, openweathermap_api_key = read_program_config()
    if success:
        logging.debug("Further actions are executed here")
