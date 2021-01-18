#
# Multi-Purpose APRS Daemon: OpenWeatherMap Modules
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: Uses openweathermap.org for WX report prediction
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
from datetime import datetime
from utility_modules import make_pretty_aprs_messages
from utility_modules import read_program_config
import logging


def get_daily_weather_from_openweathermapdotorg(
    latitude: float,
    longitude: float,
    date_offset: int,
    openweathermap_api_key: str,
    units: str = "metric",
    language: str = "en",
):
    """
    Gets the OWM 'onecall' weather forecast for a given latitide
    and longitude and tries to extract the raw weather data for
    a certain date. Unit (imperial or metric) is forwarded to
    OpenWeatherMap in order to get the user's wx forecast
    in his desired unit of measure

    Parameters
    ==========
    latitude: 'float'
        latitude position
    longitude: 'float'
        longitude position
    date_offset: 'int'
        numeric offset from 'today' to the desired
        target day; e.g. today = tuesday and desired
        day = thursday, then date_offset = 2
    openweathermap_api_key: str
        API key for accessing openweathermap.org api
    units: 'str'
        Unit of measure. Can either be 'metric' or 'imperial'
    language: 'str'
        ISO3166-2 language in lowercase

    Returns
    =======
    success: 'bool'
        True if we were able to download the data
    weather_tuple: 'dict'
        JSON weather tuple for the requested day.
        Format: see https://openweathermap.org/api/one-call-api
    timezone_offset: 'int'
        Shift in seconds from UTC.
        Format: see https://openweathermap.org/api/one-call-api
    timezone: 'str'
        Timezone name for the requested location
    """

    weather_tuple = timezone_offset = timezone = None
    success = False

    # fmt: off
    owm_supported_languages = [
        "af", "al", "ar", "az",
        "bg", "ca", "cz", "da",
        "de", "el", "en", "eu",
        "fa", "fi", "fr", "gl",
        "he", "hi", "hr", "hu",
        "id", "it", "ja", "kr",
        "la", "lt", "mk", "no",
        "nl", "pl", "pt", "ro",
        "ru", "sv", "se", "sk",
        "sl", "sp", "es", "sr",
        "th", "tr", "ua", "uk",
        "vi", "cn", "tw", "zu",
    ]
    # fmt: on

    if language not in owm_supported_languages:
        language = "en"
    if language == "cn":
        language = "zh_cn"
    if language == "tw":
        language = "zh_tw"

    # return 'false' if user has requested a day that is out of bounds
    if date_offset < 0 or date_offset > 7:
        return success, weather_tuple, timezone_offset, timezone_offset

    if units not in ["imperial", "metric"]:
        return success, weather_tuple, timezone_offset, timezone_offset

    # Issue the request to OWN
    url = f"https://api.openweathermap.org/data/2.5/onecall?lat={latitude}&lon={longitude}&units={units}&exclude=hourly,minutely&lang={language}&appid={openweathermap_api_key}"
    resp = requests.get(url)
    if resp.status_code == 200:
        x = resp.json()
        # get weather for the given day offset
        if "daily" in x:
            weather_tuple = x["daily"][date_offset]
            success = True
        if "timezone_offset" in x:
            timezone_offset = x["timezone_offset"]
        if "timezone" in x:
            timezone = x["timezone"]

    return success, weather_tuple, timezone_offset, timezone


def parse_daily_weather_from_openweathermapdotorg(
    weather_tuple: dict, units: str, requested_address: str, when: str, when_dt: str
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
    requested_address: 'str'
        Contains the human-readable address for which the user
        has requested the wx forecast
    when: 'str':
        Contains the human-readable date/time for which the user
        has requested the wx forecast.
    when_dt: 'str'
        Parameter that tells the daytime for the wx forcast. Can
        be 'full', 'morning', 'daytime', 'evening', 'night'


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
    w_clouds = w_visibility = None

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
            tmp_dt = datetime.fromtimestamp(w_dt)
            when_text = datetime.strftime(tmp_dt, "%d-%b-%y")
        if "sunrise" in weather_tuple:
            w_sunrise = weather_tuple["sunrise"]
        if "sunset" in weather_tuple:
            w_sunset = weather_tuple["sunset"]
        if "temp" in weather_tuple:
            w_temp_day = weather_tuple["temp"]["day"]
            w_temp_night = weather_tuple["temp"]["night"]
            w_temp_eve = weather_tuple["temp"]["eve"]
            w_temp_morn = weather_tuple["temp"]["morn"]
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
        if "rain" in weather_tuple:
            w_rain = weather_tuple["rain"]
        if "snow" in weather_tuple:
            w_snow = weather_tuple["snow"]
        if "visibility" in weather_tuple:
            w_visibility = weather_tuple["visibility"]

        # Now we have everything we need. Build the content that we
        # want to return back to the user. We use a function that
        # prevents the final messages from being split up in the
        # middle of the respective substrings.

        # Start with the human-readable address that the user has requested.
        weather_forecast_array = make_pretty_aprs_messages(
            f"{when_text} {requested_address}", weather_forecast_array
        )

        # Add the forecast string
        if w_weather_description:
            weather_forecast_array = make_pretty_aprs_messages(
                w_weather_description, weather_forecast_array
            )

        # Add temperatures whereas applicable per 'when_dt' parameters
        if w_temp_day or w_temp_morn or w_temp_eve or w_temp_night:
            if w_temp_morn and when_dt in ["full", "morning"]:
                weather_forecast_array = make_pretty_aprs_messages(
                    f"morn:{w_temp_morn:.0f}{temp_uom}", weather_forecast_array
                )
            if w_temp_day and when_dt in ["full", "daytime"]:
                weather_forecast_array = make_pretty_aprs_messages(
                    f"day:{w_temp_day:.0f}{temp_uom}", weather_forecast_array
                )
            if w_temp_eve and when_dt in ["full", "evening"]:
                weather_forecast_array = make_pretty_aprs_messages(
                    f"eve:{w_temp_eve:.0f}{temp_uom}", weather_forecast_array
                )
            if w_temp_night and when_dt in ["full", "night"]:
                weather_forecast_array = make_pretty_aprs_messages(
                    f"nite:{w_temp_night:.0f}{temp_uom}", weather_forecast_array
                )

        # Sunrise and Sunset
        if w_sunset and w_sunrise:
            tmp1 = datetime.fromtimestamp(w_sunrise)
            tmp2 = datetime.fromtimestamp(w_sunset)
            weather_forecast_array = make_pretty_aprs_messages(
                f"sunrise/set {tmp1.hour:02d}:{tmp1.minute:02d}/{tmp2.hour:02d}:{tmp2.minute:02d}UTC",
                weather_forecast_array,
            )
        elif w_sunrise and not w_sunset:
            tmp = datetime.fromtimestamp(w_sunrise)
            weather_forecast_array = make_pretty_aprs_messages(
                f"sunrise {tmp.hour}:{tmp.minute}UTC", weather_forecast_array
            )
        else:
            tmp = datetime.fromtimestamp(w_sunset)
            weather_forecast_array = make_pretty_aprs_messages(
                f"sunset {tmp.hour}:{tmp.minute}UTC", weather_forecast_array
            )

        # Add remaining parameters
        if w_rain:
            weather_forecast_array = make_pretty_aprs_messages(
                f"rain:{w_rain:.0f}{rain_uom}", weather_forecast_array
            )
        if w_snow:
            weather_forecast_array = make_pretty_aprs_messages(
                f"snow:{w_snow:.0f}{snow_uom}", weather_forecast_array
            )
        if w_clouds:
            weather_forecast_array = make_pretty_aprs_messages(
                f"clouds:{w_clouds}{clouds_uom}", weather_forecast_array
            )
        if w_uvi:
            weather_forecast_array = make_pretty_aprs_messages(
                f"uvi:{w_uvi:.1f}", weather_forecast_array
            )
        if w_pressure:
            weather_forecast_array = make_pretty_aprs_messages(
                f"{pressure_uom}:{w_pressure}", weather_forecast_array
            )
        if w_humidity:
            weather_forecast_array = make_pretty_aprs_messages(
                f"hum:{w_humidity}{humidity_uom}", weather_forecast_array
            )
        if w_dew_point:
            weather_forecast_array = make_pretty_aprs_messages(
                f"dewpt:{w_dew_point:.0f}{temp_uom}", weather_forecast_array
            )
        if w_wind_speed:
            weather_forecast_array = make_pretty_aprs_messages(
                f"wndspd:{w_wind_speed:.0f}{wind_speed_uom}", weather_forecast_array
            )
        if w_wind_deg:
            weather_forecast_array = make_pretty_aprs_messages(
                f"wnddeg:{w_wind_deg}{wind_deg_uom}", weather_forecast_array
            )
        if w_visibility:
            weather_forecast_array = make_pretty_aprs_messages(
                f"vis:{w_visibility}{visibility_uom}", weather_forecast_array
            )

        # Ultimately, return the array
        return weather_forecast_array


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
    )
    logger = logging.getLogger(__name__)

    success, aprsdotfi_api_key, openweathermap_api_key = read_program_config()
    if success:
        (
            success,
            weather_tuple,
            timezone_offset,
            timezone,
        ) = get_daily_weather_from_openweathermapdotorg(
            51.8458575, 8.2997425, 0, openweathermap_api_key, "metric"
        )
        if success:
            my_weather_forecast_array = parse_daily_weather_from_openweathermapdotorg(
                weather_tuple, "metric", "Und jetzt das Wetter", "Samstag", "full"
            )
            logger.info(my_weather_forecast_array)
