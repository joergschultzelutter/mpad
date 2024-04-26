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
from utility_modules import make_pretty_aprs_messages
from utility_modules import read_program_config
import logging
from pprint import pformat
import math
import mpad_config
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def get_daily_weather_from_yrdotcom(
    latitude: float,
    longitude: float,
    offset: int,
    units: str = "metric",
    access_mode: str = "day",
    daytime: str = "daytime"
):
    """
    Gets the yr.no weather forecast for a given latitide
    and longitude and tries to extract the raw weather data for
    a certain date.

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
        Format: see https://openweathermap.org/api/one-call-api
    """

    headers = {"User-Agent": mpad_config.mpad_default_user_agent}

    weather_tuple = weather_tuples = None
    success = False

    assert access_mode in ["day", "hour", "current"]
    assert daytime in ["full","morning","daytime","evening","night"]


    # return 'false' if user has requested a day that is out of bounds
    if access_mode == "day":
        if offset < 0 or offset > 7:
            return success, weather_tuple
    if access_mode == "hour":
        if offset < 0 or offset > 47:
            return success, weather_tuple

    if units not in ["imperial", "metric"]:
        return success, weather_tuple

    # Prepare the URL
    url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={latitude}&lon={longitude}"
    try:
        resp = requests.get(url=url,headers=headers)
    except requests.exceptions.RequestException as e:
        logger.error(msg="{e}")
        resp = None
    if resp:
        if resp.status_code == 203:
            logger.error(msg="Request to yr.no indicates API deprecation - see https://developer.yr.no/doc/locationforecast/HowTO/")
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

                    # build a generic index, thus allowing us to access the element
                    # directly at a later point in time
                    for index, weather_tuple in enumerate(weather_tuples):
                        dt = datetime.strptime(weather_tuple["time"], "%Y-%m-%dT%H:%M:%SZ")
                        unix_timestamp = int(dt.replace(tzinfo=timezone.utc).timestamp())
                        wx_time_offsets[unix_timestamp] = {"date":weather_tuple["time"],"index": index,"hour":dt.hour}

                    # get our current UTC timestamp
                    dt_utc = datetime.utcnow()
                    pass
                    pass
                    pass




            x = response

            if "current" in x and access_mode == "current":
                weather_tuple = x["current"]
                success = True
            elif "daily" in x and access_mode == "day":
                if offset < len(x["daily"]):
                    weather_tuple = x["daily"][offset]
                    success = True
            elif "hourly" in x and access_mode == "hour":
                if offset < len(x["hourly"]):
                    weather_tuple = x["hourly"][offset]
                    success = True
            logger.info(msg=pformat(weather_tuple))
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
        ) = get_daily_weather_from_yrdotcom(
            latitude=51.8458575,
            longitude=8.2997425,
            offset=0,
            units="metric",
            access_mode="day",
            daytime="daytime"
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
