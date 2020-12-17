#
# Multi-Purpose APRS Daemon
# Author: Joerg Schultze-Lutter, 2020
#
# Core process
#
# Reimplements portions of Martin Nile's WXBOT code (KI6WJP)
#

from regex_decoder import parsemessage
from openweathermap_modules import get_daily_weather_from_openweathermapdotorg, parse_daily_weather_from_openweathermapdotorg
from apscheduler.schedulers.background import BackgroundScheduler
from airport_data_modules import read_icao_and_iata_data, get_metar_data
from utility_modules import log_to_stderr
import apscheduler.schedulers.base
import re

import aprslib
import datetime
import time

# Konfigurationseinstellungen
myversion = "0.01"
mylat = "51.8388N"                          # 8 chars fixed length, ddmm.mmN, see chapter 6 pg. 23
mylon = "008.3266E"                         # 9 chars fixed length, dddmm.mmE, see chapter 6 pg. 23
mytable = "/"                               # my symbol table (/=primary \=secondary, or overlay)
mysymbol = "?"                              # Symbol: Server
myalias = "DF1JSL-10"                       # We're going to listen to APRS traffic with this address
myaprstocall = "APRS"                       # siehe http://aprs.org/aprs11/tocalls.txt
myaprsis_login_callsign="n0call"            # APRS-IS-Login; Passcode wird automatisch errechnet

myaprs_server_name = "euro.aprs2.net"       # Login-Server
myaprs_server_port = 14580                  # Port
myaprs_server_filter = "g/WXBOT/WXYO"       # Server-Filter. alt: t/m
#myaprs_server_filter = "t/m"   # Server-Filter. alt: t/m
mycallsigns_to_parse = ['WXBOT', 'WXYO']

myaprs_filename = "wxtng_served.txt"    # Number of served packages
myicaoiata_filename = "stations.txt"    # ICAO & IATA data; https://www.aviationweather.gov/docs/metar/stations.txt

########################################
help_text_array = [
    '(default=wx for pos of sending callsign). Position commands:',
    'city,state;country OR city,state OR city;country OR zip;country OR',
    'zip with/wo country OR grid|mh+4..6 char OR lat/lon OR callsign',
    'time: mon..sun(day),today,tomorrow.Extra: mtr|metric imp|imperial'
]

# Bulletindaten (Versand alle 4h)
bulletin_texts = {
    'BLN0' : f'{myalias} {myversion} APRS WX Bot (Prototype)',
    'BLN1' : f'I have just hatched and am still in alpha test mode. More useful',
    'BLN2' : f'information is going to be added here very soon. Thank you.'
}

# Beacondaten (Versand alle 30 min)
beacon_text_array = [
    f'={mylat}/{mylon}{mysymbol}{myalias} {myversion}',
    '>My tiny little APRS bot (pre-alpha testing)'
]
# Send-ID-Counter 1..99999
number_of_served_packages = 1

# Packet Delays zum Versenden via APRS-IS
packet_delay_long = 2.0
packet_delay_short = 1.0

def parse_aprs_data(packet_data_dict, item):
    try:
        return packet_data_dict.get(item)
    except Exception:
        return None

def read_number_of_served_packages():
    sp = 1
    try:
        with open(f'{myaprs_filename}', 'r') as f:
            if f.mode == 'r':
                contents = f.read()
                f.close()
                sp = int(contents)
    except:
        sp = 1
        log_to_stderr(f"Cannot read {myaprs_filename}; creating new file")
    return sp

def write_number_of_served_packages(sp):
    try:
        with open(f'{myaprs_filename}', 'w') as f:
            f.write('%d' % sp)
            f.close()
    except:
        log_to_stderr(f"Cannot write number of served packages to {myaprs_filename}")

def get_aprsis_passcode(mycallsign):
    mycallsign = mycallsign.upper()
    if mycallsign == "N0CALL":
        mypasscode = "-1"
        simulate_send_process = True
    else:
        mypasscode = aprslib.passcode(mycallsign)
        simulate_send_process = False
    return  mycallsign, mypasscode, simulate_send_process

def SendBeaconAndStatusMsg(myaprsis,simulate_send):
    global number_of_served_packages
    log_to_stderr("Beacon-Intervall erreicht; sende Beacons")
    for bcn in beacon_text_array:
        stringtosend = f"{myalias}>{myaprstocall}:{bcn}"
        if myaprsis._connected:
            if not simulate_send:
                print(f"echtes Senden: {stringtosend}")
            else:
                log_to_stderr(f"Sende: {stringtosend}")
    write_number_of_served_packages(number_of_served_packages)

def SendBulletinMessages(myaprsis,simulate_send):
    log_to_stderr("Bulletin-Intervall erreicht; sende Bulletins")
    for recipient_id,bln in bulletin_texts.items():
        stringtosend = f"{myalias}>{myaprstocall}::{recipient_id:9}:{bln}"
        if myaprsis._connected:
            if not simulate_send:
                print(f"echtes Senden: {stringtosend}")
            else:
                log_to_stderr(f"Sende: {stringtosend}")

def SendAck(myaprsis, simulate_send, src_call_sign, msg_no):
    if msg_no:
        log_to_stderr("Sende Ack")
        stringtosend = f"{myalias}>{myaprstocall}::{src_call_sign:9}:ack{msg_no}"
        if myaprsis._connected:
            if not simulate_send:
                print(f"echtes Senden: {stringtosend}")
            else:
                log_to_stderr(f"Sende: {stringtosend}")

# Senden der bereits aufbereiteten Pakete; es ist sichergestellt, dass keines > 67 Byte ist
def SendAprsMessageList(aprsis, simulate_send, message_text_array, src_call_sign, send_with_msg_no):
    global number_of_served_packages
    for single_message in message_text_array:
        stringtosend = f"{myalias}>{myaprstocall}::{src_call_sign:9}:{single_message}"
        if send_with_msg_no:
            stringtosend = stringtosend+"}"+f"{number_of_served_packages:05}"
            number_of_served_packages = number_of_served_packages + 1
            if number_of_served_packages > 99999:  # max. 5stellig
                number_of_served_packages = 1
        if aprsis._connected:
            if not simulate_send:
                print("Echtes Senden")
            else:
                log_to_stderr(stringtosend)
        time.sleep(packet_delay_short)

def SendSingleAprsMessage (aprsis, simulate_send, message_text, src_call_sign, send_with_msg_no):
    global number_of_served_packages
    maxlen = 67  # max. size of APRS message
    chunks = [message_text[i:i + maxlen] for i in range(0, len(message_text), maxlen)]
    for chunk in chunks:
        stringtosend = f"{myalias}>{myaprstocall}::{src_call_sign:9}:{chunk}"
        if send_with_msg_no:
            stringtosend = stringtosend+"}"+f"{number_of_served_packages:05}"
            number_of_served_packages = number_of_served_packages + 1
            if number_of_served_packages > 99999:  # max. 5stellig
                number_of_served_packages = 1
        if aprsis._connected:
            if not simulate_send:
                print("Echtes Senden")
            else:
                log_to_stderr(stringtosend)
        time.sleep(packet_delay_short)

def extract_msgno_from_defective_message(message_text):
    msg = msgno = None

    matches = re.search(r"(.*)\{([a-zA-Z0-9]{1,5})\}", message_text, re.IGNORECASE)
    if matches:
        try:
            msg = matches[1]
            msgno = matches[2]
        except:
            msg = message_text
            msgno = None
    return msg,msgno

# Main-Callback, der alles im Bereich APRS-Kommunikation erledigt
def mycallback(packet):
    # Beinhaltet die späteren aufbereiteten Wetternachrichten
    weather_forecast_array = []

    # Basis-APRS-Daten extrahieren
    addresse_string = parse_aprs_data(packet, 'addresse')
    message_text_string = parse_aprs_data(packet, "message_text")
    msgNo_string = parse_aprs_data(packet, 'msgNo')  # für Acknowledgment der initialen Nachricht
    from_string = parse_aprs_data(packet, 'from')
    format_string = parse_aprs_data(packet, 'format')

    # Wenn keine MsgNo gefunden, dann prüfen, ob die Message selbst noch eine (ungültige) Message+MessageNo beinhaltet. Falls ja: extrahieren
    # entspricht nicht den Standards, aber offensichtlich kommen solche Pakete ab und zu an
    if not msgNo_string:
        message_text_string, msgNo_string = extract_msgno_from_defective_message(message_text_string)

    # anschließend testen, ob wir jetzt final eine MessageNo erhalten haben
    msg_no_supported = True if msgNo_string else False

    # zunächst die eingehende Nachricht beantworten
    # in meiner Callzeichenliste vorhanden? --> wird durch den aprs_is-Filter durchgeführt und ist eigentlich nicht mehr notwendig
    if addresse_string in mycallsigns_to_parse:
        # Format = message und message_text gefüllt? (sollte dann keine Response sein)
        if format_string == "message" and message_text_string:
            # Diese Nachricht ist für uns. Es kann losgehen
            log_to_stderr(f"received packet: {packet}")
            # ack senden, falls msgNo vorhanden (siehe S. 71ff.)
            SendAck(AIS,aprsis_simulate_send,from_string, msgNo_string)
            # Content parsen
            lat, lon, when, when_dt, what, units, callsign, language, metar, requested_address, date_offset, satellite, err = parsemessage(
                message_text_string, from_string.upper())
            if (not err):
                log_to_stderr("Angefragt;When;WhenDaytime;What;DateOffset;Lat;Lon;Units;Language;Callsign;Satellite")
                log_to_stderr(f"{requested_address};{when};{when_dt};{what};{date_offset};{lat};{lon}{units};{language};{callsign};{satellite}")
                if what == "wx":
                    success, myweather, tz_offset, tz = get_daily_weather_from_openweathermapdotorg(latitude=lat, longitude=lon, units=units, days_offset=date_offset)
                    if success:
                        weather_forecast_array = parse_daily_weather_from_openweathermapdotorg(myweather, units, requested_address, when, when_dt)
                        SendAprsMessageList(AIS,aprsis_simulate_send,weather_forecast_array,from_string,msg_no_supported)
                elif what == "help":
                        SendAprsMessageList(AIS,aprsis_simulate_send,help_text_array,from_string,msg_no_supported)
                elif what == "metar":
                        metar_response, found = get_metar_data(metar)
                        if found:
                            SendSingleAprsMessage(AIS,aprsis_simulate_send,metar_response,from_string,msg_no_supported)
                        else:
                            print ("metar nicht gefunden; noch Suche anhand Geokoordinaten implementieren")
                elif what == 'satpass':
                    print("Satpass")
                elif what == 'riseset':
                    print('Riseset')
                elif what == "whereis":
                    print("Eigene Position ermitteln")
                elif what == "repeater":
                    print("Repeater ermitteln")
                else:
                    # nichts gefunden; Fehlermeldung an User senden
                    SendSingleAprsMessage(AIS, aprsis_simulate_send, requested_address, from_string, msg_no_supported)
                    log_to_stderr(f"Unable to grok packet {packet}")
            else:
                # nichts gefunden; Fehlermeldung anm User senden
                SendSingleAprsMessage(AIS,aprsis_simulate_send, requested_address,from_string,msg_no_supported)
                log_to_stderr(f"Unable to grok packet {packet}")

aprsis_callsign, aprsis_passcode,aprsis_simulate_send = get_aprsis_passcode(myaprsis_login_callsign)
number_of_served_packages = read_number_of_served_packages()
read_icao_and_iata_data()

try:
    while True:
        reconnect_timestamp = status_timestamp = beacon_timestamp = datetime.datetime.now()
        # Callsign und Passcode setzen
        AIS = aprslib.IS(aprsis_callsign,aprsis_passcode)

        # Filterport und zugehörigen Filter setzen
        AIS.set_server(myaprs_server_name, myaprs_server_port)
        AIS.set_filter(myaprs_server_filter)

        log_to_stderr(f"Verbindung herstellen: Server={myaprs_server_name}, port={myaprs_server_port}, filter={myaprs_server_filter}, APRS-IS User: {aprsis_callsign}, APRS-IS Passcode: {aprsis_passcode}")
        AIS.connect(blocking=True)
        if AIS._connected == True:
            log_to_stderr("Verbindung aufgebaut")

            # Initiales Beacon versenden
            log_to_stderr("Initiales Beacon nach Verbindungsaufbau senden")
            SendBeaconAndStatusMsg(AIS,aprsis_simulate_send)

           #Scheduler einrichten und starten
            aprs_scheduler = BackgroundScheduler()
            aprs_scheduler.add_job(SendBeaconAndStatusMsg, 'interval', id='bulletin', minutes=30,args=[AIS,aprsis_simulate_send])
            aprs_scheduler.add_job(SendBulletinMessages, 'interval', id='status', minutes=4*60, args=[AIS, aprsis_simulate_send])
            aprs_scheduler.start()

            log_to_stderr("Starte Callback-Consumer")
            AIS.consumer(mycallback, blocking=True, immortal=True,raw=False)

            log_to_stderr("Callback verlassen")
            # Scheduler zuerst stoppen, leeren und dann herunterfahren
            aprs_scheduler.pause()
            aprs_scheduler.remove_all_jobs()
            if aprs_scheduler.state != apscheduler.schedulers.base.STATE_STOPPED:
                try:
                    aprs_scheduler.shutdown()
                except:
                    log_to_stderr("Fehler beim Scheduler Shutdown")

            # Verbindung schließen
            log_to_stderr("Schliesse Verbindung")
            AIS.close()
        else:
            log_to_stderr("Konnte Verbindung nicht neu aufbauen")
        log_to_stderr("Schlafe 5 sec")
        time.sleep(5)
#        AIS.close()
except (KeyboardInterrupt, SystemExit):
    log_to_stderr("received exception!")
    if aprs_scheduler.state != apscheduler.schedulers.base.STATE_STOPPED:
        try:
            aprs_scheduler.shutdown()
        except:
            log_to_stderr("Fehler beim Shutdown APRS-Scheduler")
    AIS.close()
    write_number_of_served_packages(number_of_served_packages)
