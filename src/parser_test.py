#
# Parser Test file - you can use this code for test runs on the input parser and output generator
# The result is equivalent to what would be sent to aprs-is
# Populate the main function's 'testcall' parameter with the APRS message that you want to have parsed
#
from utility_modules import (
    read_program_config,
    make_pretty_aprs_messages,
    check_if_file_exists,
    build_full_pathname,
    create_zip_file_from_log,
)
from input_parser import parse_input_message
from output_generator import generate_output_message
import logging
from pprint import pformat
from airport_data_modules import update_local_airport_stations_file
from skyfield_modules import update_local_mpad_satellite_data
from repeater_modules import update_local_repeatermap_file
import mpad_config
from messaging_modules import send_apprise_message
import sys
import atexit
import traceback

exception_occurred = False
ex_type = ex_value = ex_traceback = None

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def testcall(message_text: str, from_callsign: str):
    global apprise_config_file

    (
        success,
        aprsdotfi_api_key,
        aprsis_callsign,
        aprsis_passcode,
        dapnet_login_callsign,
        dapnet_login_passcode,
        smtpimap_email_address,
        smtpimap_email_password,
        apprise_config_file,
    ) = read_program_config()
    assert success

    logger.info(msg=f"parsing message '{message_text}' for callsign '{from_callsign}'")

    success, response_parameters = parse_input_message(
        message_text, from_callsign, aprsdotfi_api_key
    )

    logger.info(msg=pformat(response_parameters))
    if success:
        # enrich our response parameters with all API keys that we need for
        # the completion of the remaining tasks. The APRS access details
        # are not known and will be set to simulation mode
        response_parameters.update(
            {
                "aprsdotfi_api_key": aprsdotfi_api_key,
                "dapnet_login_callsign": dapnet_login_callsign,
                "dapnet_login_passcode": dapnet_login_passcode,
                "smtpimap_email_address": smtpimap_email_address,
                "smtpimap_email_password": smtpimap_email_password,
            }
        )
        logger.info(msg="Response:")
        logger.info(msg=pformat(generate_output_message(response_parameters)))
    else:
        human_readable_message = response_parameters["human_readable_message"]
        # Dump the HRM to the user if we have one
        if human_readable_message:
            output_message = make_pretty_aprs_messages(
                message_to_add=f"{human_readable_message}",
                add_sep=False,
            )
        # If not, just dump the link to the instructions
        else:
            output_message = [
                "Sorry, did not understand your request. Have a look at my command",
                "syntax, see https://github.com/joergschultzelutter/mpad",
            ]
        logger.info(output_message)
        logger.info(msg=pformat(response_parameters))


def download_data_files_if_missing(force_download: bool = False):
    # if the user has never ever run the actual bot, some files might be missing, thus preventing us from
    # simulating the bot's actual behavior in real life. As a workaround, check if the files are missing
    # and download them, if necessary
    #

    # Read the config
    # we only need the Apprise file name
    (
        success,
        aprsdotfi_api_key,
        aprsis_callsign,
        aprsis_passcode,
        dapnet_login_callsign,
        dapnet_login_passcode,
        smtpimap_email_address,
        smtpimap_email_password,
        apprise_config_file,
    ) = read_program_config()
    assert success

    # check if airport data file is present
    if (
        not check_if_file_exists(
            build_full_pathname(mpad_config.mpad_airport_stations_filename)
        )
        or force_download
    ):
        logger.info("Updating local airport data file")
        update_local_airport_stations_file(
            airport_stations_filename=mpad_config.mpad_airport_stations_filename,
            apprise_config_file=apprise_config_file,
        )

    # check if the satellite data is present
    if (
        not check_if_file_exists(
            build_full_pathname(mpad_config.mpad_satellite_frequencies_filename)
        )
        or not check_if_file_exists(
            build_full_pathname(mpad_config.mpad_tle_amateur_satellites_filename)
        )
        or force_download
    ):
        logger.info("Updating local satellite data files")
        update_local_mpad_satellite_data(apprise_config_file=apprise_config_file)

    # check if the repeater data is present
    if (
        not check_if_file_exists(
            build_full_pathname(mpad_config.mpad_repeatermap_raw_data_filename)
        )
        or not check_if_file_exists(
            build_full_pathname(mpad_config.mpad_hearham_raw_data_filename)
        )
        or force_download
    ):
        logger.info("Updating local repeater data files")
        update_local_repeatermap_file(apprise_config_file=apprise_config_file)


def mpad_exception_handler():
    """
    This function will be called in case of a regular program exit OR
    an uncaught exception. If an exception has occurred, we will try to
    send out an Apprise message along with the stack trace to the user

    Parameters
    ==========

    Returns
    =======
    """

    if not exception_occurred:
        return

    # Send a message before we hit the bucket
    message_body = f"The MPAD process has crashed. Reason: {ex_value}"

    # Try to zip the log file if possible
    success, log_file_name = create_zip_file_from_log(mpad_config.mpad_nohup_filename)

    # check if we can spot a 'nohup' file which already contains our status
    if log_file_name and check_if_file_exists(log_file_name):
        message_body = message_body + " (log file attached)"

    # send_apprise_message will check again if the file exists or not
    # Therefore, we can skip any further detection steps here
    send_apprise_message(
        message_header="MPAD process has crashed",
        message_body=message_body,
        apprise_config_file=apprise_config_file,
        message_attachment=log_file_name,
    )


def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Custom exception handler which is installed by the
    main process. We only do a few things:
    - remember that there has been an uncaught exception
    - save the exception type / value / tracebace

    Parameters
    ==========
    exc_type:
        exception type object
    exc_value:
        exception value object
    exc_traceback:
        exception traceback object

    Returns
    =======
    """

    global exception_occurred
    global ex_type
    global ex_value
    global ex_traceback

    # set some global values so that we know why the program has crashed
    exception_occurred = True
    ex_type = exc_type
    ex_value = exc_value
    ex_traceback = exc_traceback

    logger.info(f"Core process has received uncaught exception: {exc_value}")

    # and continue with the regular flow of things
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


if __name__ == "__main__":
    # Check if the local database files exist and
    # create them, if necessary
    download_data_files_if_missing(force_download=True)

    # Register the on_exit function to be called on program exit
    atexit.register(mpad_exception_handler)

    # Set up the exception handler to catch unhandled exceptions
    sys.excepthook = handle_exception

    testcall(message_text="saturday", from_callsign="DF1JSL-1")
