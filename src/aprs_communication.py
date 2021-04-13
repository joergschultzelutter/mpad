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
    logger.info(msg="Reached beacon interval; sending beacons")
    for bcn in mpad_config.aprs_beacon_messages:
        stringtosend = f"{mpad_config.mpad_alias}>{mpad_config.mpad_aprs_tocall}:{bcn}"
        if not simulate_send:
            logger.info(msg=f"Sending beacon: {stringtosend}")
            myaprsis.sendall(stringtosend)
            time.sleep(mpad_config.packet_delay_other)
        else:
            logger.info(msg=f"Simulating beacons: {stringtosend}")


def send_bulletin_messages(
    myaprsis: aprslib.inet.IS, bulletin_dict: dict, simulate_send: bool = True
):
    """
    Sends bulletin message list to APRS_IS
    'Recipient' is 'BLNxxx' and is predefined in the bulletin's dict 'key'. The actual message
    itself is stored in the dict's 'value'.
    If 'simulate_send'= True, we still prepare the message but only send it to our log file

    Parameters
    ==========
    myaprsis: 'aprslib.inet.IS'
        Our aprslib object that we will use for the communication part
    bulletin_dict: 'dict'
        The bulletins that we are going to send upt to the user. Key = BLNxxx, Value = Bulletin Text
    simulate_send: 'bool'
        If True: Prepare string but only send it to logger

    Returns
    =======
    none
    """
    logger.info(msg="reached bulletin interval; sending bulletins")
    for recipient_id, bln in bulletin_dict.items():
        stringtosend = f"{mpad_config.mpad_alias}>{mpad_config.mpad_aprs_tocall}::{recipient_id:9}:{bln}"
        if not simulate_send:
            logger.info(msg=f"Sending bulletin: {stringtosend}")
            myaprsis.sendall(stringtosend)
            time.sleep(mpad_config.packet_delay_other)
        else:
            logger.info(msg=f"simulating bulletins: {stringtosend}")


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
        logger.info(msg="Preparing acknowledgment receipt")
        stringtosend = f"{mpad_config.mpad_alias}>{mpad_config.mpad_aprs_tocall}::{users_callsign:9}:ack{source_msg_no}"
        if not simulate_send:
            logger.info(msg=f"Sending acknowledgment receipt: {stringtosend}")
            myaprsis.sendall(stringtosend)
            time.sleep(mpad_config.packet_delay_other)
        else:
            logger.info(msg=f"Simulating acknowledgment receipt: {stringtosend}")


def send_aprs_message_list(
    myaprsis: aprslib.inet.IS,
    message_text_array: list,
    destination_call_sign: str,
    send_with_msg_no: bool,
    aprs_message_counter: int,
    external_message_number: str,
    simulate_send: bool = True,
    new_ackrej_format: bool = False,
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
    destination_call_sign: 'str'
        Target user call sign that is going to receive the message (usually, this
        is the user's call sign who has sent us the initial message)
    send_with_msg_no: 'bool'
        If True, each outgoing message will have its own message ID attached to the outgoing content
        If False, no message ID is added
    aprs_message_counter: int
        message_counter for messages that require to be ack'ed
    simulate_send: 'bool'
        If True: Prepare string but only send it to logger
    external_message_number: 'str'
        only used if we deal with the new ackrej format
    new_ackrej_format: 'bool'
        false: apply the old ack/rej logic as described in aprs101.pdf.
               MPAD generates its own message id. The user's message ID
               (from the original request) will NOT be added to the
               outgoing message
        True: apply the new ack/rej logic as described
        in http://www.aprs.org/aprs11/replyacks.txt
               MPAD generates its own message id. The user's message ID
               (from the original request) WILL be added to the
               outgoing message

    Returns
    =======
    aprs_message_counter: 'int'
        new value for message_counter for messages that require to be ack'ed
    """
    for single_message in message_text_array:
        stringtosend = f"{mpad_config.mpad_alias}>{mpad_config.mpad_aprs_tocall}::{destination_call_sign:9}:{single_message}"
        if send_with_msg_no:
            alpha_counter = get_alphanumeric_counter_value(aprs_message_counter)
            stringtosend = stringtosend + "{" + alpha_counter
            if new_ackrej_format:
                stringtosend = stringtosend + "}" + external_message_number[:2]
            aprs_message_counter = aprs_message_counter + 1
            if (
                aprs_message_counter > 676 or alpha_counter == "ZZ"
            ):  # for the alphanumeric counter AA..ZZ, this is equal to "ZZ"
                aprs_message_counter = 0
        if not simulate_send:
            logger.info(msg=f"Sending response message '{stringtosend}'")
            myaprsis.sendall(stringtosend)
        else:
            logger.info(msg=f"Simulating response message '{stringtosend}'")
        time.sleep(mpad_config.packet_delay_message)
    return aprs_message_counter


def check_for_new_ackrej_format(message_text: str):
    """
    Have a look at the incoming APRS message and check if it
    contains a message no which does not follow the APRS
    standard (see aprs101.pdf chapter 14)

    http://www.aprs.org/aprs11/replyacks.txt

    but rather follow the new format

    http://www.aprs.org/aprs11/replyacks.txt

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
    new_ackrej_format: 'bool'
        True if the ackrej_format has to follow the new ack-rej handling
        process as described in http://www.aprs.org/aprs11/replyacks.txt
    """

    """
    The following assumptions apply when handling APRS messages in general:
    
    Option 1: no message ID present:
        send no ACK
        outgoing messages have no msg number attachment

            Example data exchange 1:
            DF1JSL-4>APRS,TCPIP*,qAC,T2PRT::WXBOT    :94043
            WXBOT>APRS,qAS,KI6WJP::DF1JSL-4 :Mountain View CA. Today,Sunny High 60
            
            Example data exchange 2:
            DF1JSL-4>APRS,TCPIP*,qAC,T2SPAIN::EMAIL-2  :jsl24469@gmail.com Hallo
            EMAIL-2>APJIE4,TCPIP*,qAC,AE5PL-JF::DF1JSL-4 :Email sent to jsl24469@gmail.com

    
    Option 2: old message number format is present: (example: msg{12345)
        Send ack with message number from original message (ack12345)
        All outgoing messages have trailing msg number ( {abcde ); can be numeric or
        slphanumeric counter. See aprs101.pdf chapter 14

            Example data exchange 1:
            DF1JSL-4>APRS,TCPIP*,qAC,T2SP::EMAIL-2  :jsl24469@gmail.com Hallo{12345
            EMAIL-2>APJIE4,TCPIP*,qAC,AE5PL-JF::DF1JSL-4 :ack12345
            EMAIL-2>APJIE4,TCPIP*,qAC,AE5PL-JF::DF1JSL-4 :Email sent to jsl24469@gmail.com{891
            DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::EMAIL-2  :ack891
            
            Example data exchange 2:
            DF1JSL-4>APRS,TCPIP*,qAC,T2CSNGRAD::EMAIL-2  :jsl24469@gmail.com{ABCDE
            EMAIL-2>APJIE4,TCPIP*,qAC,AE5PL-JF::DF1JSL-4 :ackABCDE
            EMAIL-2>APJIE4,TCPIP*,qAC,AE5PL-JF::DF1JSL-4 :Email sent to jsl24469@gmail.com{893
            DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::EMAIL-2  :ack893

    
    Option 3: new messages with message ID but without trailing retry msg ids: msg{AB}
        Do NOT send extra ack
        All outgoing messages have 2-character msg id, followed by message ID from original message
        Example: 
        User sends message "Hello{AB}" to MPAD
        MPAD responds "Message content line 1{DE}AB" to user
        MPAD responds "Message content line 2{DF}AB" to user
        
        AB -> original message
        DE, DF -> message IDs generated by MPAD
        
            Example data exchange 1:
            DF1JSL-4>APRS,TCPIP*,qAC,T2NUERNBG::WXBOT    :99801{AB}
            WXBOT>APRS,qAS,KI6WJP::DF1JSL-4 :Lemon Creek AK. Today,Scattered Rain/Snow and Patchy Fog 50% High 4{QL}AB
            DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :ackQL}AB
            WXBOT>APRS,qAS,KI6WJP::DF1JSL-4 :0{QM}AB
            DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :ackQM}AB
            
            Example data exchange 2:
            DF1JSL-4>APRS,TCPIP*,qAC,T2SPAIN::EMAIL-2  :jsl24469@gmail.com Hallo{AB}
            EMAIL-2>APJIE4,TCPIP*,qAC,AE5PL-JF::DF1JSL-4 :Email sent to jsl24469@gmail.com{OQ}AB
            DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::EMAIL-2  :ackOQ}AB

    
    Option 4: new messages with message ID and with trailing retry msg ids: msg{AB}CD
        We don't handle retries - therefore, apply option #3 for processing these
        the "CD" part gets omitted and is not used 
        
            Example data exchange 1:
            DF1JSL-4>APRS,TCPIP*,qAC,T2CZECH::WXBOT    :99801{LM}AA
            WXBOT>APRS,qAS,KI6WJP::DF1JSL-4 :Lemon Creek AK. Today,Scattered Rain/Snow and Patchy Fog 50% High 4{QP}LM
            DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :ackQP}LM
            WXBOT>APRS,qAS,KI6WJP::DF1JSL-4 :0{QQ}LM
            DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::WXBOT    :ackQQ}LM

            Example data exchange 2:
            DF1JSL-4>APRS,TCPIP*,qAC,T2SP::EMAIL-2  :jsl24469@gmail.com Welt{DE}FG
            EMAIL-2>APJIE4,TCPIP*,qAC,AE5PL-JF::DF1JSL-4 :Email sent to jsl24469@gmail.com{OS}DE
            DF1JSL-4>APOSB,TCPIP*,qAS,DF1JSL::EMAIL-2  :ackOS}DE

    """

    msg = msgno = None
    new_ackrej_format = False

    # if message text is present, split up between aaaaaa{bb}cc
    # where aaaaaa = message text
    # bb = message number
    # cc = message retry (may or may not be present)
    if message_text:
        matches = re.search(
            r"^(.*){([a-zA-Z0-9]{2})}(\w*)$", message_text, re.IGNORECASE
        )
        if matches:
            try:
                msg = matches[1].rstrip()
                msgno = matches[2]
                new_ackrej_format = True
            except:
                msg = message_text
                msgno = None
                new_ackrej_format = False
        else:
            msg = message_text
    else:
        msg = message_text
    return msg, msgno, new_ackrej_format


def detect_and_map_new_ackrej_requests(message_text: str):
    """
    Workaround for aprslib as it can't process the 'new' response code format
    in a proper way.

    Parameters
    ==========
    message_text: 'str'
        APRS message text that needs to be examined. If this text contains
        the new ack/rej message as _sole_ data, then the response_text field
        will be populated with the ack/rej, the message numbers will be assigned
        and the message_text itself will be None'd. Otherwise, the original
        message text will be returned

    Returns
    =======
    message_text: 'str'
        original message text or 'None' if ack/rej in new format was detected
    response_string: 'str'
        None or "ack"/"rej"
    foreign_message_id: 'str'
        None or the request's message ID (the one that the sender has assigned)
    old_mpad_message_id: 'str'
        None or one of our older message ID's
    """

    matches = re.search(r"^(ack|rej)(..)}(..)$", message_text, re.IGNORECASE)
    response_string = foreign_message_id = old_mpad_message_id = None
    if matches:
        response_string = matches[1]
        foreign_message_id = matches[2]
        old_mpad_message_id = matches[3]
        message_text = None
    return message_text, response_string, foreign_message_id, old_mpad_message_id


def get_alphanumeric_counter_value(numeric_counter: int):
    """
    Calculate an alphanumeric

    Parameters
    ==========
    numeric_counter: 'int'
        numeric counter that is used for calculating the start value

    Returns
    =======
    alphanumeric_counter: 'str'
        alphanumeric counter that is based on the numeric counter
    """
    first_char = int(numeric_counter / 26)
    second_char = int(numeric_counter % 26)
    alphanumeric_counter = chr(first_char + 65) + chr(second_char + 65)
    return alphanumeric_counter


if __name__ == "__main__":
    logger.info(detect_and_map_new_ackrej_requests("ackAB}CD"))
    logger.info(check_for_new_ackrej_format("Deensen{AB}CD"))

    msg_list = [
        "1234567890123456789012345678901234567890123456789012345678901234567",
        "aaaaaaaaaabbbbbbbbbbccccccccccddddddddddeeeeeeeeeeffffffffffggggggg",
    ]

    logger.info(
        send_aprs_message_list(
            myaprsis=None,
            message_text_array=msg_list,
            destination_call_sign="DF1JSL-SX",
            send_with_msg_no=True,
            aprs_message_counter=0,
            external_message_number="LMAA",
            simulate_send=True,
            new_ackrej_format=False,
        )
    )
