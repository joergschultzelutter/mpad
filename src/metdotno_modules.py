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
    "heavysleet": "HEavySleet",
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


def calculate_daily_forecast(
    pressure_values: list,
    temperature_values: list,
    cloudiness_values: list,
    humidity_values: list,
    wind_direction_degrees: list,
    wind_speed_values: list,
):
    # Calculate average pressure
    avg_pressure = sum(pressure_values) / len(pressure_values)

    # Calculate average temperature
    avg_temperature = sum(temperature_values) / len(temperature_values)

    # Calculate average cloudiness
    avg_cloudiness = sum(cloudiness_values) / len(cloudiness_values)

    # Calculate average humidity
    avg_humidity = sum(humidity_values) / len(humidity_values)

    # Convert wind direction degrees to radians for vector addition
    wind_direction_radians = [
        degrees * (3.14159 / 180) for degrees in wind_direction_degrees
    ]

    # Calculate x and y components of wind direction vectors
    wind_direction_x = sum([cos(rad) for rad in wind_direction_radians]) / len(
        wind_direction_radians
    )
    wind_direction_y = sum([sin(rad) for rad in wind_direction_radians]) / len(
        wind_direction_radians
    )

    # Calculate resulting wind direction
    avg_wind_direction_degrees = atan2(wind_direction_y, wind_direction_x) * (
        180 / 3.14159
    )

    # Ensure wind direction is within [0, 360) degrees
    avg_wind_direction_degrees %= 360

    # Calculate average wind speed
    avg_wind_speed = sum(wind_speed_values) / len(wind_speed_values)

    return (
        round(avg_pressure),
        round(avg_temperature, 1),
        round(avg_cloudiness),
        round(avg_humidity),
        round(avg_wind_direction_degrees),
        round(avg_wind_speed, 1),
    )


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
                        try:
                            result = weather_tuples[0]["data"]["instant"]["details"]
                        except KeyError:
                            return False, None
                        # we received the main tuple. Now try to get the remaining
                        # optional content and add it to our tuple
                        success = True
                        try:
                            symbol_code = weather_tuples[0]["data"]["next_1_hours"][
                                "summary"
                            ]["symbol_code"]
                            result["symbol_code"] = symbol_code
                        except KeyError:
                            pass
                        try:
                            precipitation_amount = weather_tuples[0]["data"][
                                "next_1_hours"
                            ]["details"]["precipitation_amount"]
                            result["precipitation_amount"] = precipitation_amount
                        except KeyError:
                            pass
                        return success, result

                    # if user wants an hour offset, try to return that
                    # one back to the user
                    elif access_mode == "hour":
                        if len(weather_tuples) > offset:
                            try:
                                result = weather_tuples[offset]["data"]["instant"][
                                    "details"
                                ]
                            except KeyError:
                                return False, None

                            # we received the main tuple. Now try to get the remaining
                            # optional content and add it to our tuple
                            success = True
                            try:
                                symbol_code = weather_tuples[offset]["data"][
                                    "next_1_hours"
                                ]["summary"]["symbol_code"]
                                result["symbol_code"] = symbol_code
                            except KeyError:
                                pass
                            try:
                                precipitation_amount = weather_tuples[offset]["data"][
                                    "next_1_hours"
                                ]["details"]["precipitation_amount"]
                                result["precipitation_amount"] = precipitation_amount
                            except KeyError:
                                pass
                            return success, result
                    else:
                        # "day" mode access
                        #
                        # In comparison to OpenWeatherMap, yr.no's integration is a tad messy
                        # as there are no information clusters on e.g. "noon", "night" et al.
                        # Additionally, there is no "full day" overview, thus we need to rebuild
                        # all of this ourselves in case the user requests it
                        #
                        # build a generic index secondary index on our data
                        # not really required but I am a lazy guy and
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
                        generic_index = -1

                        # used whenever a full day's results ARE requested
                        found_full = False
                        full_pressure = []
                        full_temperature = []
                        full_cloudiness = []
                        full_humidity = []
                        full_wind_direction = []
                        full_wind_speed = []

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
                                    daytime == "morning"
                                    and wx_dt.hour == mpad_config.mpad_wx_morning
                                ):
                                    found_generic = True
                                    found_generic_index = wx_time_offset["index"]
                                    break
                                elif (
                                    daytime == "daytime"
                                    and wx_dt.hour == mpad_config.mpad_wx_daytime
                                ):
                                    found_generic = True
                                    found_generic_index = wx_time_offset["index"]
                                    break
                                elif (
                                    daytime == "evening"
                                    and wx_dt.hour == mpad_config.mpad_wx_evening
                                ):
                                    found_generic = True
                                    found_generic_index = wx_time_offset["index"]
                                    break
                                elif (
                                    daytime == "night"
                                    and wx_dt.hour == mpad_config.mpad_wx_night
                                ):
                                    found_generic = True
                                    found_generic_index = wx_time_offset["index"]
                                    break
                                else:
                                    # the only remaining option is now a full day's result
                                    # Add the values to a list and we will deal with them later
                                    if wx_time_offset["index"] < len(weather_tuples):
                                        try:
                                            full_pressure.append(
                                                weather_tuples[wx_time_offset["index"]][
                                                    "data"
                                                ]["instant"]["details"][
                                                    "air_pressure_at_sea_level"
                                                ]
                                            )
                                            full_cloudiness.append(
                                                weather_tuples[wx_time_offset["index"]][
                                                    "data"
                                                ]["instant"]["details"][
                                                    "cloud_area_fraction"
                                                ]
                                            )
                                            full_temperature.append(
                                                weather_tuples[wx_time_offset["index"]][
                                                    "data"
                                                ]["instant"]["details"][
                                                    "air_temperature"
                                                ]
                                            )
                                            full_humidity.append(
                                                weather_tuples[wx_time_offset["index"]][
                                                    "data"
                                                ]["instant"]["details"][
                                                    "relative_humidity"
                                                ]
                                            )
                                            full_wind_speed.append(
                                                weather_tuples[wx_time_offset["index"]][
                                                    "data"
                                                ]["instant"]["details"]["wind_speed"]
                                            )
                                            full_wind_direction.append(
                                                weather_tuples[wx_time_offset["index"]][
                                                    "data"
                                                ]["instant"]["details"][
                                                    "wind_from_direction"
                                                ]
                                            )
                                            found_full = True
                                        except KeyError:
                                            found_full = False

                        # Did we retrieve anything but a full day's response?
                        # Then return the tuple back to the user
                        if found_generic:
                            if generic_index < len(weather_tuples):
                                try:
                                    success = True
                                    return (
                                        success,
                                        weather_tuples[generic_index]["data"][
                                            "instant"
                                        ]["details"],
                                    )
                                except KeyError:
                                    return False, None
                        # if we were supposed to gather a full day's results, try our
                        # best to provide the user with an average based on what we
                        # have gathered
                        if found_full:
                            (
                                avg_pressure,
                                avg_temperature,
                                avg_cloudiness,
                                avg_humidity,
                                avg_wind_direction_degrees,
                                avg_wind_speed,
                            ) = calculate_daily_forecast(
                                pressure_values=full_pressure,
                                temperature_values=full_temperature,
                                cloudiness_values=full_cloudiness,
                                humidity_values=full_humidity,
                                wind_direction_degrees=full_wind_direction,
                                wind_speed_values=full_wind_speed,
                            )
                            success = True
                            response = {
                                "air_pressure_at_sea_level": avg_pressure,
                                "air_temperature": avg_temperature,
                                "cloud_area_fraction": avg_cloudiness,
                                "relative_humidity": avg_humidity,
                                "wind_from_direction": avg_wind_direction_degrees,
                                "wind_speed": avg_wind_speed,
                            }
                            return success, response

    return success, weather_tuple


def parse_daily_weather_from_openweathermapdotorg(
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

    # Now extract content from the JSON import (if present)
    if weather_tuple:
        # If we have a time stamp, then let's provide a real date to the user
        if "dt" in weather_tuple:
            w_dt = weather_tuple["dt"]
            tmp_dt = datetime.utcfromtimestamp(w_dt)
            when_text = datetime.strftime(tmp_dt, "%d-%b-%y")
        if "sunrise" in weather_tuple:
            w_sunrise = weather_tuple["sunrise"]
        if "sunset" in weather_tuple:
            w_sunset = weather_tuple["sunset"]
        # hourly reports: temp = float value, daily reports: temp = dict value
        if "temp" in weather_tuple:
            subset = weather_tuple["temp"]
            if isinstance(subset, dict):
                if "day" in subset:
                    w_temp_day = subset["day"]
                if "night" in subset:
                    w_temp_night = weather_tuple["temp"]["night"]
                if "eve" in subset:
                    w_temp_eve = weather_tuple["temp"]["eve"]
                if "morn" in subset:
                    w_temp_morn = weather_tuple["temp"]["morn"]
                if "min" in subset:
                    w_temp_min = weather_tuple["temp"]["min"]
                if "max" in subset:
                    w_temp_max = weather_tuple["temp"]["max"]
            elif isinstance(subset, float):
                w_temp = weather_tuple["temp"]
        if "pressure" in weather_tuple:
            w_pressure = weather_tuple["pressure"]
        if "humidity" in weather_tuple:
            w_humidity = weather_tuple["humidity"]
        if "dew_point" in weather_tuple:
            w_dew_point = weather_tuple["dew_point"]
        if "wind_speed" in weather_tuple:
            w_wind_speed = weather_tuple["wind_speed"]
        if "wind_deg" in weather_tuple:
            w_wind_deg = weather_tuple["wind_deg"]
        if "weather" in weather_tuple:
            w_weather_description = weather_tuple["weather"][0]["description"]
        if "uvi" in weather_tuple:
            w_uvi = weather_tuple["uvi"]
        if "clouds" in weather_tuple:
            w_clouds = weather_tuple["clouds"]
        # when hourly data was requested, the result comes as a
        # dictionary - otherwise as a float
        if "rain" in weather_tuple:
            subset = weather_tuple["rain"]
            if isinstance(subset, float):
                w_rain = weather_tuple["rain"]
            elif isinstance(subset, dict):
                if "1h" in subset:
                    w_rain = subset["1h"]
        # when hourly data was requested, the result comes as a
        # dictionary - otherwise as a float
        if "snow" in weather_tuple:
            subset = weather_tuple["snow"]
            if isinstance(subset, float):
                w_snow = weather_tuple["snow"]
            elif isinstance(subset, dict):
                if "1h" in subset:
                    w_snow = subset["1h"]
        if "visibility" in weather_tuple:
            w_visibility = weather_tuple["visibility"]

        # Now we have everything we need. Build the content that we
        # want to return back to the user. We use a function that
        # prevents the final messages from being split up in the
        # middle of the respective substrings.

        # For now, only the user's address and the forecast string can contain 'real' UTF-8 data
        #
        # Start with the human-readable address that the user has requested.
        weather_forecast_array = make_pretty_aprs_messages(
            message_to_add=f"{when_text} {human_readable_text}",
            destination_list=weather_forecast_array,
            force_outgoing_unicode_messages=force_outgoing_unicode_messages,
        )

        # Add the forecast string
        if w_weather_description:
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=w_weather_description,
                destination_list=weather_forecast_array,
                force_outgoing_unicode_messages=force_outgoing_unicode_messages,
            )

        # Add temperatures whereas applicable per 'when_dt' parameters
        if w_temp_day or w_temp_morn or w_temp_eve or w_temp_night or w_temp:
            if w_temp_morn and when_dt in ["full", "morning"]:
                weather_forecast_array = make_pretty_aprs_messages(
                    message_to_add=f"morn:{round(w_temp_morn)}{temp_uom}",
                    destination_list=weather_forecast_array,
                )
            if w_temp_day and when_dt in ["full", "daytime"]:
                weather_forecast_array = make_pretty_aprs_messages(
                    message_to_add=f"day:{round(w_temp_day)}{temp_uom}",
                    destination_list=weather_forecast_array,
                )
            if w_temp_eve and when_dt in ["full", "evening"]:
                weather_forecast_array = make_pretty_aprs_messages(
                    message_to_add=f"eve:{round(w_temp_eve)}{temp_uom}",
                    destination_list=weather_forecast_array,
                )
            if w_temp_night and when_dt in ["full", "night"]:
                weather_forecast_array = make_pretty_aprs_messages(
                    message_to_add=f"nite:{round(w_temp_night)}{temp_uom}",
                    destination_list=weather_forecast_array,
                )
            if w_temp:  # hourly report
                weather_forecast_array = make_pretty_aprs_messages(
                    message_to_add=f"temp:{round(w_temp)}{temp_uom}",
                    destination_list=weather_forecast_array,
                )

        # Sunrise and Sunset
        if w_sunset and w_sunrise:
            tmp1 = datetime.utcfromtimestamp(w_sunrise)
            tmp2 = datetime.utcfromtimestamp(w_sunset)
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"sunrise/set {tmp1.hour:02d}:{tmp1.minute:02d}/{tmp2.hour:02d}:{tmp2.minute:02d}UTC",
                destination_list=weather_forecast_array,
            )
        elif w_sunrise and not w_sunset:
            tmp = datetime.utcfromtimestamp(w_sunrise)
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"sunrise {tmp.hour}:{tmp.minute}UTC",
                destination_list=weather_forecast_array,
            )
        elif w_sunset and not w_sunrise:
            tmp = datetime.utcfromtimestamp(w_sunset)
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"sunset {tmp.hour}:{tmp.minute}UTC",
                destination_list=weather_forecast_array,
            )

        # Add remaining parameters
        if w_rain:
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"rain:{math.ceil(w_rain)}{rain_uom}",
                destination_list=weather_forecast_array,
            )
        if w_snow:
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"snow:{math.ceil(w_snow)}{snow_uom}",
                destination_list=weather_forecast_array,
            )
        if w_clouds:
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"clouds:{w_clouds}{clouds_uom}",
                destination_list=weather_forecast_array,
            )
        if w_uvi:
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"uvi:{w_uvi:.1f}",
                destination_list=weather_forecast_array,
            )
        if w_pressure:
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"{pressure_uom}:{w_pressure}",
                destination_list=weather_forecast_array,
            )
        if w_humidity:
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"hum:{w_humidity}{humidity_uom}",
                destination_list=weather_forecast_array,
            )
        if w_dew_point:
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"dewpt:{math.ceil(w_dew_point)}{temp_uom}",
                destination_list=weather_forecast_array,
            )
        if w_wind_speed:
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"wndspd:{math.ceil(w_wind_speed)}{wind_speed_uom}",
                destination_list=weather_forecast_array,
            )
        if w_wind_deg:
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"wnddeg:{w_wind_deg}{wind_deg_uom}",
                destination_list=weather_forecast_array,
            )
        if w_visibility:
            weather_forecast_array = make_pretty_aprs_messages(
                message_to_add=f"vis:{w_visibility}{visibility_uom}",
                destination_list=weather_forecast_array,
            )

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
            offset=12,
            access_mode="hour",
            daytime="full",
        )

        success = False
        if success:
            my_weather_forecast_array = parse_daily_weather_from_openweathermapdotorg(
                weather_tuple=weather_tuple,
                units="metric",
                human_readable_text="Und jetzt das Wetter ÄäÖöÜüß",
                when="Samstag",
                when_dt="full",
                force_outgoing_unicode_messages=True,
            )
            logger.info(my_weather_forecast_array)
