#
# Multi-Purpose APRS Daemon: various APRS routines
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: APRS communication core functions
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
    "BLN0": f"{mpad_config.mpad_alias} {mpad_config.mpad_version} Multi-Purpose APRS Bot",
    "BLN1": f"I have just hatched and am still in alpha test mode. More useful",
    "BLN2": f"information is going to be added here very soon. Thank you.",
}

# APRS_IS beacon texts (will be sent every 30 mins)
# Note: these HAVE to have 67 characters (or less) per entry
# MPAD will NOT check the content and send it out 'as is'
beacon_text_array: list = [
    f"={mpad_config.mpad_latitude}/{mpad_config.mpad_longitude}{mpad_config.aprs_symbol}{mpad_config.mpad_alias} {mpad_config.mpad_version}",
    ">My tiny little APRS bot (pre-alpha testing)",
]


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


def get_aprsis_passcode(call_sign: str = "N0CALL"):
    """
    Get the APRS passcode for the given call sign
    If call sign = 'N0CALL', we will return:

    a) a passcode of -1 (see aprslib.is)
    b) a flag which tells MPAD that it is only to simulate the send process

    Parameters
    ==========
    call_sign: 'str'
        Call sign string that we want to use for connecting to aprs-is

    Returns
    =======
    call_sign: 'str'
        Same as input parameter; converted to uppercase
    passcode: 'str'
        passcode for the call_sign data; -1 if call sign = 'N0CALL'
    simulate_send_process: 'bool'
        We will only simulate the send process if this field is True
    """

    call_sign = call_sign.upper()

    if call_sign == "N0CALL":
        passcode = "-1"  # read only, see aprslib
        simulate_send_process = True
    else:
        # We got ourselves a real callsign, let's get the passcode
        passcode = aprslib.passcode(call_sign)
        simulate_send_process = False
    return call_sign, passcode, simulate_send_process


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
    logging.debug("Reached beacon interval; sending beacons")
    for bcn in beacon_text_array:
        stringtosend = f"{mpad_config.mpad_alias}>{mpad_config.mpad_aprs_tocall}:{bcn}"
        if not simulate_send:
            logging.debug(f"echtes Senden: {stringtosend}")
        else:
            logging.debug(f"Simulating beacons: {stringtosend}")


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
    logging.debug("reached bulletin interval; sending bulletins")
    for recipient_id, bln in bulletin_texts.items():
        stringtosend = f"{mpad_config.mpad_alias}>{mpad_config.mpad_aprs_tocall}::{recipient_id:9}:{bln}"
        if not simulate_send:
            logging.debug(f"echtes Senden: {stringtosend}")
        else:
            logging.debug(f"simulating bulletins: {stringtosend}")


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
        logging.debug("Preparing acknowledgment receipt")
        stringtosend = f"{mpad_config.mpad_alias}>{mpad_config.mpad_aprs_tocall}::{users_callsign:9}:ack{source_msg_no}"
        if not simulate_send:
            logging.debug(f"echtes Senden: {stringtosend}")
        else:
            logging.debug(f"Simulating acknowledgment receipt: {stringtosend}")


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
    If 'simulate_send'= True, we still prepare the message but only send it to our  log file

    Parameters
    ==========
    myaprsis: 'aprslib.inet.IS'
        Our aprslib object that we will use for the communication part
    message_text_array: 'list'
        Contains 1..n entries of the content that we want to send to the user
    src_call_sign: 'str'
        Call sign of the user that has sent us the message
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
        stringtosend = (
            f"{mpad_config.mpad_alias}>{mpad_config.mpad_aprs_tocall}::{src_call_sign:9}:{single_message}"
        )
        if send_with_msg_no:
            stringtosend = stringtosend + "}" + f"{number_of_served_packages:05}"
            number_of_served_packages = number_of_served_packages + 1
            if number_of_served_packages > 99999:  # max 5 digits
                number_of_served_packages = 1
        if not simulate_send:
            logging.debug("Echtes Senden")
        else:
            logging.debug(f"Simulating response message '{stringtosend}'")
        time.sleep(mpad_config.packet_delay_short)
    return number_of_served_packages


def extract_msgno_from_defective_message(message_text: str):
    msg = msgno = None

    if message_text:
        matches = re.search(r"(.*){([a-zA-Z0-9]{1,5})}", message_text, re.IGNORECASE)
        if matches:
            try:
                msg = matches[1]
                msgno = matches[2]
            except:
                msg = message_text
                msgno = None
    else:
        msg = message_text
    return msg, msgno


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
    )
    send_beacon_and_status_msg(None)
    send_bulletin_messages(None)
    logging.debug(get_aprsis_passcode("N0CALL"))
