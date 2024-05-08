#
# Multi-Purpose APRS Daemon: met.no Modules
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: Uses met.no for WX report prediction
# Tries to rebuild the old OpenWeatherMap API output as close as possible
#
# API documentation: https://developer.yr.no/featured-products/forecast/
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

import requests
from utility_modules import make_pretty_aprs_messages
from utility_modules import read_program_config
import logging
from pprint import pformat
import math
import mpad_config
from datetime import datetime, timezone, timedelta
from math import sin, cos, atan2

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

# Map the yr.no wx symbol to MPAD target msg
# source: https://api.met.no/weatherapi/locationforecast/2.0/swagger
metdotno_symbol_mapper: dict = {
    "clearsky_day": "ClearSky",
    "clearsky_night": "ClearSky",
    "clearsky_polartwilight": "ClearSky",
    "fair_day": "Moderate",
    "fair_night": "Moderate",
    "fair_polartwilight": "Moderate",
    "lightssnowshowersandthunder_day": "LightSnow",
    "lightssnowshowersandthunder_night": "LightSnow",
    "lightssnowshowersandthunder_polartwilight": "LightSnow",
    "lightsnowshowers_day": "LightSnow",
    "lightsnowshowers_night": "LightSnow",
    "lightsnowshowers_polartwilight": "LightSnow",
    "heavyrainandthunder": "HeavyRain",
    "heavysnowandthunder": "HeavySnow",
    "rainandthunder": "Rain",
    "heavysleetshowersandthunder_day": "HeavySleet",
    "heavysleetshowersandthunder_night": "HeavySleet",
    "heavysleetshowersandthunder_polartwilight": "HeavySleet",
    "heavysnow": "HeavySnow",
    "heavyrainshowers_day": "HeavyRain",
    "heavyrainshowers_night": "HeavyRain",
    "heavyrainshowers_polartwilight": "HeavyRain",
    "lightsleet": "LightSleet",
    "heavyrain": "HeavyRain",
    "lightrainshowers_day": "LightRain",
    "lightrainshowers_night": "LightRain",
    "lightrainshowers_polartwilight": "LightRain",
    "heavysleetshowers_day": "HeavySleet",
    "heavysleetshowers_night": "HeavySleet",
    "heavysleetshowers_polartwilight": "HeavySleet",
    "lightsleetshowers_day": "LightSleet",
    "lightsleetshowers_night": "LightSleet",
    "lightsleetshowers_polartwilight": "LightSleet",
    "snow": "Snow",
    "heavyrainshowersandthunder_day": "HeavyRain",
    "heavyrainshowersandthunder_night": "HeavyRain",
    "heavyrainshowersandthunder_polartwilight": "HeavyRain",
    "snowshowers_day": "Snow",
    "snowshowers_night": "Snow",
    "snowshowers_polartwilight": "Snow",
    "fog": "Fog",
    "snowshowersandthunder_day": "Snow",
    "snowshowersandthunder_night": "Snow",
    "snowshowersandthunder_polartwilight": "Snow",
    "lightsnowandthunder": "LightSnow",
    "heavysleetandthunder": "HeavySleet",
    "lightrain": "LightRain",
    "rainshowersandthunder_day": "Rain",
    "rainshowersandthunder_night": "Rain",
    "rainshowersandthunder_polartwilight": "Rain",
    "rain": "Rain",
    "lightsnow": "LightSnow",
    "lightrainshowersandthunder_day": "LightRain",
    "lightrainshowersandthunder_night": "LightRain",
    "lightrainshowersandthunder_polartwilight": "LightRain",
    "heavysleet": "HeavySleet",
    "sleetandthunder": "Sleet",
    "lightrainandthunder": "LightRain",
    "sleet": "Sleet",
    "lightssleetshowersandthunder_day": "LightSleet",
    "lightssleetshowersandthunder_night": "LightSleet",
    "lightssleetshowersandthunder_polartwilight": "LightSleet",
    "lightsleetandthunder": "LightSleet",
    "partlycloudy_day": "PartlyCloudy",
    "partlycloudy_night": "PartlyCloudy",
    "partlycloudy_polartwilight": "PartlyCloudy",
    "sleetshowersandthunder_day": "Sleet",
    "sleetshowersandthunder_night": "Sleet",
    "sleetshowersandthunder_polartwilight": "Sleet",
    "rainshowers_day": "Rain",
    "rainshowers_night": "Rain",
    "rainshowers_polartwilight": "Rain",
    "snowandthunder": "Snow",
    "sleetshowers_day": "Sleet",
    "sleetshowers_night": "Sleet",
    "sleetshowers_polartwilight": "Sleet",
    "cloudy": "Cloudy",
    "heavysnowshowersandthunder_day": "HeavySnow",
    "heavysnowshowersandthunder_night": "HeavySnow",
    "heavysnowshowersandthunder_polartwilight": "HeavySnow",
    "heavysnowshowers_day": "HeavySnow",
    "heavysnowshowers_night": "HeavySnow",
    "heavysnowshowers_polartwilight": "HeavySnow",
}


def get_wx_data_tuple(weather_tuples: dict, index: int):
    success = False
    try:
        result = weather_tuples[index]["data"]["instant"]["details"]
    except KeyError:
        return False, None
    # we received the main tuple. Now try to get the remaining
    # optional content and add it to our tuple
    success = True
    try:
        symbol_code = weather_tuples[index]["data"]["next_1_hours"]["summary"][
            "symbol_code"
        ]
        result["symbol_code"] = symbol_code
    except KeyError:
        pass
    try:
        precipitation_amount = weather_tuples[index]["data"]["next_1_hours"]["details"][
            "precipitation_amount"
        ]
        result["precipitation_amount"] = precipitation_amount
    except KeyError:
        pass
    return success, result


def get_daily_weather_from_metdotno(
    latitude: float,
    longitude: float,
    offset: int,
    access_mode: str = "day",
    daytime: str = "daytime",
):
    """
    Gets the met.no weather forecast for a given latitide
    and longitude and tries to extract the raw weather data for
    a certain date.

    NOTE: Every data that is retrieved here is in metric format
          and has to be converted to imperial format

    Parameters
    ==========
    latitude: 'float'
        latitude position
    longitude: 'float'
        longitude position
    offset: 'int'
        if 'access_mode' == 'day:
        numeric offset from 'today' to the desired
        target day; e.g. today = tuesday and desired
        day = thursday, then date_offset = 2
        if 'access_mode' == 'hour':
        mumeric hourly offset, e.g. 1 = one hour from now
    openweathermap_api_key: str
        API key for accessing openweathermap.org api
    units: 'str'
        Unit of measure. Can either be 'metric' or 'imperial'
    access_mode: 'str'
        Can either be 'day','hour' or 'current'

    Returns
    =======
    success: 'bool'
        True if we were able to download the data
    weather_tuple: 'dict'
        JSON weather tuple for the requested day.
    """

    headers = {"User-Agent": mpad_config.mpad_default_user_agent}

    weather_tuple = weather_tuples = None
    success = False

    assert access_mode in ["day", "hour", "current"]
    assert daytime in ["full", "morning", "daytime", "evening", "night"]

    # return 'false' if user has requested a day that is out of bounds
    if access_mode == "day":
        if offset < 0 or offset > 7:
            return success, weather_tuple
    if access_mode == "hour":
        if offset < 0 or offset > 47:
            return success, weather_tuple

    # Prepare the URL
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/complete?lat={latitude}&lon={longitude}"
    try:
        resp = requests.get(url=url, headers=headers)
    except requests.exceptions.RequestException as e:
        logger.error(msg="{e}")
        resp = None
    if resp:
        if resp.status_code == 203:
            logger.error(
                msg="Request to yr.no indicates API deprecation - see https://developer.yr.no/doc/locationforecast/HowTO/"
            )
        if resp.status_code == 200:
            response = resp.json()

            # get weather for the given day offset

            # yr.com provides a time stamp in human readable format; let's build
            # an offset dictionary which will make it easier to find what we
            # are looking for
            wx_time_offsets = {}

            if "properties" in response:
                if "timeseries" in response["properties"]:
                    # Get the wx content from the response.
                    weather_tuples = response["properties"]["timeseries"]

                    # Now let's distinguish between the various modes
                    # which can be requested by the user. First, let's
                    # check if the user intents to get the current
                    # weather and return it, if applicable.
                    if access_mode == "current":
                        return get_wx_data_tuple(weather_tuples=weather_tuples, index=0)

                    # if user wants an hour offset, try to return that
                    # one back to the user
                    elif access_mode == "hour":
                        if len(weather_tuples) > offset:
                            return get_wx_data_tuple(
                                weather_tuples=weather_tuples, index=offset
                            )
                        else:
                            return False, None
                    else:
                        # "day" mode access
                        #
                        # In comparison to OpenWeatherMap, yr.no's integration is a tad messy
                        # as there are no information clusters on e.g. "noon", "night" et al.
                        # Additionally, there is no "full day" overview, thus we need to rebuild
                        # all of this ourselves in case the user requests it
                        #
                        # build a generic index secondary index on our data
                        # not really required but I am a lazy SOB and
                        # it makes debugging a lot easier
                        # Ensure to use enumeration, thus allowing us to
                        # access the future target element directly

                        wx_time_offsets = []

                        for index, weather_tuple in enumerate(weather_tuples):
                            dt = datetime.strptime(
                                weather_tuple["time"], "%Y-%m-%dT%H:%M:%SZ"
                            )
                            wx_time_offsets.append(
                                {
                                    "date": weather_tuple["time"],
                                    "timestamp": dt,
                                    "index": index,
                                }
                            )
                        # get our *current* UTC timestamp
                        dt_utc = datetime.utcnow()

                        # Add our offset to this timestamp
                        dt_utc = dt_utc + timedelta(days=offset)

                        # Now remove the actual time information, thus effectively
                        # setting the datetime's stamp to midnight
                        # not really required in this case but safer in case I intend
                        # to use this field for other purposes at a later point in time
                        dt_utc = dt_utc.replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )

                        # used whenever a full day's results are NOT requested
                        found_generic = False
                        found_generic_index = -1

                        # used whenever a full day's results ARE requested
                        found_full = False
                        found_full_dict = {}

                        # Interate through the index that we have built ourselves
                        for wx_time_offset in wx_time_offsets:
                            wx_dt = wx_time_offset["timestamp"]
                            if (
                                dt_utc.day == wx_dt.day
                                and dt_utc.month == wx_dt.month
                                and dt_utc.year == wx_dt.year
                            ):
                                # We have found an entry for the current day
                                # Now lets check which timeslot fits
                                if (
                                    daytime == mpad_config.mpad_str_morning
                                    and wx_dt.hour == mpad_config.mpad_int_morning
                                ):
                                    found_generic = True
                                    found_generic_index = wx_time_offset["index"]
                                    break
                                elif (
                                    daytime == mpad_config.mpad_str_daytime
                                    and wx_dt.hour == mpad_config.mpad_int_daytime
                                ):
                                    found_generic = True
                                    found_generic_index = wx_time_offset["index"]
                                    break
                                elif (
                                    daytime == mpad_config.mpad_str_evening
                                    and wx_dt.hour == mpad_config.mpad_int_evening
                                ):
                                    found_generic = True
                                    found_generic_index = wx_time_offset["index"]
                                    break
                                elif (
                                    daytime == mpad_config.mpad_str_night
                                    and wx_dt.hour == mpad_config.mpad_int_night
                                ):
                                    found_generic = True
                                    found_generic_index = wx_time_offset["index"]
                                    break
                                else:
                                    # the only remaining option is now a full day's result
                                    if wx_time_offset["index"] < len(weather_tuples):
                                        local_daytime = None
                                        local_index = None
                                        if (
                                            wx_dt.hour
                                            in mpad_config.mpad_daytime_mapper
                                        ):
                                            # get our index
                                            local_index = wx_time_offset["index"]
                                            # and get the human readable description
                                            local_daytime = (
                                                mpad_config.mpad_daytime_mapper[
                                                    wx_dt.hour
                                                ]
                                            )

                                            # We have found at least one entry
                                            found_full = True

                                            # Now add the index and its human readable description to the directory
                                            found_full_dict[local_daytime] = local_index

                        # Did we retrieve anything but a full day's response?
                        # Then return the tuple back to the user
                        if found_generic:
                            if found_generic_index < len(weather_tuples):
                                return get_wx_data_tuple(
                                    weather_tuples=weather_tuples,
                                    index=found_generic_index,
                                )
                            else:
                                return False, None

                        # if we were supposed to gather a full day's results, try our
                        # best to provide the user with an average based on what we
                        # have gathered
                        if found_full:
                            wx_dict = {"_type": "MULTI"}
                            if mpad_config.mpad_str_morning in found_full_dict:
                                _ret, _tuple = get_wx_data_tuple(
                                    weather_tuples=weather_tuples,
                                    index=found_full_dict[mpad_config.mpad_str_morning],
                                )
                                if _ret:
                                    wx_dict[mpad_config.mpad_str_morning] = _tuple
                                    success = True
                            if mpad_config.mpad_str_daytime in found_full_dict:
                                _ret, _tuple = get_wx_data_tuple(
                                    weather_tuples=weather_tuples,
                                    index=found_full_dict[mpad_config.mpad_str_daytime],
                                )
                                if _ret:
                                    wx_dict[mpad_config.mpad_str_daytime] = _tuple
                                    success = True
                            if mpad_config.mpad_str_evening in found_full_dict:
                                _ret, _tuple = get_wx_data_tuple(
                                    weather_tuples=weather_tuples,
                                    index=found_full_dict[mpad_config.mpad_str_evening],
                                )
                                if _ret:
                                    wx_dict[mpad_config.mpad_str_evening] = _tuple
                                    success = True
                            if mpad_config.mpad_str_night in found_full_dict:
                                _ret, _tuple = get_wx_data_tuple(
                                    weather_tuples=weather_tuples,
                                    index=found_full_dict[mpad_config.mpad_str_night],
                                )
                                if _ret:
                                    wx_dict[mpad_config.mpad_str_night] = _tuple
                                    success = True
                            return success, wx_dict

    return False, None


def convert_temperature(temperature: float, units: str = "metric"):
    assert units in ("metric", "imperial")
    temperature = ((temperature * 1.8) + 32) if units == "imperial" else temperature
    return temperature


def convert_speed(speed: float, units: str = "metric"):
    assert units in ("metric", "imperial")
    speed = (speed * 2.23694) if units == "imperial" else speed
    return speed


def parse_daily_weather_from_metdotno(
    weather_tuple: dict,
    units: str,
    human_readable_text: str,
    when: str,
    when_dt: str,
    force_outgoing_unicode_messages: bool = False,
):
    """
    Parses the wx data for a given day (as returned by function
    get_daily_weather_from_openweathermapdotorg). Once the data has been
    parsed, it will build a human-readable text array, consisting of
    1..n text messages with 1..67 characters in length. This is the data
    that will ultimately be sent to the user.

    Parameters
    ==========
    weather_tuple: 'dict'
        JSON weather tuple substring for the requested day.
        Format: see https://openweathermap.org/api/one-call-api
    units: 'str'
        Unit of measure. Can either be 'metric' or 'imperial'
    human_readable_text: 'str'
        Contains the human-readable address for which the user
        has requested the wx forecast
    when: 'str':
        Contains the human-readable date/time for which the user
        has requested the wx forecast.
    when_dt: 'str'
        Parameter that tells the daytime for the wx forcast. Can
        be 'full', 'morning', 'daytime', 'evening', 'night'
    force_outgoing_unicode_messages: 'bool'
        False (default): Do not send out content as UTF-8 but
        down-convert strings to ASCII
        True: Send out all content as UTF-8

    Returns
    =======
    weather_forecast_array: 'list'
        List array, containing 1..n human readable strings with
        the parsed wx data
    """

    # Assign defaults
    w_sunrise = w_sunset = w_temp_day = w_temp_night = w_temp_eve = None
    w_temp_morn = w_pressure = w_humidity = w_dew_point = w_wind_deg = None
    w_wind_speed = w_weather_description = w_uvi = w_rain = w_snow = None
    w_clouds = w_visibility = w_temp_min = w_temp_max = w_temp = None

    # This is the array that we are going to return to the user
    weather_forecast_array = []

    # Set some unit-of-measure defaults...
    temp_uom = "c"
    wind_speed_uom = "m/s"
    rain_uom = "mm"
    snow_uom = "mm"
    sleet_uom = "mm"
    prec_uom = "mm"

    pressure_uom = "hPa"
    humidity_uom = "%"
    wind_deg_uom = ""
    clouds_uom = "%"
    visibility_uom = "m"

    # Contains either the 'when' command string or
    # a real date (if present in the wx data)
    when_text = when

    # and override some of these settings if the user has requested imperial UOM over metric defaults
    if units == "imperial":
        temp_uom = "f"
        wind_speed_uom = "mph"

    # Check if we deal with a single tuple or multiple tuples (e.g. user wants full msg
    is_multi = False

    try:
        _type = weather_tuple["_type"]
        if _type == "MULTI":
            is_multi = True
    except KeyError:
        is_multi = False

    # Start with our message
    # For now, only the user's address and the forecast string can contain 'real' UTF-8 data
    #
    # Start with the human-readable address that the user has requested.
    weather_forecast_array = make_pretty_aprs_messages(
        message_to_add=f"{when_text} {human_readable_text}",
        destination_list=weather_forecast_array,
        force_outgoing_unicode_messages=force_outgoing_unicode_messages,
    )

    # now we need to distinguish if we have one WX report or multiple ones
    # multiple reports will only get generated when the user wants to
    # receive a "full" msg report

    symbol_desc = None

    # do we need to generate a full day's report?
    if not is_multi:
        # single report - yay
        # get the human readable WX description
        if "symbol_code" in weather_tuple:
            symbol_code = weather_tuple["symbol_code"]
            if symbol_code in metdotno_symbol_mapper:
                # get the human readable description
                symbol_desc = metdotno_symbol_mapper[symbol_code]
                # and add it to the outgoing message
                weather_forecast_array = make_pretty_aprs_messages(
                    message_to_add=symbol_desc,
                    destination_list=weather_forecast_array,
                    force_outgoing_unicode_messages=force_outgoing_unicode_messages,
                )

        # get the temperature
        if "air_temperature" in weather_tuple:
            temperature = weather_tuple["air_temperature"]

            # convert to Fahrenheit, if necessary
            temperature = convert_temperature(temperature=temperature, units=units)

            # and add the message to our list
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"{round(temperature)}{temp_uom}",
                destination_list=weather_forecast_array,
                force_outgoing_unicode_messages=force_outgoing_unicode_messages,
            )

        # get the humidity
        if "relative_humidity" in weather_tuple:
            w_humidity = weather_tuple["relative_humidity"]

            # and add the message to our list
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"hum:{math.ceil(w_humidity)}{humidity_uom}",
                destination_list=weather_forecast_array,
            )

        # get the UV index
        if "ultraviolet_index_clear_sky" in weather_tuple:
            w_uvi = weather_tuple["ultraviolet_index_clear_sky"]

            # and add the message to our list
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"uvi:{w_uvi:.1f}",
                destination_list=weather_forecast_array,
            )

        # get the dew point
        if "dew_point_temperature" in weather_tuple:
            w_dew_pt = weather_tuple["dew_point_temperature"]

            # convert the temperature, if necessary
            w_dew_pt = convert_temperature(temperature=w_dew_pt, units=units)

            # and add the message to our list
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"dewpt:{math.ceil(w_dew_pt)}{temp_uom}",
                destination_list=weather_forecast_array,
            )

        # get the precipitation amount
        if "precipitation_amount" in weather_tuple:
            w_prec = weather_tuple["precipitation_amount"]

            # try to determine what we're dealing with
            if symbol_desc:
                symbol_desc = symbol_desc.lower()
                if "rain" in symbol_desc:
                    s_prec = "rain"
                    uom_prec = rain_uom
                elif "snow" in symbol_desc:
                    s_prec = "snow"
                    uom_prec = snow_uom
                elif "sleet" in symbol_desc:
                    s_prec = "sleet"
                    uom_prec = sleet_uom
                else:
                    s_prec = "prec"
                    uom_prec = prec_uom
            else:
                s_prec = "prec"
                uom_prec = prec_uom
            # and add the message to our list
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"{s_prec}:{math.ceil(w_prec)}{uom_prec}",
                destination_list=weather_forecast_array,
            )

        # get the wind speed
        if "wind_speed" in weather_tuple:
            w_wind_speed = weather_tuple["wind_speed"]

            w_wind_speed = convert_speed(speed=w_wind_speed, units=units)
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"wspd:{math.ceil(w_wind_speed)}{wind_speed_uom}",
                destination_list=weather_forecast_array,
            )

        # get the wind degrees
        if "wind_from_direction" in weather_tuple:
            w_wind_deg = weather_tuple["wind_from_direction"]

            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"wdeg:{math.ceil(w_wind_deg)}{wind_deg_uom}",
                destination_list=weather_forecast_array,
            )

        # Get the cloud coverage
        if "cloud_area_fraction" in weather_tuple:
            w_clouds = weather_tuple["cloud_area_fraction"]

            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"cld:{math.ceil(w_clouds)}{clouds_uom}",
                destination_list=weather_forecast_array,
            )

        # Get the cloud coverage
        if "air_pressure_at_sea_level" in weather_tuple:
            w_pressure = weather_tuple["air_pressure_at_sea_level"]

            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"{pressure_uom}:{math.ceil(w_pressure)}",
                destination_list=weather_forecast_array,
            )

    else:
        # We need to do the impossible :-) Try to retrieve all four wx tuples
        # whereas present in our dictionary

        wx_night = (
            weather_tuple[mpad_config.mpad_str_night]
            if mpad_config.mpad_str_night in weather_tuple
            else None
        )
        wx_morning = (
            weather_tuple[mpad_config.mpad_str_morning]
            if mpad_config.mpad_str_morning in weather_tuple
            else None
        )
        wx_daytime = (
            weather_tuple[mpad_config.mpad_str_daytime]
            if mpad_config.mpad_str_daytime in weather_tuple
            else None
        )
        wx_evening = (
            weather_tuple[mpad_config.mpad_str_evening]
            if mpad_config.mpad_str_evening in weather_tuple
            else None
        )

        # determine the human readable WX description.
        # we will use the WX description at noon
        if wx_daytime:
            if "symbol_code" in wx_daytime:
                symbol_code = wx_daytime["symbol_code"]
                if symbol_code in metdotno_symbol_mapper:
                    # get the human readable description
                    symbol_desc = metdotno_symbol_mapper[symbol_code]
                    # and add it to the outgoing message
                    weather_forecast_array = make_pretty_aprs_messages(
                        message_to_add=symbol_desc,
                        destination_list=weather_forecast_array,
                        force_outgoing_unicode_messages=force_outgoing_unicode_messages,
                    )

        # get the temperatures whereas available
        if wx_night:
            if "air_temperature" in wx_night:
                night_temperature = wx_night["air_temperature"]

                # convert to Fahrenheit, if necessary
                night_temperature = round(
                    convert_temperature(temperature=night_temperature, units=units)
                )
        else:
            night_temperature = None

        if wx_morning:
            if "air_temperature" in wx_morning:
                morning_temperature = wx_morning["air_temperature"]

                # convert to Fahrenheit, if necessary
                morning_temperature = round(
                    convert_temperature(temperature=morning_temperature, units=units)
                )
        else:
            morning_temperature = None

        if wx_daytime:
            if "air_temperature" in wx_daytime:
                daytime_temperature = wx_daytime["air_temperature"]

                # convert to Fahrenheit, if necessary
                daytime_temperature = round(
                    convert_temperature(temperature=daytime_temperature, units=units)
                )
        else:
            daytime_temperature = None

        if wx_evening:
            if "air_temperature" in wx_evening:
                evening_temperature = wx_evening["air_temperature"]

                # convert to Fahrenheit, if necessary
                evening_temperature = round(
                    convert_temperature(temperature=evening_temperature, units=units)
                )
        else:
            evening_temperature = None

        # Do we have at least one value?
        if (
            night_temperature
            or daytime_temperature
            or morning_temperature
            or night_temperature
        ):
            wx_string = ""

            if night_temperature:
                wx_string = wx_string + f"Nite:{night_temperature}{temp_uom} "

            if morning_temperature:
                wx_string = wx_string + f"Morn:{morning_temperature}{temp_uom} "

            if daytime_temperature:
                wx_string = wx_string + f"Day:{daytime_temperature}{temp_uom} "

            if evening_temperature:
                wx_string = wx_string + f"Eve:{evening_temperature}{temp_uom} "

            # remove trailing spaces whereas present
            wx_string = wx_string.rstrip()

            # and add the message to our list
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"Temp {wx_string}",
                destination_list=weather_forecast_array,
                force_outgoing_unicode_messages=force_outgoing_unicode_messages,
            )

        # get the UVI values whereas present
        uvi_night = uvi_morning = uvi_daytime = uvi_evening = 0.0

        if wx_night:
            if "ultraviolet_index_clear_sky" in wx_night:
                uvi_night = wx_night["ultraviolet_index_clear_sky"]

        if wx_morning:
            if "ultraviolet_index_clear_sky" in wx_morning:
                uvi_morning = wx_morning["ultraviolet_index_clear_sky"]

        if wx_daytime:
            if "ultraviolet_index_clear_sky" in wx_daytime:
                uvi_daytime = wx_daytime["ultraviolet_index_clear_sky"]

        if wx_evening:
            if "ultraviolet_index_clear_sky" in wx_evening:
                uvi_evening = wx_evening["ultraviolet_index_clear_sky"]

        # get the max UVI value
        uvi_max = 0.0
        if uvi_night > uvi_max:
            uvi_max = uvi_night

        if uvi_morning > uvi_max:
            uvi_max = uvi_morning

        if uvi_daytime > uvi_max:
            uvi_max = uvi_daytime

        if uvi_evening > uvi_max:
            uvi_max = uvi_evening

        # and add the message to our list
        weather_forecast_array = make_pretty_aprs_messages(
            message_to_add=f"uvi:{uvi_max:.1f}",
            destination_list=weather_forecast_array,
        )

        pass

    # Ultimately, return the array
    return weather_forecast_array


if __name__ == "__main__":
    (
        success,
        aprsdotfi_api_key,
        openweathermap_api_key,
        aprsis_callsign,
        aprsis_passcode,
        dapnet_callsign,
        dapnet_passcode,
        smtpimap_email_address,
        smtpimap_email_password,
    ) = read_program_config()

    if success:
        (
            success,
            weather_tuple,
        ) = get_daily_weather_from_metdotno(
            latitude=51.8458575,
            longitude=8.2997425,
            offset=1,
            access_mode="day",
            daytime=mpad_config.mpad_str_morning,
        )

        logger.info(pformat(weather_tuple))

        if success:
            my_weather_forecast_array = parse_daily_weather_from_metdotno(
                weather_tuple=weather_tuple,
                units="metric",
                human_readable_text="Und jetzt das Wetter ÄäÖöÜüß",
                when="Samstag",
                when_dt=mpad_config.mpad_str_morning,
                force_outgoing_unicode_messages=True,
            )
            logger.info(my_weather_forecast_array)
