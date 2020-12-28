import unittest
from utility_modules import read_program_config
from input_parser import parsemessage
from output_generator import generate_output_message


class MyTestCase(unittest.TestCase):
    def test123(self):
        success, aprsdotfi_api_key, openweathermapdotorg_api_key = read_program_config()
        assert (success == True)

#        message_text="whereis CA5NIW-R"
        message_text="whereis k6cdf-6"
        from_callsign = "df1jsl-1"

        print(f"parsing message '{message_text}' for callsign '{from_callsign}'")

        success, response_parameters = parsemessage(message_text,from_callsign, aprsdotfi_api_key)
        if success:
            print (generate_output_message(response_parameters, openweathermapdotorg_api_key))
        else:
            print (response_parameters)

if __name__ == '__main__':
    unittest.main()
