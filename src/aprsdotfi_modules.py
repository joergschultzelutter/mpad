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
from datetime import datetime
from utility_modules import read_program_config
import logging
import mpad_config

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


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
    lasttime: 'datetime'
        the time when the target last reported this (current) position
        If not found, returned default value is of value datetime.min
        (0001-01-01 00:00:00)
    aprsfi_callsign: 'str'
        Call sign converted to uppercase
    """
    headers = {
        "User-Agent": mpad_config.mpad_default_user_agent
    }

    success = False
    latitude = longitude = altitude = 0.0

    lasttime = datetime.min  # placeholder value in case we can't determine the aprs.fi 'lasttime' information
    result = "fail"
    found = 0  # number of entries found in aprs.fi request (if any)

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
                    # We extract only the very first entry and disregard
                    # entries 2..n whereas ever present
                    # now extract lat/lon/altitude/lasttime

                    # Check if lat/lon are present; this is the essential information that we need to continue
                    if (
                        "lat" not in json_content["entries"][0]
                        and "lng" in json_content["entries"][0]
                    ):
                        success = False
                    else:
                        success = True
                        latitude = float(json_content["entries"][0]["lat"])
                        longitude = float(json_content["entries"][0]["lng"])
                    # Now check for our optional fields
                    if "altitude" in json_content["entries"][0]:
                        altitude = float(json_content["entries"][0]["altitude"])
                    if "lasttime" in json_content["entries"][0]:
                        _mylast = float(json_content["entries"][0]["lasttime"])
                        lasttime = datetime.utcfromtimestamp(_mylast)

        return success, latitude, longitude, altitude, lasttime, aprsfi_callsign


if __name__ == "__main__":
    (
        success,
        aprsdotfi_api_key,
        openweathermapdotorg_api_key,
        aprsis_callsign,
        aprsis_passcode,
        dapnet_callsign,
        dapnet_passcode,
    ) = read_program_config()
    if success:
        logger.info(get_position_on_aprsfi("DF1JSL-8", aprsdotfi_api_key))
