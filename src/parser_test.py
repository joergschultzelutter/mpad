#
# Parser Test file
#
from utility_modules import read_program_config
from input_parser import parse_input_message
from output_generator import generate_output_message
import logging
from pprint import pformat


def testcall(message_text: str, from_callsign: str):
    (
        success,
        aprsdotfi_api_key,
        openweathermapdotorg_api_key,
        aprsis_callsign,
        aprsis_passcode,
        dapnet_login_callsign,
        dapnet_login_passcode,
    ) = read_program_config()
    assert success

    logger.info(f"parsing message '{message_text}' for callsign '{from_callsign}'")

    success, response_parameters = parse_input_message(
        message_text, from_callsign, aprsdotfi_api_key
    )

    logger.info("Parser:")
    logger.info(pformat(response_parameters))
    if success:
        # enrich our response parameters with all API keys that we need for
        # the completion of the remaining tasks
        response_parameters.update(
            {
                "aprsdotfi_api_key": aprsdotfi_api_key,
                "openweathermapdotorg_api_key": openweathermapdotorg_api_key,
                "dapnet_login_callsign": dapnet_login_callsign,
                "dapnet_login_passcode": dapnet_login_passcode,
            }
        )
        logger.info("Response:")
        logger.info(pformat(generate_output_message(response_parameters)))
    else:
        logger.info(pformat(response_parameters))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(module)s -%(levelname)s- %(message)s"
    )
    logger = logging.getLogger(__name__)

    testcall(message_text="vispass iss saturday top5", from_callsign="df1jsl-8")
