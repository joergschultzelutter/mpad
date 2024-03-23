#
# Parser Test file - you can use this code for test runs on the input parser and output generator
# The result is equivalent to what would be sent to aprs-is
# Populate the main function's 'testcall' parameter with the APRS message that you want to have parsed
#
from utility_modules import read_program_config, make_pretty_aprs_messages
from input_parser import parse_input_message
from output_generator import generate_output_message
import logging
from pprint import pformat

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
)
logger = logging.getLogger(__name__)


def testcall(message_text: str, from_callsign: str):
    (
        success,
        aprsdotfi_api_key,
        openweathermapdotorg_api_key,
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
                "openweathermapdotorg_api_key": openweathermapdotorg_api_key,
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
        # logger.info(msg=pformat(response_parameters))


if __name__ == "__main__":
    testcall(message_text="taf df1jsl-1", from_callsign="df1jsl-1")
