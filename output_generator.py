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


from utility_modules import make_pretty_aprs_messages, log_to_stderr
from airport_data_modules import get_metar_data
from skyfield_modules import get_sun_moon_rise_set_for_latlon
from geo_conversion_modules import convert_latlon_to_maidenhead, convert_latlon_to_mgrs, convert_latlon_to_utm, convert_latlon_to_dms

import datetime

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

    cwop_id = cwop_dict['cwop_id']
    time = cwop_dict['time']
    temp = cwop_dict['temp']
    temp_uom = cwop_dict['temp_uom']
    wind_direction = cwop_dict['wind_direction']
    wind_speed = cwop_dict['wind_speed']
    wind_gust = cwop_dict['wind_gust']
    speedgust_uom = cwop_dict['speedgust_uom']
    rain_1h = cwop_dict['rain_1h']
    rain_24h = cwop_dict['rain_24h']
    rain_mn = cwop_dict['rain_mn']
    rain_uom = cwop_dict['rain_uom']
    humidity = cwop_dict['humidity']
    humidity_uom = cwop_dict['humidity_uom']
    air_pressure = cwop_dict['air_pressure']
    air_pressure_uom = cwop_dict['air_pressure_uom']

    # Generate the output
    output_list = []
    # we ignore the 'human_readable_message' variable at this point
    # as it did not yet contain the respective CWOP ID
    if cwop_id:
        output_list = make_pretty_aprs_messages(f"CWOP for {cwop_id}", output_list)
    if time:
        ts = datetime.datetime.fromtimestamp(time)
        output_list = make_pretty_aprs_messages(datetime.datetime.strftime(ts, "%d-%b-%y"), output_list)
    if temp:
        output_list = make_pretty_aprs_messages(f"{temp}{temp_uom}", output_list)
    if wind_direction:
        output_list = make_pretty_aprs_messages(f"{wind_direction}deg", output_list)
    if wind_speed:
        output_list = make_pretty_aprs_messages(f"Spd. {wind_speed}{speedgust_uom}", output_list)
    if wind_gust:
        output_list = make_pretty_aprs_messages(f"Gust {wind_gust}{speedgust_uom}", output_list)
    if rain_1h:
        output_list = make_pretty_aprs_messages(f"Rain 1h {rain_1h}{rain_uom}", output_list)
    if rain_24h:
        output_list = make_pretty_aprs_messages(f"Rain 24h {rain_24h}{rain_uom}", output_list)
    if rain_mn:
        output_list = make_pretty_aprs_messages(f"Rain mn {rain_mn}{rain_uom}", output_list)
    if humidity:
        output_list = make_pretty_aprs_messages(f"Hum. {humidity}{humidity_uom}", output_list)
    if air_pressure:
        output_list = make_pretty_aprs_messages(f"Press. {air_pressure}{air_pressure_uom}", output_list)

    return output_list


def generate_output_message(response_parameters: dict, openweathermapdotorg_api_key: str):
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
            output_list = []
            output_list = make_pretty_aprs_messages(f"{human_readable_message} - unable to get wx", output_list)
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
            success = True
            output_list = []
            output_list = make_pretty_aprs_messages(f"Unable to get METAR date for {icao_code}", output_list)
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
        success, cwop_dict = get_nearest_cwop_findu(latitude=latitude, longitude=longitude, units=units)
        if success:
            # extract the response fields from the parsed message content
            output_list = create_cwop_content(cwop_dict)
            success = True
            return success, output_list
        else:
            output_list = []
            output_list = make_pretty_aprs_messages(f"Unable to get nearest CWOP for {message_callsign}", output_list)
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
            output_list = []
            output_list = make_pretty_aprs_messages(f"Unable to get CWOP for ID {cwop_id}", output_list)
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

        sunrise, sunset, moonrise, moonset = get_sun_moon_rise_set_for_latlon(latitude=latitude, longitude=longitude,requested_date=requested_date, elevation=altitude)
        output_list = []
        output_list = make_pretty_aprs_messages(human_readable_message,output_list)
        output_list = make_pretty_aprs_messages(datetime.datetime.strftime(requested_date,"%d-%b"), output_list)
        output_list = make_pretty_aprs_messages("GMT sun rise/set", output_list)
        output_list = make_pretty_aprs_messages(datetime.datetime.strftime(sunrise,"%H:%M"), output_list)
        output_list = make_pretty_aprs_messages(datetime.datetime.strftime(sunset,"-%H:%M"), output_list)
        output_list = make_pretty_aprs_messages("moon set/rise", output_list)
        output_list = make_pretty_aprs_messages(datetime.datetime.strftime(moonset,"%H:%M"), output_list)
        output_list = make_pretty_aprs_messages(datetime.datetime.strftime(moonrise,"-%H:%M"), output_list)
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

        #human-readable data was reverse-lookup'ed and can be 'None'
        city = response_parameters["city"]
        state = response_parameters["state"]
        zip = response_parameters["zip"]
        country = response_parameters["country"]

        output_list = []
        output_list = make_pretty_aprs_messages(human_readable_message,output_list)

        grid = convert_latlon_to_maidenhead(latitude=latitude, longitude=longitude)
        output_list = make_pretty_aprs_messages(f"Grid {grid}", output_list)

        lat_deg, lat_min, lat_sec, lat_hdg, lon_deg, lon_min, lon_sec, lon_hdg = convert_latlon_to_dms(latitude=latitude,longitude=longitude)
        output_list = make_pretty_aprs_messages(f"DMS: {lat_deg}.{lat_min}\'{lat_sec}\" {lat_hdg} {lon_deg}.{lon_min}\'{lon_sec}\" {lon_hdg}", output_list)

        zone_number, zone_letter, easting, northing = convert_latlon_to_utm(latitude=latitude, longitude=longitude)
        output_list = make_pretty_aprs_messages(f"UTM: {zone_number}{zone_letter} {easting} {northing}", output_list)

        mgrs = convert_latlon_to_mgrs(latitude=latitude, longitude=longitude)
        output_list = make_pretty_aprs_messages(f"MGRS: {mgrs}", output_list)

        output_list = make_pretty_aprs_messages(f"Lat/Lon: {latitude}/{longitude}", output_list)

        human_readable_address = None
        if city:
            human_readable_address = city
            if zip:
                human_readable_address += f", {zip}"
            if country:
                human_readable_address += f", {country}"

        if human_readable_address:
            output_list = make_pretty_aprs_messages(human_readable_address, output_list)

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
