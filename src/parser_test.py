from utility_modules import read_program_config
from input_parser import parse_input_message
from output_generator import generate_output_message
import logging


def testcall(message_text: str, from_callsign: str):
    success, aprsdotfi_api_key, openweathermapdotorg_api_key = read_program_config()
    assert success == True

    logger.debug(
        f"parsing message '{message_text}' for callsign '{from_callsign}'"
    )

    success, response_parameters = parse_input_message(
        message_text, from_callsign, aprsdotfi_api_key
    )
    logger.debug("Parser:")
    logger.debug(response_parameters)
    if success:
        logger.debug("Response:")
        logger.debug(
            generate_output_message(
                response_parameters, openweathermapdotorg_api_key
            )
        )
    else:
        logger.debug(response_parameters)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(module)s -%(levelname)s- %(message)s')
    logger = logging.getLogger(__name__)

    testcall("satpass zarya","df1jsl-1")