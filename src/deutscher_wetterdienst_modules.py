#
# Multi-Purpose APRS Daemon: Deutscher Wetterdienst WX Warning Bulletins
# Author: Joerg Schultze-Lutter, 2020
#
# Deutscher Wetterdienst wx bulletins for German users
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

# List of valid WarnCellIDs can be found here: https://www.dwd.de/DE/leistungen/opendata/hilfe.html

from utility_modules import read_program_config, convert_text_to_plain_ascii
import logging
from datetime import datetime
import mpad_config
import re
import requests
import json
from aprs_communication import send_bulletin_messages
import aprslib

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def send_dwd_bulletins(myaprsis: aprslib.inet.IS, simulate_send: bool = True):
    """
    Sends Deutscher Wetterdienst bulletin messages to APRS_IS (if such warnings are present)
    The function extracts the data from the DWD web site, transfers it into bulletin messages
    and then uses MPAD's default bulletin function for sending out the data

    Parameters
    ==========
    myaprsis: 'aprslib.inet.IS'
        Our aprslib object that we will use for the communication part. We only use
        this here for passing through the parameter value to the bulletin function
    simulate_send: 'bool'
        If True: Prepare string but only send it to logger. We only use
        this here for passing through the parameter value to the bulletin function

    Returns
    =======
    none
    """
    success = False
    dwd_bulletin_dictionary = {}
    _bulletin_prefix = "BLN"
    _wx_prefix = "WX"

    headers = {"User-Agent": mpad_config.mpad_default_user_agent}

    try:
        resp = requests.get(
            url=f"https://www.dwd.de/DWD/warnungen/warnapp/json/warnings.json",
            headers=headers,
        )
    except:
        resp = None
    if resp:
        if resp.status_code == 200:
            website_content_text = resp.text
            # website provides JSONP content; let's get rid of the leading and trailing data
            # see https://www.dwd.de/DE/wetter/warnungen_aktuell/objekt_einbindung/objekteinbindung.html
            if not website_content_text.startswith("{"):
                regex_string = "^(warnWetter.loadWarnings\()"
                website_content_text = re.sub(
                    pattern=regex_string, repl="", string=website_content_text
                )
                regex_string = "(\);)$"
                website_content_text = re.sub(
                    pattern=regex_string, repl="", string=website_content_text
                )
            try:
                website_content = json.loads(website_content_text)
            except:
                website_content = {}
            if "warnings" in website_content:
                w = website_content["warnings"]
                for warncell in mpad_config.mpad_dwd_warncells:
                    if warncell in website_content["warnings"]:
                        success = True
                        warncell_data_list = website_content["warnings"][warncell]

                        warncell_abbrev = mpad_config.mpad_dwd_warncells[warncell]
                        if len(warncell_abbrev) > 3:
                            warncell_abbrev = warncell_abbrev[:3]
                        for single_warncell in warncell_data_list:
                            dwd_event = bln_message = None
                            dwd_end = datetime.min
                            if "event" in single_warncell:
                                dwd_event = single_warncell["event"]
                            if "end" in single_warncell:
                                try:
                                    dwd_end = datetime.fromtimestamp(
                                        single_warncell["end"] / 1000
                                    )
                                except:
                                    dwd_end = datetime.min
                            if dwd_end != datetime.min and dwd_event:
                                # This time stamp uses LOCAL time settings and NOT UTC time settings
                                # hour format string will not work on Windows, see
                                # https://stackoverflow.com/questions/904928/python-strftime-date-without-leading-0
                                #
                                # As this is a bulletin message, we always convert its content from UTF-8 to ASCII
                                dwd_event = convert_text_to_plain_ascii(
                                    message_string=dwd_event
                                )
                                dwd_event = dwd_event.upper()
                                bln_message = f"DWD Warnung vor {dwd_event} in {warncell_abbrev} bis {dwd_end.strftime('%d-%b %-Hh')}"
                                if len(bln_message) > 67:
                                    bln_message = bln_message[:67]
                                for i in range(0, 10):
                                    wxkey = f"{_bulletin_prefix}{i:1d}{_wx_prefix}{warncell_abbrev:3}"
                                    if wxkey not in dwd_bulletin_dictionary:
                                        dwd_bulletin_dictionary[wxkey] = bln_message
                                        break
    if len(dwd_bulletin_dictionary) > 0:
        # logger.info(dwd_bulletin_dictionary)
        send_bulletin_messages(
            myaprsis=myaprsis,
            bulletin_dict=dwd_bulletin_dictionary,
            simulate_send=simulate_send,
        )


if __name__ == "__main__":
    (
        success,
        aprsdotfi_api_key,
        openweathermapdotorg_api_key,
        aprsis_callsign,
        aprsis_passcode,
        dapnet_callsign,
        dapnet_passcode,
        smtpimap_email_address,
        smtpimap_email_password,
    ) = read_program_config()
    if success:
        send_dwd_bulletins(myaprsis=None, simulate_send=True)
