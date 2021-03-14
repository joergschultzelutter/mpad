#
# Multi-Purpose APRS Daemon: various APRS routines
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: APRS communication core functions
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

import aprslib
import logging
import time
import re

import mpad_config

# APRS_IS bulletin messages (will be sent every 4 hrs)
# Note: these HAVE to have 67 characters (or less) per entry
# MPAD will NOT check the content and send it out 'as is'
bulletin_texts: dict = {
    "BLN0": f"{mpad_config.mpad_alias} {mpad_config.mpad_version} Multi-Purpose APRS Daemon",
    #    "BLN1": f"I have just hatched and am still in alpha test mode. More useful",
    #    "BLN2": f"information is going to be added here very soon. Thank you.",
}

# APRS_IS beacon texts (will be sent every 30 mins)
# - APRS Position (first line) needs to have 63 characters or less
# - APRS Status can have 67 chars (as usual)
# Details: see aprs101.pdf chapter 8

# MPAD will NOT check the content and send it out 'as is'
#
# This message is a position report; format description can be found on pg. 23ff and pg. 94ff.
# of aprs101.pdf. Message symbols: see http://www.aprs.org/symbols/symbolsX.txt and aprs101.pdf
# on page 104ff.
# Format is as follows: =Lat primary-symbol-table-identifier lon symbol-identifier test-message
# Lat/lon from the configuration have to be valid or the message will not be accepted by aprs-is
#
# Example nessage: MPAD>APRS:=5150.34N/00819.60E?MPAD 0.01
# results in
# lat = 5150.34N
# primary symbol identifier = /
# lon = 00819.60E
# symbol identifier = ?
# plus some text.
# The overall total symbol code /? refers to a server icon - see list of symbols
#
beacon_text_array: list = [
    f"={mpad_config.mpad_latitude}{mpad_config.aprs_table}{mpad_config.mpad_longitude}{mpad_config.aprs_symbol}{mpad_config.mpad_alias} {mpad_config.mpad_version} /A={mpad_config.mpad_beacon_altitude_ft:06}",
    #    ">My tiny little APRS bot (pre-alpha testing)",
]

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def parse_aprs_data(packet_data_dict: dict, item: str):
    """
    Get a value for a key from a dictionary. If key is not present,
    return 'None' for value

    Parameters
    ==========
    packet_data_dict: 'dict'
        Contains pre-parsed



    Returns
    =======
    call_sign: 'str'
        Same as input parameter; converted to uppercase
    passcode: 'str'
        passcode for the call_sign data; -1 if call sign = 'N0CALL'
    simulate_send_process: 'bool'
        We will only simulate the send process if this field is True
    """
    if item in packet_data_dict:
        return packet_data_dict[item]
    else:
        return None


def send_beacon_and_status_msg(myaprsis: aprslib.inet.IS, simulate_send: bool = True):
    """
    Send beacon message list to APRS_IS
    If 'simulate_send'= True, we still prepare the message but only send it to our log file

    Parameters
    ==========
    myaprsis: 'aprslib.inet.IS'
        Our aprslib object that we will use for the communication part
    simulate_send: 'bool'
        If True: Prepare string but only send it to logger

    Returns
    =======
    none
    """
    logger.info("Reached beacon interval; sending beacons")
    for bcn in beacon_text_array:
        stringtosend = f"{mpad_config.mpad_alias}>{mpad_config.mpad_aprs_tocall}:{bcn}"
        if not simulate_send:
            logger.info(f"Sending beacon: {stringtosend}")
            myaprsis.sendall(stringtosend)
            time.sleep(mpad_config.packet_delay_other)
        else:
            logger.info(f"Simulating beacons: {stringtosend}")


def send_bulletin_messages(myaprsis: aprslib.inet.IS, simulate_send: bool = True):
    """
    Sends bulletin message list to APRS_IS
    'Recipient' is 'BLN0' ...'BLNn' and is predefined in the bulletin's dict element
    If 'simulate_send'= True, we still prepare the message but only send it to our log file

    Parameters
    ==========
    myaprsis: 'aprslib.inet.IS'
        Our aprslib object that we will use for the communication part
    simulate_send: 'bool'
        If True: Prepare string but only send it to logger

    Returns
    =======
    none
    """
    logger.info("reached bulletin interval; sending bulletins")
    for recipient_id, bln in bulletin_texts.items():
        stringtosend = f"{mpad_config.mpad_alias}>{mpad_config.mpad_aprs_tocall}::{recipient_id:9}:{bln}"
        if not simulate_send:
            logger.info(f"Sending bulletin: {stringtosend}")
            myaprsis.sendall(stringtosend)
            time.sleep(mpad_config.packet_delay_other)
        else:
            logger.info(f"simulating bulletins: {stringtosend}")


def send_ack(
    myaprsis: aprslib.inet.IS,
    users_callsign: str,
    source_msg_no: str,
    simulate_send: bool = True,
):
    """
    Send acknowledgment for received package to APRS_IS if
    a message number was present
    If 'simulate_send'= True, we still prepare the message but only send it to our  log file

    Parameters
    ==========
    myaprsis: 'aprslib.inet.IS'
        Our aprslib object that we will use for the communication part
    users_callsign: 'str'
        Call sign of the user that has sent us the message
    source_msg_no: 'str'
        message number from user's request. Can be 'None'. In that case, we don't send a message acknowledgment to the user
        (normally, we should not enter this function at all if this value is 'None'. The safeguard will still stay in place)
    simulate_send: 'bool'
        If True: Prepare string but only send it to logger

    Returns
    =======
    none
    """

    if source_msg_no:
        logger.info("Preparing acknowledgment receipt")
        stringtosend = f"{mpad_config.mpad_alias}>{mpad_config.mpad_aprs_tocall}::{users_callsign:9}:ack{source_msg_no}"
        if not simulate_send:
            logger.info(f"Sending acknowledgment receipt: {stringtosend}")
            myaprsis.sendall(stringtosend)
            time.sleep(mpad_config.packet_delay_other)
        else:
            logger.info(f"Simulating acknowledgment receipt: {stringtosend}")


def send_aprs_message_list(
    myaprsis: aprslib.inet.IS,
    message_text_array: list,
    src_call_sign: str,
    send_with_msg_no: bool,
    number_of_served_packages: int,
    simulate_send: bool = True,
):
    """
    Send a pre-prepared message list to to APRS_IS
    All packages have a max len of 67 characters
    If 'simulate_send'= True, we still prepare the message but only send it to our log file

    Parameters
    ==========
    myaprsis: 'aprslib.inet.IS'
        Our aprslib object that we will use for the communication part
    message_text_array: 'list'
        Contains 1..n entries of the content that we want to send to the user
    src_call_sign: 'str'
        Target user call sign that is going to receive the message (usually, this
        is the user's call sign who has sent us the initial message)
    send_with_msg_no: 'bool'
        If True, each outgoing message will have its own message ID attached to the outgoing content
        If False, no message ID is added
    number_of_served_packages: int
        number of packages sent to aprs_is
    simulate_send: 'bool'
        If True: Prepare string but only send it to logger

    Returns
    =======
    number_of_served_packages: 'int'
        number of packages sent to aprs_is
    """
    for single_message in message_text_array:
        stringtosend = f"{mpad_config.mpad_alias}>{mpad_config.mpad_aprs_tocall}::{src_call_sign:9}:{single_message}"
        if send_with_msg_no:
            stringtosend = stringtosend + "{" + f"{number_of_served_packages:05}"
            number_of_served_packages = number_of_served_packages + 1
            if number_of_served_packages > 99999:  # max 5 digits
                number_of_served_packages = 1
        if not simulate_send:
            logger.info(f"Sending response message '{stringtosend}'")
            myaprsis.sendall(stringtosend)
        else:
            logger.info(f"Simulating response message '{stringtosend}'")
        time.sleep(mpad_config.packet_delay_message)
    return number_of_served_packages


def extract_msgno_from_defective_message(message_text: str):
    """
    Have a look at the incoming APRS message and check if it
    contains a message no which does not follow the APRS
    standard (see aprs101.pdf chapter 14)

    http://www.aprs.org/aprs11/replyacks.txt


    Explanation:

    Per specification, any APRS message that HAS a message ID
    contains this data in as trailing information in the following format:

    message_text_1_to_67_chars{message_no_1_to_5_chars
    e.g.
    Hello World{12345

    MPAD has encountered a few messages where the message does seem
    to contain message IDs that are transmitted in an invalid format:

    Hello World{12345}ab

    aprslib does not recognise this format because it deviates from the
    APRS standard. This tweak recognises such messages, extracts the message
    number and ignores the trailing content.

    Parameters
    ==========
    message_text: 'str'
        The original aprs message as originally extracted by aprslib

    Returns
    =======
    msg: 'str'
        original message OR the modified message minus message no and trailing
        data
    msg_no: 'str'
        Null if no message_no was present
    """

    msg = msgno = None

    if message_text:
        matches = re.search(r"(.*){([a-zA-Z0-9]{1,5})}", message_text, re.IGNORECASE)
        if matches:
            try:
                msg = matches[1].rstrip()
                msgno = matches[2]
            except:
                msg = message_text
                msgno = None
        else:
            msg = message_text
    else:
        msg = message_text
    return msg, msgno


if __name__ == "__main__":
    logger.info(extract_msgno_from_defective_message("Deensen;de tomorrow {ab}cd"))
