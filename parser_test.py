import unittest
from utility_modules import read_program_config
from input_parser import parsemessage
from output_generator import generate_output_message
import logging


class MyTestCase(unittest.TestCase):
    def test123(self):
        success, aprsdotfi_api_key, openweathermapdotorg_api_key = read_program_config()
        assert (success == True)

        # message_text = APRS-Message excluding any message IDs etc
        message_text="satpass iss"
        # from_callsign = Sender's callsign
        from_callsign = "df1jsl-1"

        logging.debug(f"parsing message '{message_text}' for callsign '{from_callsign}'")

        success, response_parameters = parsemessage(message_text,from_callsign, aprsdotfi_api_key)
        logging.debug("Parser:")
        logging.debug(response_parameters)
        if success:
            logging.debug("Response:")
            logging.debug(generate_output_message(response_parameters, openweathermapdotorg_api_key))
        else:
            logging.debug(response_parameters)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(module)s -%(levelname)s - %(message)s')
    logging.debug('Start of program')
    unittest.main()
    logging.debug('Start of program')
