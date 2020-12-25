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
from utility_modules import make_pretty_aprs_messages, log_to_stderr
from airport_data_modules import get_metar_data

###
# Help text that the user receives in case he has requested help
help_text_array = [
    "(default=wx for pos of sending callsign). Position commands:",
    "city,state;country OR city,state OR city;country OR zip;country OR",
    "zip with/wo country OR grid|mh+4..6 char OR lat/lon OR callsign",
    "time: mon..sun(day),today,tomorrow.Extra: mtr|metric imp|imperial",
]


def generate_output_message(response_parameters: dict):
    """
    Evaluate the input parser's output and gather the data the user
    wants to receive. If this function is called, then the parser
    process was successful - we no longer need to check the status

    Parameters
    ==========


    Returns
    =======
    success: 'bool'
        True if operation was successful
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
    # this is a error for us
    #
    if what == "metar":
        icao_code = response_parameters["icao"]
        human_readable_message = response_parameters["human_readable_message"]
        success, metar_response = get_metar_data(icao_code=icao_code)
        if success:
            output_list = []
            output_list = make_pretty_aprs_messages(human_readable_message, output_list)
            output_list = make_pretty_aprs_messages(metar_response, output_list)
            return success, output_list
        else:
            print("metar nicht gefunden")

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
        human_readable_message = response_parameters["human_readable_message"]
        output_list = ["cwop by lat lon"]
        success = True
        return success, output_list

    #
    # CWOP data by CWOP ID?
    #
    if what == "cwop_by_cwop_id":
        human_readable_message = response_parameters["human_readable_message"]
        cwop_id = response_parameters["cwop_id"]
        output_list = ["cwop by cwop_id"]
        success = True
        return success, output_list

    #
    # Sunrise/Sunset and Moonrise/Moonset
    #
    if what == "riseset":
        latitude = response_parameters["latitude"]
        longitude = response_parameters["longitude"]
        altitude = response_parameters["altitude"]
        output_list = ["riseset"]
        success = True
        return success, output_list

    #
    # 'Whereis' location information
    #
    if what == "whereis":
        latitude = response_parameters["latitude"]
        longitude = response_parameters["longitude"]
        altitude = response_parameters["altitude"]
        when_daytime = response_parameters["when_daytime"]
        output_list = ["whereis"]
        success = True
        return success, output_list

    #
    # Repeater data
    #
    if what == "repeater":
        latitude = response_parameters["latitude"]
        longitude = response_parameters["longitude"]
        altitude = response_parameters["altitude"]
        repeater_band = response_parameters["repeater_band"]
        repeater_mode = response_parameters["repeater_mode"]
        output_list = ["repeater"]
        success = True
        return success, output_list

    # No keyword found
    success = False
    output_list = ["Unable to parse packet"]
    log_to_stderr(f"Unable to parse packet")
    return success, output_list
