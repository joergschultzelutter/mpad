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
)
from input_parser import parse_input_message
from output_generator import generate_output_message
import logging
from pprint import pformat
from airport_data_modules import update_local_airport_stations_file
from skyfield_modules import update_local_mpad_satellite_data
from repeater_modules import update_local_repeatermap_file
from mpad_config import (
    mpad_airport_stations_filename,
    mpad_satellite_frequencies_filename,
    mpad_tle_amateur_satellites_filename,
)
from mpad_config import (
    mpad_hearham_raw_data_filename,
    mpad_repeatermap_raw_data_filename,
)

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def testcall(message_text: str, from_callsign: str):
    (
        success,
        aprsdotfi_api_key,
        aprsis_callsign,
        aprsis_passcode,
        dapnet_login_callsign,
        dapnet_login_passcode,
        smtpimap_email_address,
        smtpimap_email_password,
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


def download_data_files_if_missing():
    # if the user has never ever run the actual bot, some files might be missing, thus preventing us from
    # simulating the bot's actual behavior in real life. As a workaround, check if the files are missing
    # and download them, if necessary
    #
    # check if airport data file is present
    if not check_if_file_exists(build_full_pathname(mpad_airport_stations_filename)):
        logger.info("Updating local airport data file")
        update_local_airport_stations_file(mpad_airport_stations_filename)

    # check if the satellite data is present
    if not check_if_file_exists(
        build_full_pathname(mpad_satellite_frequencies_filename)
    ) or not check_if_file_exists(
        build_full_pathname(mpad_tle_amateur_satellites_filename)
    ):
        logger.info("Updating local satellite data files")
        update_local_mpad_satellite_data()

    # check if the repeater data is present
    if not check_if_file_exists(
        build_full_pathname(mpad_repeatermap_raw_data_filename)
    ) or not check_if_file_exists(build_full_pathname(mpad_hearham_raw_data_filename)):
        logger.info("Updating local repeater data files")
        update_local_repeatermap_file()


if __name__ == "__main__":
    # Check if the local database files exist and
    # create them, if necessary
    download_data_files_if_missing()

    testcall(message_text="saturday", from_callsign="DF1JSL-1")
