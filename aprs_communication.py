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
from utility_modules import write_number_of_served_packages

# Configuration settings
mpad_version = "0.01"
mpad_latitude = "51.8388N"  # 8 chars fixed length, ddmm.mmN, see chapter 6 pg. 23
mpad_longitude = "008.3266E"  # 9 chars fixed length, dddmm.mmE, see chapter 6 pg. 23
mpad_alias = "MPAD"  # Identifier for sending data to APRS-IS
mpad_aprs_tocall = "APRS"  # APRS "TOCALL", see http://aprs.org/aprs11/tocalls.txt. Needs to get its own identifier at a later point in time


# Constants, do not change
aprs_table = "/"  # my symbol table (/=primary \=secondary, or overlay)
aprs_symbol = "?"  # APRS symbol: Server
packet_delay_long = 2.0  # packet delay in seconds after sending data to aprs-is
packet_delay_short = 1.0  # packet delay in seconds after sending data to aprs-is

global number_of_served_packages

# bulletin messages (will be sent every 4 hrs)
bulletin_texts = {
    "BLN0": f"{mpad_alias} {mpad_version} APRS WX Bot (Prototype)",
    "BLN1": f"I have just hatched and am still in alpha test mode. More useful",
    "BLN2": f"information is going to be added here very soon. Thank you.",
}

# beacon texts (will be sent every 30 mins)
beacon_text_array = [
    f"={mpad_latitude}/{mpad_longitude}{aprs_symbol}{mpad_alias} {mpad_version}",
    ">My tiny little APRS bot (pre-alpha testing)",
]


def parse_aprs_data(packet_data_dict, item):
    try:
        return packet_data_dict.get(item)
    except Exception:
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
    global number_of_served_packages
    logging.debug("Beacon-Intervall erreicht; sende Beacons")
    for bcn in beacon_text_array:
        stringtosend = f"{mpad_alias}>{mpad_aprs_tocall}:{bcn}"
        if not simulate_send:
            logging.debug(f"echtes Senden: {stringtosend}")
        else:
            logging.debug(f"Sende: {stringtosend}")
    write_number_of_served_packages(number_of_served_packages)


def send_bulletin_messages(myaprsis: aprslib.inet.IS, simulate_send: bool = True):
    """
    Send bulletin message list to APRS_IS
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
    logging.debug("Bulletin-Intervall erreicht; sende Bulletins")
    for recipient_id, bln in bulletin_texts.items():
        stringtosend = f"{mpad_alias}>{mpad_aprs_tocall}::{recipient_id:9}:{bln}"
        if not simulate_send:
            logging.debug(f"echtes Senden: {stringtosend}")
        else:
            logging.debug(f"Sende: {stringtosend}")


def send_ack(
    myaprsis: aprslib.inet.IS,
    src_call_sign: str,
    msg_no: str,
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
    src_call_sign: 'str'
        Call sign of the user that has sent us the message
    msg_no: 'str'
        message number from user's request. Can be 'None'. In that case, we don't send a message acknowledgment to the user
    simulate_send: 'bool'
        If True: Prepare string but only send it to logger

    Returns
    =======
    none
    """

    if msg_no:
        logging.debug("Preparing acknowledgment")
        stringtosend = f"{mpad_alias}>{mpad_aprs_tocall}::{src_call_sign:9}:ack{msg_no}"
        if not simulate_send:
            logging.debug(f"echtes Senden: {stringtosend}")
        else:
            logging.debug(f"Sende: {stringtosend}")


def send_aprs_message_list(
    myaprsis: aprslib.inet.IS,
    message_text_array: list,
    src_call_sign: str,
    send_with_msg_no: bool,
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
    simulate_send: 'bool'
        If True: Prepare string but only send it to logger

    Returns
    =======
    none
    """
    global number_of_served_packages
    for single_message in message_text_array:
        stringtosend = (
            f"{mpad_alias}>{mpad_aprs_tocall}::{src_call_sign:9}:{single_message}"
        )
        if send_with_msg_no:
            stringtosend = stringtosend + "}" + f"{number_of_served_packages:05}"
            number_of_served_packages = number_of_served_packages + 1
            if number_of_served_packages > 99999:  # max. 5stellig
                number_of_served_packages = 1
        if not simulate_send:
            logging.debug("Echtes Senden")
        else:
            logging.debug(stringtosend)
        time.sleep(packet_delay_short)


def send_single_aprs_message(
    myaprsis: aprslib.inet.IS,
    message_text: str,
    src_call_sign: str,
    send_with_msg_no: bool,
    simulate_send,
):
    """
    Send a single line of text to APRS_IS
    Split message up into 1..n chunks of 67 character string if content is too long
    If 'simulate_send'= True, we still prepare the message but only send it to our log file

    Parameters
    ==========
    myaprsis: 'aprslib.inet.IS'
        Our aprslib object that we will use for the communication part
    message_text: 'str'
        Contains 1..n entries of the content that we want to send to the user
    src_call_sign: 'str'
        Call sign of the user that has sent us the message
    send_with_msg_no: 'bool'
        If True, each outgoing message will have its own message ID attached to the outgoing content
        If False, no message ID is added
    simulate_send: 'bool'
        If True: Prepare string but only send it to logger

    Returns
    =======
    none
    """
    global number_of_served_packages
    maxlen = 67  # max. size of APRS message
    chunks = [message_text[i : i + maxlen] for i in range(0, len(message_text), maxlen)]
    for chunk in chunks:
        stringtosend = f"{mpad_alias}>{mpad_aprs_tocall}::{src_call_sign:9}:{chunk}"
        if send_with_msg_no:
            stringtosend = stringtosend + "}" + f"{number_of_served_packages:05}"
            number_of_served_packages = number_of_served_packages + 1
            if number_of_served_packages > 99999:  # max. 5stellig
                number_of_served_packages = 1
        if not simulate_send:
            logging.debug("Echtes Senden")
        else:
            logging.debug(stringtosend)
        time.sleep(packet_delay_short)


def extract_msgno_from_defective_message(message_text: str):
    msg = msgno = None

    matches = re.search(r"(.*)\{([a-zA-Z0-9]{1,5})\}", message_text, re.IGNORECASE)
    if matches:
        try:
            msg = matches[1]
            msgno = matches[2]
        except:
            msg = message_text
            msgno = None
    return msg, msgno


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
    )
