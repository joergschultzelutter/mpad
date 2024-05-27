#
# Multi-Purpose APRS Daemon: met.no Modules
# Author: Joerg Schultze-Lutter, 2024
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
from utility_modules import get_local_and_utc_times, find_best_matching_time
import logging
from pprint import pformat
import math
import mpad_config
from datetime import datetime, timezone, timedelta
from math import sin, cos, atan2
import sys
from geo_conversion_modules import convert_wind_direction_to_human_text

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)

# Map the yr.no wx symbol to MPAD target msg
# source: https://api.met.no/weatherapi/locationforecast/2.0/swagger
#
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
    """
    Helper method for retrieving the correct wx tuple from
    the list of wx tuples provided by met.no

    NOTE: Every data that is retrieved here is in metric format
          and has to be converted to imperial format, if necessary

    Parameters
    ==========
    weather_tuples: 'dict'
        met.no's list of wx tuples
    index: 'int'
        the index of the element that we intend
        to retrieve from that list

    Returns
    =======
    success: 'bool'
        True if we were able to download the data
    weather_tuple: 'dict'
        JSON weather tuple for the requested day.
    """
    success = False

    if index >= len(weather_tuples):
        return False, None

    try:
        result = weather_tuples[index]["data"]["instant"]["details"]
    except (KeyError, IndexError):
        return False, None

    # we received the main wx report
    success = True

    # we received the main tuple. Now try to get the remaining
    # OPTIONAL content and add it to our tuple
    #
    # dependent on how far we go into the future, the content might
    # be listed within the next 1 / 6 / 12 hours
    #
    # precipitation may or may not be present, but the symbol code will
    # always be present - meaning that we can use it as a detection
    # for whether we were successful or not

    # First, try to get the data for hour 1
    try:
        symbol_code = weather_tuples[index]["data"]["next_1_hours"]["summary"][
            "symbol_code"
        ]
        result["symbol_code"] = symbol_code
        precipitation_amount = weather_tuples[index]["data"]["next_1_hours"]["details"][
            "precipitation_amount"
        ]
        result["precipitation_amount"] = precipitation_amount

    except (KeyError, IndexError):
        pass

    # if we didn't get data for hour 1, let's try hour 6
    if "symbol_code" not in result:
        # try to get the data for hour 6
        try:
            symbol_code = weather_tuples[index]["data"]["next_6_hours"]["summary"][
                "symbol_code"
            ]
            result["symbol_code"] = symbol_code
            precipitation_amount = weather_tuples[index]["data"]["next_6_hours"][
                "details"
            ]["precipitation_amount"]
            result["precipitation_amount"] = precipitation_amount
        except (KeyError, IndexError):
            pass

    # Finally, if we didn't get data for hour 6, let's try hour 12
    if "symbol_code" not in result:
        # try to get the data for hour 12
        try:
            symbol_code = weather_tuples[index]["data"]["next_12_hours"]["summary"][
                "symbol_code"
            ]
            result["symbol_code"] = symbol_code
            precipitation_amount = weather_tuples[index]["data"]["next_12_hours"][
                "details"
            ]["precipitation_amount"]
            result["precipitation_amount"] = precipitation_amount
        except (KeyError, IndexError):
            pass

    return success, result


def get_weather_from_metdotno(
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
    access_mode: 'str'
        Can either be 'day','hour' or 'current'
    daytime: 'str'
        Can either be 'night','morning', 'daytime', 'evening', or 'full'

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
    # yes, met.no supports larger indices but all of these entries are
    # not going to me consecutive, thus making the processing of our data difficult
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
                                weather_tuple["time"], "%Y-%m-%dT%H:%M:%S%z"
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

                        # get the local times for night / morning / noon / evening and their UTC counterparts
                        time_stamps = get_local_and_utc_times(
                            latitude=latitude, longitude=longitude, base_date=dt_utc
                        )

                        # this is the maximum gap in the dict that we are going to encounter
                        # for the first 48 hours, met.no provides a wx report on an hourly
                        # basis. All the other following days provide a wx report every 6 hours
                        # (interval and time zone are fixed; 0 / 6 / 12 / 18 h UTC)
                        max_dict_gap = 6
                        max_dict_gap_half = max_dict_gap / 2

                        # For each of the time stamps, first get the UTC value and then
                        # try to get the best matching entry
                        night_timestamp_utc = time_stamps[mpad_config.mpad_str_night][
                            "utc_time"
                        ]
                        night_timestamp_lt = find_best_matching_time(
                            target_utc_time=night_timestamp_utc,
                            timestamp_data=wx_time_offsets,
                            timestamp_data_element="timestamp",
                            gap_half=max_dict_gap_half,
                        )
                        morning_timestamp_utc = time_stamps[
                            mpad_config.mpad_str_morning
                        ]["utc_time"]
                        morning_timestamp_lt = find_best_matching_time(
                            target_utc_time=morning_timestamp_utc,
                            timestamp_data=wx_time_offsets,
                            timestamp_data_element="timestamp",
                            gap_half=max_dict_gap_half,
                        )

                        daytime_timestamp_utc = time_stamps[
                            mpad_config.mpad_str_daytime
                        ]["utc_time"]
                        daytime_timestamp_lt = find_best_matching_time(
                            target_utc_time=daytime_timestamp_utc,
                            timestamp_data=wx_time_offsets,
                            timestamp_data_element="timestamp",
                            gap_half=max_dict_gap_half,
                        )

                        evening_timestamp_utc = time_stamps[
                            mpad_config.mpad_str_evening
                        ]["utc_time"]
                        evening_timestamp_lt = find_best_matching_time(
                            target_utc_time=evening_timestamp_utc,
                            timestamp_data=wx_time_offsets,
                            timestamp_data_element="timestamp",
                            gap_half=max_dict_gap_half,
                        )
                        # Now it's time to validate these entries. Dependent on where we are located,
                        # we might encounter a situation where we do not have a fitting time stamp for
                        # the CURRENT day but only for the NEXT day - which is not what we want
                        #
                        # note that the time stamps might already be invalid at this point; we don't care
                        # about this and handle these issues in our subroutine
                        #
                        # the subroutine will check if the wx report for this day is valid (read:
                        # its time stamp is within these 6 hours). If so, we will retrieve the
                        # object's index, thus allowing it to get the actual wx element(s) from
                        # met.no's wx data set

                        # First, invalidate all index setting
                        night_timestamp_index = (
                            morning_timestamp_index
                        ) = daytime_timestamp_index = evening_timestamp_index = None

                        # now validate the time stamp and retrieve the index if the time stamp looks ok
                        night_timestamp = validate_received_timestamp(
                            utc_timestamp=night_timestamp_utc,
                            received_timestamp=night_timestamp_lt["timestamp"],
                            mode=daytime,
                            gap_full=max_dict_gap,
                        )
                        if night_timestamp:
                            night_timestamp_index = night_timestamp_lt["index"]

                        morning_timestamp = validate_received_timestamp(
                            utc_timestamp=morning_timestamp_utc,
                            received_timestamp=morning_timestamp_lt["timestamp"],
                            mode=daytime,
                            gap_full=max_dict_gap,
                        )
                        if morning_timestamp:
                            morning_timestamp_index = morning_timestamp_lt["index"]

                        daytime_timestamp = validate_received_timestamp(
                            utc_timestamp=daytime_timestamp_utc,
                            received_timestamp=daytime_timestamp_lt["timestamp"],
                            mode=daytime,
                            gap_full=max_dict_gap,
                        )
                        if daytime_timestamp:
                            daytime_timestamp_index = daytime_timestamp_lt["index"]

                        evening_timestamp = validate_received_timestamp(
                            utc_timestamp=evening_timestamp_utc,
                            received_timestamp=evening_timestamp_lt["timestamp"],
                            mode=daytime,
                            gap_full=max_dict_gap,
                        )
                        if evening_timestamp:
                            evening_timestamp_index = evening_timestamp_lt["index"]

                        # We are now in a position where we have calculated all possible values for
                        # the user's local time zone for night/morning/daytime/evening
                        # now let's check and see what the user has requested

                        if daytime in [
                            mpad_config.mpad_str_morning,
                            mpad_config.mpad_str_night,
                            mpad_config.mpad_str_daytime,
                            mpad_config.mpad_str_evening,
                        ]:
                            my_index = None
                            if daytime == mpad_config.mpad_str_night:
                                my_index = night_timestamp_index
                            elif daytime == mpad_config.mpad_str_morning:
                                my_index = morning_timestamp_index
                            elif daytime == mpad_config.mpad_str_daytime:
                                my_index = daytime_timestamp_index
                            else:
                                my_index = evening_timestamp_index

                            if my_index:
                                if my_index < len(weather_tuples):
                                    return get_wx_data_tuple(
                                        weather_tuples=weather_tuples,
                                        index=my_index,
                                    )
                                else:
                                    return False, None
                        else:  # can only be "full", see assertion
                            wx_dict = {"_type": "MULTI"}

                            # generate the entry for each index and
                            # add it to our dictionary
                            if morning_timestamp_index is not None:
                                _ret, _tuple = get_wx_data_tuple(
                                    weather_tuples=weather_tuples,
                                    index=morning_timestamp_index,
                                )
                                if _ret:
                                    wx_dict[mpad_config.mpad_str_morning] = _tuple
                                    success = True

                            # generate the entry for each index and
                            # add it to our dictionary
                            if daytime_timestamp_index is not None:
                                _ret, _tuple = get_wx_data_tuple(
                                    weather_tuples=weather_tuples,
                                    index=daytime_timestamp_index,
                                )
                                if _ret:
                                    wx_dict[mpad_config.mpad_str_daytime] = _tuple
                                    success = True

                            # generate the entry for each index and
                            # add it to our dictionary
                            if evening_timestamp_index is not None:
                                _ret, _tuple = get_wx_data_tuple(
                                    weather_tuples=weather_tuples,
                                    index=evening_timestamp_index,
                                )
                                if _ret:
                                    wx_dict[mpad_config.mpad_str_evening] = _tuple
                                    success = True

                            # generate the entry for each index and
                            # add it to our dictionary
                            if night_timestamp_index is not None:
                                _ret, _tuple = get_wx_data_tuple(
                                    weather_tuples=weather_tuples,
                                    index=night_timestamp_index,
                                )
                                if _ret:
                                    wx_dict[mpad_config.mpad_str_night] = _tuple
                                    success = True
                            return success, wx_dict
    return False, None


def validate_received_timestamp(
    utc_timestamp: datetime, received_timestamp: datetime, mode: str, gap_full: int
):
    """
    Helper method which checks and -if necessary- invalidates
    a given time stamp

    Parameters
    ==========
    utc_timestamp: 'datetime'
        reference UTC timestamp, calculated based on the lat/lon
        values earlier provided by the user
    received_timestamp: 'datetime'
        "best/closest" UTC timestamp, retrieved from met.no's wx
        data lookup table
    mode: 'str'
        The mode that the user wants us to query. This helper
        method is _only_ used for "full" day wx requests
    gap_full: 'int'
        This is the maximum gap in the dict that we are going to encounter
        For the first 48 hours, met.no provides a wx report on an hourly
        basis. All the other following days provide a wx report every 6 hours
        Therefore, our gap will be passed to this method as '6' hours

    Returns
    =======
    received_timestamp: 'datetime'
        Either 'datetime' or None, in case we had to invalidate the time stamp
    """

    # Explanation on why we need this method:
    #
    # Dependent on where we are located in this world, we may retrieve an incorrect
    # date in case the user has requested IN COMBINATION:
    #
    # - report type = "full" day report
    # - date = current date (aka offset = 0)
    # - time zone difference that is larger than 1 (e.g. program is hosted in UTC, but
    # request originated from e.g. PST)
    #
    # In such a case (especially when moving westwards from a time zone perspective),
    # the data provided my met.no may not contain a fitting entry for the desired date
    # and the algo will pick a date for the NEXT day instead. We can bypass this issue
    # by calculating the difference between our original (calculated) UTC timestamp and
    # the UTC timestamp that has been retrieved from the met.no wx table. In case the
    # difference is greater than 'gap_full' (usually: 6), we know that a different day
    # has been picked and we will therefore invalidate the entry, thus preventing it
    # from being used.

    # We only need this method for "full" day requests.
    if mode != "full" or not received_timestamp:
        return received_timestamp

    # Calculate the difference between the calculated and the retrieved timestamp
    # ensure to use the ABS value as the difference may also be negative
    if received_timestamp > utc_timestamp:
        # calculation: westwards (e.g. UTC to the U.S.)
        diff_time = received_timestamp - utc_timestamp
    else:
        # calculation: eastwards (e.g. UTC to the Japans)
        diff_time = utc_timestamp - received_timestamp

    diff_hours = abs(round(diff_time.seconds / 3600))

    # Do we exceed the maximum gap value? If yes, invalidate the response, thus
    # preventing the time stamp from being used
    if diff_hours > gap_full:
        return None

    # otherwise, return the time stamp as is
    return received_timestamp


def convert_temperature(temperature: float, units: str = "metric"):
    """
    Helper method which converts temperature degrees from the metric
    system (Celsius) to the imperial system (Fahrenheit)

    Parameters
    ==========
    temperature: 'float'
        temperature in Celsius
    units: 'str'
        either "metric" or "imperial"

    Returns
    =======
    temperature: 'float'
        Temperature value
    """
    assert units in ("metric", "imperial")
    temperature = ((temperature * 1.8) + 32) if units == "imperial" else temperature
    return temperature


def convert_speed(speed: float, units: str = "metric"):
    """
    Helper method which converts speed from the metric
    system (km/h) to the imperial system (mph)

    Parameters
    ==========
    speed: 'float'
        speed in km/h
    units: 'str'
        either "metric" or "imperial"

    Returns
    =======
    speed: 'float'
        Speed value
    """
    assert units in ("metric", "imperial")
    speed = (speed * 2.23694) if units == "imperial" else speed
    return speed


def parse_weather_from_metdotno(
    weather_tuple: dict,
    units: str,
    human_readable_text: str,
    when: str,
    when_dt: str,
    force_outgoing_unicode_messages: bool = False,
):
    """
    Parses the wx tuple (as returned by function get_weather_from_metdotno)
    Once the data has been parsed, it will build a human-readable text array,
    consisting of 1..n text messages with 1..67 characters in length.
    This is the data that will ultimately be sent to the user.

    WX forecasts for specific points in time (e.g., 12h, 'daytime', 'current') are
    literally provided "as is". In case the user has requested a ful day wx fc,
    we will try to build it for the user. Note: as met.no do not offer a full day
    forecast option, the output generated by this code may not be as accurate as
    the one that is generated on met.no's web site. Additionally, the output will be
    deliberately shortened (e.g. no uvi_min but only uvi_max values) in order to keep
    the outgoing wx message(s) as short as possible.

    Parameters
    ==========
    weather_tuple: 'dict'
        JSON weather tuple substring for the requested day.
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

    # This is the array that we are going to return to the user
    weather_forecast_array = []

    # Set some unit-of-measure defaults...
    temp_uom = "C"
    temp_uom_imperial = "F"

    wind_speed_uom = "m/s"
    wind_speed_uom_imperial = "mph"

    rain_uom = "mm"
    snow_uom = "mm"
    sleet_uom = "mm"
    prec_uom = "mm"

    pressure_uom = "hPa"
    humidity_uom = "%"
    wind_deg_uom = "dg"
    clouds_uom = "%"
    visibility_uom = "m"

    # Contains either the 'when' command string or
    # a real date (if present in the wx data)
    when_text = when

    # and override some of these settings if the user has requested imperial UOM over metric defaults
    if units == "imperial":
        temp_uom = "f"
        wind_speed_uom = "mph"

    # Check if we deal with a single tuple or multiple tuples (e.g. user wants FULL msg)
    is_multi = False
    try:
        _type = weather_tuple["_type"]
        if _type == "MULTI":
            is_multi = True
    except KeyError:
        is_multi = False

    # Start with our output message
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
            uom = wind_speed_uom
            w_wind_speed = weather_tuple["wind_speed"]
            if units == "imperial":
                w_wind_speed = convert_speed(speed=w_wind_speed, units=units)
                uom = wind_speed_uom_imperial

            # placeholder for human readable degrees
            wdir = None

            # get the wind degrees
            if "wind_from_direction" in weather_tuple:
                w_wind_deg = weather_tuple["wind_from_direction"]
                wdir = convert_wind_direction_to_human_text(degrees=w_wind_deg)

            if wdir:
                weather_forecast_array = make_pretty_aprs_messages(
                    message_to_add=f"wspd:{math.ceil(w_wind_speed)}{uom} {wdir}",
                    destination_list=weather_forecast_array,
                )
            else:
                weather_forecast_array = make_pretty_aprs_messages(
                    message_to_add=f"wspd:{math.ceil(w_wind_speed)}{uom}",
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

        #
        # END of "single time stamp" request
        #

    else:
        # This is the "Full Day" branch
        #
        # As the met.no service does not offer a full day's wx forecast,
        # we will try to build it for the user

        # get the four tuples for night, morning, daytime and evening
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

        symbol_codes = {}
        available_symbol_codes = 0

        # get the symbol_codes for this day
        if wx_night:
            if "symbol_code" in wx_night:
                sym_night = wx_night["symbol_code"]
                if sym_night in symbol_codes:
                    symbol_codes[sym_night] = symbol_codes[sym_night] + 1
                    available_symbol_codes = available_symbol_codes + 1
                else:
                    symbol_codes[sym_night] = 1

        if wx_morning:
            if "symbol_code" in wx_morning:
                sym_morning = wx_morning["symbol_code"]
                if sym_morning in symbol_codes:
                    symbol_codes[sym_morning] = symbol_codes[sym_morning] + 1
                    available_symbol_codes = available_symbol_codes + 1
                else:
                    symbol_codes[sym_morning] = 1

        if wx_daytime:
            if "symbol_code" in wx_daytime:
                sym_daytime = wx_daytime["symbol_code"]
                if sym_daytime in symbol_codes:
                    symbol_codes[sym_daytime] = symbol_codes[sym_daytime] + 1
                    available_symbol_codes = available_symbol_codes + 1
                else:
                    symbol_codes[sym_daytime] = 1

        if wx_evening:
            if "symbol_code" in wx_evening:
                sym_evening = wx_evening["symbol_code"]
                if sym_evening in symbol_codes:
                    symbol_codes[sym_evening] = symbol_codes[sym_evening] + 1
                    available_symbol_codes = available_symbol_codes + 1
                else:
                    symbol_codes[sym_evening] = 1

        # place holder for mapped symbol code in case we need it later
        # for the precipitiation output value
        precipitiation_symbol_desc = None

        # Now let's try to determine what we have received
        # did we not get four different codes? This means
        # that we got more a symbol more than once, meaning that there is a higher
        # chance that the symbol code is valid not just for a single time but
        # for the whole day
        if len(symbol_codes) != available_symbol_codes:
            max_value = max(symbol_codes.values())
            for key, value in symbol_codes.items():
                if value == max_value:
                    symbol_code = key
                    if symbol_code in metdotno_symbol_mapper:
                        # get the human readable description
                        symbol_desc = metdotno_symbol_mapper[symbol_code]
                        # save it for the precipitiation output (if necessary)
                        precipitiation_symbol_desc = symbol_desc
                        # and add it to the outgoing message
                        weather_forecast_array = make_pretty_aprs_messages(
                            message_to_add=symbol_desc,
                            destination_list=weather_forecast_array,
                            force_outgoing_unicode_messages=force_outgoing_unicode_messages,
                        )
                    break
        else:
            # We have received four different wx code symbols
            # in order to provide the user with at least one symbol
            # let's use the one that is present at noon
            #
            # determine the human readable WX description.
            # we will use the WX description at noon
            if wx_daytime:
                if "symbol_code" in wx_daytime:
                    symbol_code = wx_daytime["symbol_code"]
                    if symbol_code in metdotno_symbol_mapper:
                        # get the human readable description
                        symbol_desc = metdotno_symbol_mapper[symbol_code]
                        # save it for the precipitiation output (if necessary)
                        precipitiation_symbol_desc = symbol_desc
                        # and add it to the outgoing message
                        weather_forecast_array = make_pretty_aprs_messages(
                            message_to_add=symbol_desc,
                            destination_list=weather_forecast_array,
                            force_outgoing_unicode_messages=force_outgoing_unicode_messages,
                        )

        # get the temperatures whereas available
        night_temperature = (
            morning_temperature
        ) = daytime_temperature = evening_temperature = 0.0

        uom = temp_uom_imperial if units == "imperial" else temp_uom

        if wx_night:
            if "air_temperature" in wx_night:
                night_temperature = wx_night["air_temperature"]

                # convert to Fahrenheit, if necessary
                night_temperature = round(
                    convert_temperature(temperature=night_temperature, units=units)
                )

        if wx_morning:
            if "air_temperature" in wx_morning:
                morning_temperature = wx_morning["air_temperature"]

                # convert to Fahrenheit, if necessary
                morning_temperature = round(
                    convert_temperature(temperature=morning_temperature, units=units)
                )

        if wx_daytime:
            if "air_temperature" in wx_daytime:
                daytime_temperature = wx_daytime["air_temperature"]

                # convert to Fahrenheit, if necessary
                daytime_temperature = round(
                    convert_temperature(temperature=daytime_temperature, units=units)
                )

        if wx_evening:
            if "air_temperature" in wx_evening:
                evening_temperature = wx_evening["air_temperature"]

                # convert to Fahrenheit, if necessary
                evening_temperature = round(
                    convert_temperature(temperature=evening_temperature, units=units)
                )

        # Do we have at least one value?
        if (
            night_temperature
            or daytime_temperature
            or morning_temperature
            or night_temperature
        ):
            if night_temperature:
                wx_string = f"Nite:{night_temperature}{uom}"
                weather_forecast_array = make_pretty_aprs_messages(
                    message_to_add=wx_string,
                    destination_list=weather_forecast_array,
                    force_outgoing_unicode_messages=force_outgoing_unicode_messages,
                )

            if morning_temperature:
                wx_string = f"Morn:{morning_temperature}{uom}"
                weather_forecast_array = make_pretty_aprs_messages(
                    message_to_add=wx_string,
                    destination_list=weather_forecast_array,
                    force_outgoing_unicode_messages=force_outgoing_unicode_messages,
                )

            if daytime_temperature:
                wx_string = f"Day:{daytime_temperature}{uom}"
                weather_forecast_array = make_pretty_aprs_messages(
                    message_to_add=wx_string,
                    destination_list=weather_forecast_array,
                    force_outgoing_unicode_messages=force_outgoing_unicode_messages,
                )

            if evening_temperature:
                wx_string = f"Eve:{evening_temperature}{uom}"
                weather_forecast_array = make_pretty_aprs_messages(
                    message_to_add=wx_string,
                    destination_list=weather_forecast_array,
                    force_outgoing_unicode_messages=force_outgoing_unicode_messages,
                )

        # get the average humidity
        avg_hum = 0.0
        avg_hum_count = 0

        if wx_night:
            if "relative_humidity" in wx_night:
                avg_hum = avg_hum + wx_night["relative_humidity"]
                avg_hum_count = avg_hum_count + 1

        if wx_morning:
            if "relative_humidity" in wx_morning:
                avg_hum = avg_hum + wx_morning["relative_humidity"]
                avg_hum_count = avg_hum_count + 1

        if wx_daytime:
            if "relative_humidity" in wx_daytime:
                avg_hum = avg_hum + wx_daytime["relative_humidity"]
                avg_hum_count = avg_hum_count + 1

        if wx_evening:
            if "relative_humidity" in wx_evening:
                avg_hum = avg_hum + wx_evening["relative_humidity"]
                avg_hum_count = avg_hum_count + 1

        if avg_hum_count > 0:
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"avghum:{math.ceil(avg_hum/avg_hum_count)}{humidity_uom}",
                destination_list=weather_forecast_array,
            )

        # get the UVI values whereas present
        uvi_night = uvi_morning = uvi_daytime = uvi_evening = None

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

        # get the max UVI value. We will only concentrate on the maximum value
        # and disregard the minimum value
        uvi_max, _ = get_maxmin(
            value_night=uvi_night,
            value_morning=uvi_morning,
            value_daytime=uvi_daytime,
            value_evening=uvi_evening,
        )

        # and add the message to our list
        if uvi_max:
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"uvi:{uvi_max:.1f}",
                destination_list=weather_forecast_array,
            )

        # get the precipitation values whereas present
        pre_night = pre_morning = pre_daytime = pre_evening = 0.0

        if wx_night:
            if "precipitation_amount" in wx_night:
                pre_night = wx_night["precipitation_amount"]

        if wx_morning:
            if "precipitation_amount" in wx_morning:
                pre_morning = wx_morning["precipitation_amount"]

        if wx_daytime:
            if "precipitation_amount" in wx_daytime:
                pre_daytime = wx_daytime["precipitation_amount"]

        if wx_evening:
            if "precipitation_amount" in wx_evening:
                pre_evening = wx_evening["precipitation_amount"]

        # get the  precipitation value and use the symbol code
        # for determining what we are about to receive (rain, snow, sleet)
        # yr.no summarizes the data and we will do, too
        pre_sum = pre_night + pre_morning + pre_daytime + pre_evening
        # and use the description which we saved earlier
        symbol_desc = precipitiation_symbol_desc

        # try to determine what we're dealing with
        # if we can't determine that it is either rain,
        # snow, or sleet, then use a "precipitation" default label
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
        if pre_sum > 0.0:
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"{s_prec}:{math.ceil(pre_sum)}{uom_prec}",
                destination_list=weather_forecast_array,
            )

        # get the wind speed values whereas present
        wsp_night = wsp_morning = wsp_daytime = wsp_evening = None

        if wx_night:
            if "wind_speed" in wx_night:
                wsp_night = wx_night["wind_speed"]

        if wx_morning:
            if "wind_speed" in wx_morning:
                wsp_morning = wx_morning["wind_speed"]

        if wx_daytime:
            if "wind_speed" in wx_daytime:
                wsp_daytime = wx_daytime["wind_speed"]

        if wx_evening:
            if "wind_speed" in wx_evening:
                wsp_evening = wx_evening["wind_speed"]

        # get the max/min values
        wsp_max, wsp_min = get_maxmin(
            value_night=wsp_night,
            value_morning=wsp_morning,
            value_daytime=wsp_daytime,
            value_evening=wsp_evening,
        )

        # convert to imperial system, if necessary
        uom = wind_speed_uom
        if units == "imperial":
            if wsp_max:
                wsp_max = convert_speed(speed=wsp_max, units=units)
            if wsp_min:
                wsp_min = convert_speed(speed=wsp_min, units=units)
            uom = wind_speed_uom_imperial

        # prior to generating the message, get the wind direction

        # get the wind directions values whereas present
        wdr_night = wdr_morning = wdr_daytime = wdr_evening = None

        if wx_night:
            if "wind_from_direction" in wx_night:
                wdr_night = wx_night["wind_from_direction"]

        if wx_morning:
            if "wind_from_direction" in wx_morning:
                wdr_morning = wx_morning["wind_from_direction"]

        if wx_daytime:
            if "wind_from_direction" in wx_daytime:
                wdr_daytime = wx_daytime["wind_from_direction"]

        if wx_evening:
            if "wind_from_direction" in wx_evening:
                wdr_evening = wx_evening["wind_from_direction"]

        # get the max/min values
        wdr_max, wdr_min = get_maxmin(
            value_night=wdr_night,
            value_morning=wdr_morning,
            value_daytime=wdr_daytime,
            value_evening=wdr_evening,
        )

        # and now convert the data to a human readable heading, e.g. SSW
        wdr_max_str = convert_wind_direction_to_human_text(degrees=wdr_max)
        wdr_min_str = convert_wind_direction_to_human_text(degrees=wdr_min)

        wdr_str = ""
        # we SHOULD get a text for both, but check the status first
        if wdr_max_str or wdr_min_str:
            if wdr_max_str and wdr_min_str:
                if wdr_max_str == wdr_min_str:
                    wdr_str = f"{wdr_max_str}"
                else:
                    wdr_str = f"{wdr_min_str}-{wdr_max_str}"
            else:
                if wdr_max_str:
                    wdr_str = f"{wdr_max_str}"
                else:
                    wdr_str = f"{wdr_min_str}"

        # did wd get at least one value?
        if wsp_max and wsp_min:
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"wind:{math.ceil(wsp_min)}-{math.ceil(wsp_max)}{uom} {wdr_str}",
                destination_list=weather_forecast_array,
            )
        else:
            if wsp_min:
                weather_forecast_array = make_pretty_aprs_messages(
                    message_to_add=f"wind:{math.ceil(wsp_min)}{uom}{wdr_str} {wdr_str}",
                    destination_list=weather_forecast_array,
                )
            if wsp_max:
                weather_forecast_array = make_pretty_aprs_messages(
                    message_to_add=f"wind:{math.ceil(wsp_max)}{uom} {wdr_str}",
                    destination_list=weather_forecast_array,
                )

        # get the cloud area fraction values whereas present
        caf_night = caf_morning = caf_daytime = caf_evening = None

        if wx_night:
            if "cloud_area_fraction" in wx_night:
                caf_night = wx_night["cloud_area_fraction"]

        if wx_morning:
            if "cloud_area_fraction" in wx_morning:
                caf_morning = wx_morning["cloud_area_fraction"]

        if wx_daytime:
            if "cloud_area_fraction" in wx_daytime:
                caf_daytime = wx_daytime["cloud_area_fraction"]

        if wx_evening:
            if "cloud_area_fraction" in wx_evening:
                caf_evening = wx_evening["cloud_area_fraction"]

        # get the max value and ignore the min value
        caf_max, _ = get_maxmin(
            value_night=caf_night,
            value_morning=caf_morning,
            value_daytime=caf_daytime,
            value_evening=caf_evening,
        )

        # did we get a value?
        if caf_max:
            # build the message
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"cld:{math.ceil(caf_max)}{clouds_uom}",
                destination_list=weather_forecast_array,
            )

        # get the air pressure values whereas present
        psi_night = psi_morning = psi_daytime = psi_evening = None

        if wx_night:
            if "air_pressure_at_sea_level" in wx_night:
                psi_night = wx_night["air_pressure_at_sea_level"]

        if wx_morning:
            if "air_pressure_at_sea_level" in wx_morning:
                psi_morning = wx_morning["air_pressure_at_sea_level"]

        if wx_daytime:
            if "air_pressure_at_sea_level" in wx_daytime:
                psi_daytime = wx_daytime["air_pressure_at_sea_level"]

        if wx_evening:
            if "air_pressure_at_sea_level" in wx_evening:
                psi_evening = wx_evening["air_pressure_at_sea_level"]

        # get the max and min pressure values
        psi_max, psi_min = get_maxmin(
            value_night=psi_night,
            value_morning=psi_morning,
            value_daytime=psi_daytime,
            value_evening=psi_evening,
        )

        # this is to reduce the message length
        # if the difference between max and min is > 1
        # then we will report both values. Otherwise,
        # we will report the max value only
        if psi_max and psi_min:
            if (math.ceil(psi_max) - math.ceil(psi_min)) <= 1:
                psi_min = None

        if psi_max and psi_min:
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"prs:{math.ceil(psi_min)}-{math.ceil(psi_max)}{pressure_uom}",
                destination_list=weather_forecast_array,
            )
        else:
            if psi_max:
                weather_forecast_array = make_pretty_aprs_messages(
                    message_to_add=f"prs:{math.ceil(psi_max)}{pressure_uom}",
                    destination_list=weather_forecast_array,
                )
            if psi_min:
                weather_forecast_array = make_pretty_aprs_messages(
                    message_to_add=f"prs:{math.ceil(psi_min)}{pressure_uom}",
                    destination_list=weather_forecast_array,
                )

    # Ultimately, return the array
    return weather_forecast_array


def get_maxmin(
    value_night: float, value_morning: float, value_daytime: float, value_evening: float
):
    """
    Helper method for finding the max and min value out of four values

    Parameters
    ==========
    value_night: 'float'
        numeric value
    value_morning: 'float'
        numeric value
    value_daytime: 'float'
        numeric value
    value_evening: 'float'
        numeric value

    Returns
    =======
    value_max: 'float'
        or None if not found
    value_min: 'float'
        or None if not found
    """

    # get the max and min values for our input parameters
    value_max = sys.float_info.min
    value_min = sys.float_info.max

    if value_night:
        if value_night > value_max:
            value_max = value_night
        if value_night < value_min:
            value_min = value_night

    if value_morning:
        if value_morning > value_max:
            value_max = value_morning
        if value_morning < value_min:
            value_min = value_morning

    if value_daytime:
        if value_daytime > value_max:
            value_max = value_daytime
        if value_daytime < value_min:
            value_min = value_daytime

    if value_evening:
        if value_evening > value_max:
            value_max = value_evening
        if value_evening < value_min:
            value_min = value_evening

    # In case we didn't succeed at all, ensure that we
    # return the info accordingly
    if value_max == sys.float_info.min:
        value_max = None

    if value_min == sys.float_info.max:
        value_min = None

    return value_max, value_min


if __name__ == "__main__":
    (
        success,
        aprsdotfi_api_key,
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
        ) = get_weather_from_metdotno(
            #            latitude=51.8458575,
            #            longitude=8.2997425,
            latitude=34.03,
            longitude=-118.24,
            offset=0,
            access_mode="day",
            daytime=mpad_config.mpad_str_full,
        )

        logger.info(pformat(weather_tuple))

        if success:
            my_weather_forecast_array = parse_weather_from_metdotno(
                weather_tuple=weather_tuple,
                units="metric",
                human_readable_text="Und jetzt das Wetter ÄäÖöÜüß",
                when="Samstag",
                when_dt=mpad_config.mpad_str_full,
                force_outgoing_unicode_messages=True,
            )
            logger.info(my_weather_forecast_array)
