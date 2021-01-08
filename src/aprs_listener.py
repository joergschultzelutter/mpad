#
# Multi-Purpose APRS Daemon
# Author: Joerg Schultze-Lutter, 2020
#
# Core process
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

from input_parser import parse_input_message
from apscheduler.schedulers.background import BackgroundScheduler
from output_generator import generate_output_message
from airport_data_modules import update_local_airport_stations_file
from repeater_modules import update_local_repeatermap_file
from skyfield_modules import update_local_tle_file
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
    send_ack,
    extract_msgno_from_defective_message,
    send_aprs_message_list,
)
import apscheduler.schedulers.base
import sys
import logging
import aprslib
import time
import mpad_config

########################################


# APRSlib callback
# Extract the fields from the APRS message, start the parsing process,
# execute the command and send the command output back to the user
def mycallback(raw_aprs_packet):

    global number_of_served_packages

    logger = logging.getLogger(__name__)

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
    addresse_string = raw_aprs_packet.get("addresse")
    #
    # The is the actual message that we are going to parse
    message_text_string = raw_aprs_packet.get("message_text")
    #
    # messagenumber, if present in the original msg (note: this is optional)
    msgno_string = raw_aprs_packet.get("msgNo")
    #
    # User's call sign. read: who has sent us this message?
    from_callsign = raw_aprs_packet.get("from")
    if from_callsign:
        from_callsign = from_callsign.upper()

    # Finally, get the format of the message that we have received
    # For content that we need to process, this should be 'message'
    # and not 'response'
    format_string = parse_aprs_data(raw_aprs_packet, "format")

    #
    # This calls a convenience handler / parser. In some rare cases, APRS
    # messages do not seem to follow the APRS messaging standard as described
    # in chapter 14 of the aprs101.pdf guide (pg. 71). Rather than sending the
    # msg no in the standard format (12345=msg_no)
    # message_text{12345
    # these senders add a closing bracket to the end of the message. Example:
    # message_text{12345}abcd
    # aprslib does not recognise this flawed package and returns the content as
    # is. Our convenience handler takes care of the issue and returns a 'clean'
    # message text and a separated message_no whereas present.
    # The trailing information (abcd) is ignored and removed.
    if not msgno_string:
        if message_text_string:
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
    # addresse_string is the sender's TARGET address (read: the target that he
    # has sent the message to). In an ideal world, this should be 'MPAD' or any
    # other call sign that the program is supposed to listen to.
    #
    # NOTE: this is a SECONDARY filter. The PRIMARY filter is defined through
    # the APRS_IS filter settings. Both filter settings can be found in the
    # mpad_config.py module. Normally, this secondary filter is obviously not
    # required as the primary aprs_is filter does a great job. If however that
    # primary filter fails, then this acts as a safe guard as we only want to
    # process and respond to messages which actually belong to us. By keeping
    # these 2 layers, you can decide to allow to pass certain packages for
    # debugging purposes.
    #
    # Is our address in the target list of call signs that we claim as owner?
    if addresse_string:
        if addresse_string in mpad_config.mpad_callsigns_to_parse:
            # Lets examine what we've got:
            # 1. Message format should always be 'message' and not 'response'
            # 2. Actual message should be populated with some content
            # Continue if both assumptions are correct
            if format_string == "message" and message_text_string:
                # This is a message that belongs to us
                logger.debug(msg=f"received raw_aprs_packet: {raw_aprs_packet}")
                # Send an ack if we did receive a message number
                # see aprs101.pdf pg. 71ff.
                if msg_no_supported:
                    send_ack(
                        myaprsis=AIS,
                        simulate_send=aprsis_simulate_send,
                        users_callsign=from_callsign,
                        source_msg_no=msgno_string,
                    )
                #
                # This is where the magic happens: Try to figure out what the user
                # wants from us. If we were able to understand the user's message,
                # 'success' will be true. In any case, the 'response_parameters'
                # dictionary will give us a hint about what to do next (and even
                # contains the parser's error message if 'success' != True)
                # input parameters: the actual message, the user's call sign and
                # the aprs.fi API access key for location lookups
                success, response_parameters = parse_input_message(
                    aprs_message=message_text_string,
                    users_callsign=from_callsign,
                    aprsdotfi_api_key=aprsdotfi_api_key,
                )
                #
                # If the 'success' parameter is True, then we should know
                # by now what the user wants from us. Now, we'll leave it to
                # another module to generate the output data of what we want
                # to send to the user.
                # The result to this post-processor will be a general success
                # status code and a list item, containing the messages that are
                # ready to be sent to the user.
                if success:
                    success, output_message = generate_output_message(
                        response_parameters=response_parameters,
                        openweathermapdotorg_api_key=openweathermapdotorg_api_key,
                    )
                    # Regardless of a success status, fire the messages to the user
                    # in case of a failure, the list item already does contain
                    # the error message to the user.
                    number_of_served_packages = send_aprs_message_list(
                        myaprsis=AIS,
                        simulate_send=aprsis_simulate_send,
                        message_text_array=output_message,
                        src_call_sign=from_callsign,
                        send_with_msg_no=msg_no_supported,
                        number_of_served_packages=number_of_served_packages,
                    )
                # darn - we failed to hail the Tripods
                else:
                    output_message = [
                        "Did not understand your request. Pls check my command syntax",
                    ]
                    number_of_served_packages = send_aprs_message_list(
                        myaprsis=AIS,
                        simulate_send=aprsis_simulate_send,
                        message_text_array=output_message,
                        src_call_sign=from_callsign,
                        send_with_msg_no=msg_no_supported,
                        number_of_served_packages=number_of_served_packages,
                    )
                    logger.debug(msg=f"Unable to grok packet {raw_aprs_packet}")


#
# MPAD main
# At first, we will set logging parameters
#
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(module)s -%(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
#
# Get the API access keys for OpenWeatherMap and APRS.fi. If we don't have those
# then there is no point in continuing
#
success, aprsdotfi_api_key, openweathermapdotorg_api_key = read_program_config()
if not success:
    logging.error(msg="Cannot find config file; aborting")
    sys.exit(0)

# Next, get the uppercase'd call sign, its aprs_is pass code and a boolean
# variable which indicates if we actually want to SEND data to APRS_IS or not
# By default, the program's call sign is N0CALL, its passcode is -1 and
# its 'simulate_send' value will be 'True', meaning that you can use the program
# in 'listen' mode without sending any actual data to aprs_is.
# If you however submit a call sign that DIFFERS from N0CALL, then the program
# will automatically calculate the correct login code for you and -in addition-
# the 'simulate_send' will be set to False, meaning that content will actually
# be sent to APRS_IS.
# By overriding the aprsis_simulate_send parameter to True, you can prevent the
# program from sending data to APRS_IS even if your call sign is not N0CALL.
aprsis_callsign, aprsis_passcode, aprsis_simulate_send = get_aprsis_passcode(
    mpad_config.aprsis_login_callsign
)
#
# Now let's read the number of served packages that we have dealt with so far
number_of_served_packages = read_number_of_served_packages()

# Define dummy values for both APRS task schedules and AIS object
aprs_scheduler = AIS = None

# Initially, refresh our local data caches
#
# Refresh the local "airport stations" file
update_local_airport_stations_file()
#
# Refresh the local "repeatermap" file
update_local_repeatermap_file()
#
# Update the satellite TLE file
update_local_tle_file()

# Now let's set up schedulers for the refresh process
# These schedulers will download the file(s) every x days
# and store the data locally, thus allowing the functions
# to read and import it whenever necessary
caching_scheduler = BackgroundScheduler()

# Set up task for IATA/ICAO data download every 30 days
caching_scheduler.add_job(
    update_local_airport_stations_file,
    "interval",
    id="airport_data",
    days=30,
    args=[],
)

# Set up task for repeater data download every 7 days
caching_scheduler.add_job(
    update_local_repeatermap_file,
    "interval",
    id="repeatermap_data",
    days=7,
    args=[],
)

# Set up task for satellite TLE data download - daily download
caching_scheduler.add_job(
    update_local_repeatermap_file,
    "interval",
    id="tle_satellite_data",
    days=1,
    args=[],
)

# start the caching scheduler
caching_scheduler.start()

#
# Finally, let's enter the 'eternal loop'
#
try:
    while True:
        # Set call sign and pass code
        AIS = aprslib.IS(aprsis_callsign, aprsis_passcode)

        # Set the APRS_IS server name and port
        AIS.set_server(mpad_config.aprsis_server_name, mpad_config.aprsis_server_port)

        # Set the APRS_IS (call sign) filter, based on our config file
        AIS.set_filter(mpad_config.aprsis_server_filter)

        # Debug what we are trying to do
        logger.debug(
            msg=f"Establish connection to APRS_IS: server={mpad_config.aprsis_server_name},"
            f"port={mpad_config.aprsis_server_port}, filter={mpad_config.aprsis_server_filter},"
            f"APRS-IS User: {aprsis_callsign}, APRS-IS passcode: {aprsis_passcode}"
        )

        AIS.connect(blocking=True)
        if AIS._connected == True:
            logger.debug(msg="Established the connection to APRS_IS")

            # Send initial beacon after establishing the connection to APRS_IS
            logger.debug(
                msg="Send initial beacon after establishing the connection to APRS_IS"
            )
            send_beacon_and_status_msg(AIS, aprsis_simulate_send)

            # Install two schedulers tasks
            # The first task is responsible for sending out beacon messages
            # to APRS; it will be triggered every 30 mins
            # The 2nd task is responsible for sending out bulletin messages
            # to APRS; it will be triggered every 4 hours
            #
            # Install scheduler task 1 - beacons
            aprs_scheduler = BackgroundScheduler()

            aprs_scheduler.add_job(
                send_beacon_and_status_msg,
                "interval",
                id="bulletin",
                minutes=30,
                args=[AIS, aprsis_simulate_send],
            )
            # Install scheduler task 2 - bulletins
            aprs_scheduler.add_job(
                send_bulletin_messages,
                "interval",
                id="status",
                hours=4,
                args=[AIS, aprsis_simulate_send],
            )
            # start both tasks
            aprs_scheduler.start()

            #
            # We are on the verge of starting the aprslib callback consumer
            # This section is going to be left only in the case of network
            # errors or if the user did raise an exception
            #
            logger.debug(msg="Starting callback consumer")
            AIS.consumer(mycallback, blocking=True, immortal=True, raw=False)

            #
            # We have left the callback, let's clean up a few things
            logger.debug("Have left the callback")
            #
            # First, stop all schedulers. Then remove the associated jobs
            # This will prevent the beacon/bulletin processes from sending out
            # messages to APRS_IS
            aprs_scheduler.pause()
            aprs_scheduler.remove_all_jobs()
            if aprs_scheduler.state != apscheduler.schedulers.base.STATE_STOPPED:
                try:
                    aprs_scheduler.shutdown()
                except:
                    logger.debug(msg="Exception during scheduler shutdown eternal loop")

            # Verbindung schließen
            logger.debug(msg="Closing APRS connection to APRS_IS")
            AIS.close()
        else:
            logger.debug(msg="Cannot re-establish connection to APRS_IS")
        # Write the number of served packages to disc
        write_number_of_served_packages(served_packages=number_of_served_packages)
        logger.debug(msg="Sleeping 5 secs")
        time.sleep(5)
#        AIS.close()
except (KeyboardInterrupt, SystemExit):
    logger.debug("received exception!")

    # write number of processed packages to disc
    write_number_of_served_packages(served_packages=number_of_served_packages)

    if aprs_scheduler:
        aprs_scheduler.pause()
        aprs_scheduler.remove_all_jobs()
        logger.debug(msg="shutting down aprs_scheduler")
        if aprs_scheduler.state != apscheduler.schedulers.base.STATE_STOPPED:
            try:
                aprs_scheduler.shutdown()
            except:
                logger.debug(msg="Exception during scheduler shutdown SystemExit loop")

    if caching_scheduler:
        logger.debug(msg="shutting down caching_scheduler")
        caching_scheduler.pause()
        caching_scheduler.remove_all_jobs()
        if caching_scheduler.state != apscheduler.schedulers.base.STATE_STOPPED:
            try:
                caching_scheduler.shutdown()
            except:
                logger.debug(msg="Exception during scheduler shutdown SystemExit loop")

    # Close the socket if it is still open
    if AIS:
        AIS.close()
