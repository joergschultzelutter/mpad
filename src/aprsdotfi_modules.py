#
# Multi-Purpose APRS Daemon: aprs.fi user data retrieval
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: get user's lat/lon/altitude from aprs.fi
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
from utility_modules import read_program_config
import logging

# APRS.fi access key (we get this value from the config file settings)


def get_position_on_aprsfi(aprsfi_callsign: str, aprsdotfi_api_key: str):
    """
    Get the position of the given call sign on aprs.fi
    Call sign is taken 'as is', e.g. with or without SSID.

    If a query for the user's call sign returns more than one position,
    then only the very first call sign position on aprs.fi
    is used by the program.

    Parameters
    ==========
    aprsfi_callsign: 'str'
        Call sign that we want to get the lat/lon coordinates for
    aprsdotfi_api_key: 'str'
        aprs.fi api access key

    Returns
    =======
    success: 'bool'
        True if call was successful
    latitude: 'float'
        latitude position if user was found on aprs.fi
    longitude: 'float'
        longitude position if user was found on aprs.fi
    altitude: 'float'
        altitude in meters if user was found on aprs.fi
    aprsfi_callsign: 'str'
        Call sign converted to uppercase
    """
    headers = {
        "User-Agent": "multi-purpose-aprs-daemon/0.0.1-internal-alpha (+https://github.com/joergschultzelutter/mpad/)"
    }

    success = False
    latitude = longitude = altitude = 0.0
    result = "fail"
    found = 0

    aprsfi_callsign = aprsfi_callsign.upper()

    try:
        resp = requests.get(
            f"https://api.aprs.fi/api/get?name={aprsfi_callsign}&what=loc&apikey={aprsdotfi_api_key}&format=json",
            headers=headers,
        )
    except:
        resp = None
    if resp:
        if resp.status_code == 200:
            json_content = resp.json()
            # extract web service result. Can either be 'ok' or 'fail'
            if "result" in json_content:
                result = json_content["result"]
            if result == "ok":
                # extract number of result sets in the response. Must be > 0
                # regardless of the available number of results, we will only
                # use the first result
                if "found" in json_content:
                    found = json_content["found"]
                if found > 0:
                    # let's assume that all is good
                    success = True
                    # now extract lat/lon/altitude
                    if "lat" in json_content["entries"][0]:
                        latitude = float(json_content["entries"][0]["lat"])
                    if "lng" in json_content["entries"][0]:
                        longitude = float(json_content["entries"][0]["lng"])
                    if "altitude" in json_content["entries"][0]:
                        altitude = float(json_content["entries"][0]["altitude"])
        return success, latitude, longitude, altitude, aprsfi_callsign


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
    )
    logger = logging.getLogger(__name__)
    success, aprsdotfi_api_key, openweathermapdotorg_api_key = read_program_config()
    if success:
        logger.debug(get_position_on_aprsfi("DF1JSL-1", aprsdotfi_api_key))
