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
    send_aprs_message_list,
)
import apscheduler.schedulers.base
import re
import sys
import logging

import aprslib
import datetime
import time


# will be prepopulated through config file
aprsdotfi_api_key = None
openweathermapdotorg_api_key = None

########################################

# Send-ID-Counter 1..99999
number_of_served_packages = 1


# Main-Callback, der alles im Bereich APRS-Kommunikation erledigt
def mycallback(packet):
    # Basis-APRS-Daten extrahieren
    addresse_string = parse_aprs_data(packet, "addresse")
    message_text_string = parse_aprs_data(packet, "message_text")
    msgNo_string = parse_aprs_data(
        packet, "msgNo"
    )  # für Acknowledgment der initialen Nachricht
    from_callsign = parse_aprs_data(packet, "from")
    from_callsign = from_callsign.upper()
    format_string = parse_aprs_data(packet, "format")

    # Wenn keine MsgNo gefunden, dann prüfen, ob die Message selbst noch eine (ungültige) Message+MessageNo beinhaltet. Falls ja: extrahieren
    # entspricht nicht den Standards, aber offensichtlich kommen solche Pakete ab und zu an
    if not msgNo_string:
        message_text_string, msgNo_string = extract_msgno_from_defective_message(
            message_text_string
        )

    # anschließend testen, ob wir jetzt final eine MessageNo erhalten haben
    msg_no_supported = True if msgNo_string else False

    # zunächst die eingehende Nachricht beantworten
    # in meiner Callzeichenliste vorhanden? --> wird durch den aprs_is-Filter durchgeführt und ist eigentlich nicht mehr notwendig
    if addresse_string in mycallsigns_to_parse:
        # Format = message und message_text gefüllt? (sollte dann keine Response sein)
        if format_string == "message" and message_text_string:
            # Diese Nachricht ist für uns. Es kann losgehen
            logging.debug(f"received packet: {packet}")
            # ack senden, falls msgNo vorhanden (siehe S. 71ff.)
            sned_ack(AIS, aprsis_simulate_send, from_callsign, msgNo_string)
            # Content parsen
            success, response_parameters = parsemessage(
                message_text_string, from_callsign, aprsdotfi_apikey
            )
            if success:
                success, output_message = generate_output_message(
                    response_parameters=response_parameters,
                    openweathermapdotorg_api_key=openweathermapdotorg_api_key,
                )
                if success:
                    number_of_served_packages=send_aprs_message_list(
                        AIS,
                        aprsis_simulate_send,
                        output_message,
                        from_string,
                        msg_no_supported,
                        number_of_served_packages,
                    )
                else:
                    # nichts gefunden; Fehlermeldung an User senden
                    send_single_aprs_message(
                        AIS,
                        aprsis_simulate_send,
                        "Fatal error",
                        from_string,
                        msg_no_supported,
                    )
                    loggging.debug(f"Unable to grok packet {packet}")
            else:
                # nichts gefunden; Fehlermeldung anm User senden
                send_single_aprs_message(
                    AIS,
                    aprsis_simulate_send,
                    requested_address,
                    from_string,
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
    myaprsis_login_callsign
)
number_of_served_packages = read_number_of_served_packages()
read_icao_and_iata_data()
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
        AIS.set_server(myaprs_server_name, myaprs_server_port)
        AIS.set_filter(myaprs_server_filter)

        logging.debug(
            f"Verbindung herstellen: Server={myaprs_server_name}, port={myaprs_server_port}, filter={myaprs_server_filter}, APRS-IS User: {aprsis_callsign}, APRS-IS Passcode: {aprsis_passcode}"
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
    if aprs_scheduler.state != apscheduler.schedulers.base.STATE_STOPPED:
        try:
            aprs_scheduler.shutdown()
        except:
            logging.debug("Fehler beim Shutdown APRS-Scheduler")
    AIS.close()
    write_number_of_served_packages(served_packages=number_of_served_packages)
