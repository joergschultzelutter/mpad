#
# Multi-Purpose APRS Daemon: Airport Data Modules
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: DAPNET communication code
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
import logging
import re
import json
from utility_modules import read_program_config, convert_text_to_plain_ascii
import requests
from requests.auth import HTTPBasicAuth
import mpad_config


def send_dapnet_message(
    from_callsign: str,
    to_callsign: str,
    message: str,
    dapnet_login_callsign: str,
    dapnet_login_passcode: str,
    dapnet_high_priority_message: bool = False,
):
    success = False
    response = None

    if dapnet_login_callsign.upper() == "N0CALL":
        response = "MPAD: DAPNET API credentials are not configured, cannot send msg"
        success = False
    else:
        # Convert the message string to plain ASCII
        message_txt = convert_text_to_plain_ascii(message_string=message)

        # Get rid of the SSID in the FROM callsign (if present)
        regex_string = r"([a-zA-Z0-9]{1,3}[0-9][a-zA-Z0-9]{0,3})-([a-zA-Z0-9]{1,2})"
        matches = re.search(
            pattern=regex_string, string=from_callsign, flags=re.IGNORECASE
        )
        if matches:
            dapnet_from_callsign = matches[1]
        else:
            dapnet_from_callsign = from_callsign

        # Now do the same thing with the target callsign
        matches = re.search(
            pattern=regex_string, string=to_callsign, flags=re.IGNORECASE
        )
        if matches:
            dapnet_to_callsign = matches[1]
        else:
            dapnet_to_callsign = to_callsign

        # shorten the message text in the unlikely case that it is longer than the
        # maximum supported length. DAPNET can process up to 80 chars; we need to
        # reduce this number by len(callsign)+2 for the message header
        message_txt = message_txt[0 : (80 - len(dapnet_from_callsign) - 2)]

        dapnet_payload = {
            "text": f"{dapnet_from_callsign.upper()}: {message_txt}",
            "callSignNames": [f"{dapnet_to_callsign.upper()}"],
            "transmitterGroupNames": [
                f"{mpad_config.mpad_dapnet_api_transmitter_group}"
            ],
            "emergency": dapnet_high_priority_message,
        }
        dapnet_payload_json = json.dumps(dapnet_payload)
        response = requests.post(
            url=mpad_config.mpad_dapnet_api_server,
            data=dapnet_payload_json,
            auth=HTTPBasicAuth(
                username=dapnet_login_callsign, password=dapnet_login_passcode
            ),
        )  # Exception handling einbauen
        if response.status_code == 201:
            success = True
            response = f"DAPNET message dispatch to {dapnet_to_callsign} via '{mpad_config.mpad_dapnet_api_transmitter_group}' successful"
        else:
            response = f"DAPNET message dispatch to {dapnet_to_callsign} failed: HTTP{response.status_code}"
            success = False
    return success, response


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
    )
    logger = logging.getLogger(__name__)

    (
        success,
        aprsdotfi_api_key,
        openweathermap_api_key,
        aprsis_callsign,
        aprsis_passcode,
        dapnet_login_callsign,
        dapnet_login_passcode,
    ) = read_program_config()
    if success:
        logger.debug(
            send_dapnet_message(
                from_callsign="DF1JSL-1",
                to_callsign="DF1JSL-8",
                message="00000000001111111111222222222233333333334444444444555555555566666666667777777777",
                dapnet_login_callsign=dapnet_login_callsign,
                dapnet_login_passcode=dapnet_login_passcode,
                dapnet_high_priority_message=False,
            )
        )
