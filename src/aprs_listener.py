#
# Multi-Purpose APRS Daemon
# Author: Joerg Schultze-Lutter, 2020
#
# Core process
#

from input_parser import parsemessage
from apscheduler.schedulers.background import BackgroundScheduler
from output_generator import generate_output_message
from utility_modules import (
    read_program_config,
    read_number_of_served_packages,
    write_number_of_served_packages,
)
from aprs_communication import (
    get_aprsis_passcode,
    parse_aprs_data,
    send_bulletin_messages,
    send_beacon_and_status_msg,
    send_single_aprs_message,
    send_ack,
    extract_msgno_from_defective_message,
    send_aprs_message_list,
)
import apscheduler.schedulers.base
import sys
import logging
import aprslib
import datetime
import time
import mpad_config

########################################


# APRSlib callback
# Extract the fields from the APRS message, start the parsing process,
# execute the command and send the command output back to the user
def mycallback(packet):

    global number_of_served_packages

    # Extract base data from the APRS message
    # our APRS-IS filter kinda guarantees that we have received an APRS message
    # Nevertheless, we hope for the best and expect the worst
    # If one of these fields cannot be extracted (or is not present, e.g. msgno)
    # then its value is 'None' by default
    #
    # Let's start:
    #
    # addresse_string contains the APRS id that the user has sent the data to
    # Usually, this is 'MPAD' but can also be a 2nd/33ed address
    # (dependent on what your program config file looks like)
    addresse_string = parse_aprs_data(packet, "addresse")
    #
    # The is the actual message that we are going to parse
    message_text_string = parse_aprs_data(packet, "message_text")
    #
    # messagenumber, if present in the original msg (note: this is optional)
    msgno_string = parse_aprs_data(packet, "msgNo")
    #
    # User's call sign. read: who has sent us this message?
    from_callsign = parse_aprs_data(packet, "from")
    from_callsign = from_callsign.upper()
    format_string = parse_aprs_data(packet, "format")

    #
    # This calls a convenience handler / parser. In some rare cases, APRS
    # messages do not seem to follow the APRS messaging standard as described
    # in chapter 14 of the aprs101.pdf guide (pg. 71). Rather than sending the
    # msg no in the standard format (12345=msg_no)
    # message_text{12345
    # these senders add a closing bracket to the end of the message. Example:
    # message_text{12345}
    # aprslib does not recognise this flawed package and returns the content as
    # is. Our convenience handler takes care of the issue and returns a 'clean'
    # message text and a separated message_no whereas present
    if not msgno_string:
        message_text_string, msgno_string = extract_msgno_from_defective_message(
            message_text_string
        )

    # Based on whether we have received a message number, we now set a session
    # parameter which tells MPAD for _this_ message whether an ACK is required
    # and whether we are supposed to send outgoing messages with or without
    # that message number.
    # True = Send ack for initial message, enrich every outgoing msg with msgno
    msg_no_supported = True if msgno_string else False

    #
    # Now let's have a look at the message that we have received
    if addresse_string in mpad_config.mycallsigns_to_parse:
        # Format = message und message_text gefüllt? (sollte dann keine Response sein)
        if format_string == "message" and message_text_string:
            # Diese Nachricht ist für uns. Es kann losgehen
            logging.debug(f"received packet: {packet}")
            # ack senden, falls msgNo vorhanden (siehe S. 71ff.)
            send_ack(AIS, aprsis_simulate_send, from_callsign, msgno_string)
            # Content parsen
            success, response_parameters = parsemessage(
                message_text_string, from_callsign, aprsdotfi_api_key
            )
            if success:
                success, output_message = generate_output_message(
                    response_parameters=response_parameters,
                    openweathermapdotorg_api_key=openweathermapdotorg_api_key,
                )
                if success:
                    number_of_served_packages = send_aprs_message_list(
                        AIS,
                        aprsis_simulate_send,
                        output_message,
                        from_callsign,
                        msg_no_supported,
                        number_of_served_packages,
                    )
                else:
                    # nichts gefunden; Fehlermeldung an User senden
                    send_single_aprs_message(
                        AIS,
                        aprsis_simulate_send,
                        "Fatal error",
                        from_callsign,
                        msg_no_supported,
                    )
                    logging.debug(f"Unable to grok packet {packet}")
            else:
                # nichts gefunden; Fehlermeldung anm User senden
                requested_address = response_parameters["human_readable_address"]
                send_single_aprs_message(
                    AIS,
                    aprsis_simulate_send,
                    requested_address,
                    from_callsign,
                    msg_no_supported,
                )
                logging.debug(f"Unable to grok packet {packet}")


#
# main
#

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(module)s -%(levelname)s - %(message)s"
)
aprsis_callsign, aprsis_passcode, aprsis_simulate_send = get_aprsis_passcode(
    mpad_config.myaprsis_login_callsign
)
number_of_served_packages = read_number_of_served_packages()
# read_icao_and_iata_data()
success, aprsdotfi_api_key, openweathermapdotorg_api_key = read_program_config()
if not success:
    logging.error("Cannot find config file; aborting")
    sys.exit(0)

try:
    while True:
        reconnect_timestamp = (
            status_timestamp
        ) = beacon_timestamp = datetime.datetime.now()
        # Callsign und Passcode setzen
        AIS = aprslib.IS(aprsis_callsign, aprsis_passcode)

        # Filterport und zugehörigen Filter setzen
        AIS.set_server(mpad_config.myaprs_server_name, mpad_config.myaprs_server_port)
        AIS.set_filter(mpad_config.myaprs_server_filter)

        logging.debug(
            f"Verbindung herstellen: Server={mpad_config.myaprs_server_name}, port={mpad_config.myaprs_server_port}, filter={mpad_config.myaprs_server_filter}, APRS-IS User: {aprsis_callsign}, APRS-IS Passcode: {aprsis_passcode}"
        )
        AIS.connect(blocking=True)
        if AIS._connected == True:
            logging.debug("Verbindung aufgebaut")

            # Initiales Beacon versenden
            logging.debug("Initiales Beacon nach Verbindungsaufbau senden")
            send_beacon_and_status_msg(AIS, aprsis_simulate_send)

            # Scheduler einrichten und starten
            aprs_scheduler = BackgroundScheduler()
            aprs_scheduler.add_job(
                send_beacon_and_status_msg,
                "interval",
                id="bulletin",
                minutes=30,
                args=[AIS, aprsis_simulate_send],
            )
            aprs_scheduler.add_job(
                send_bulletin_messages,
                "interval",
                id="status",
                minutes=4 * 60,
                args=[AIS, aprsis_simulate_send],
            )
            aprs_scheduler.start()

            logging.debug("Starte Callback-Consumer")
            AIS.consumer(mycallback, blocking=True, immortal=True, raw=False)

            logging.debug("Callback verlassen")
            # Scheduler zuerst stoppen, leeren und dann herunterfahren
            aprs_scheduler.pause()
            aprs_scheduler.remove_all_jobs()
            if aprs_scheduler.state != apscheduler.schedulers.base.STATE_STOPPED:
                try:
                    aprs_scheduler.shutdown()
                except:
                    logging.debug("Fehler beim Scheduler Shutdown")

            # Verbindung schließen
            logging.debug("Schliesse Verbindung")
            AIS.close()
        else:
            logging.debug("Konnte Verbindung nicht neu aufbauen")
        write_number_of_served_packages(served_packages=number_of_served_packages)
        logging.debug("Schlafe 5 sec")
        time.sleep(5)
#        AIS.close()
except (KeyboardInterrupt, SystemExit):
    logging.debug("received exception!")
    if aprs_scheduler:
        if aprs_scheduler.state != apscheduler.schedulers.base.STATE_STOPPED:
            try:
                aprs_scheduler.shutdown()
            except:
                logging.debug("Fehler beim Shutdown APRS-Scheduler")
        if AIS:
            AIS.close()
    write_number_of_served_packages(served_packages=number_of_served_packages)
