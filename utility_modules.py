#
# Multi-Purpose APRS Daemon: various utility routines
# Author: Joerg Schultze-Lutter, 2020
#

import datetime
import sys
import configparser
import os.path
from timezonefinder import TimezoneFinder

def make_pretty_aprs_messages(message_to_add: str, destination_list: list, max_len: int = 67, separator_char: str = ',', add_sep: bool = True):
    """
    Pretty Printer for APRS messages. As APRS messages are likely to be split
    up (due to the 67 chars message len limitation), this function prevents 
    'hard cuts'. Any information that is to be injected into message
    destination list is going to be checked wrt its length. If
    len(current content) + len(message_to_add) exceeds the max_len value,
    the content will not be added to the current list string but to a new
    string in the list.

    Example:

    current APRS message = 1111111111222222222233333333333444444444455555555556666666666

    Add String "Hello World !!!!" (16 chars)

    Add the string the 'conventional' way:

    Message changes to 
    Line 1 = 1111111111222222222233333333333444444444455555555556666666666Hello W
    Line 2 = orld !!!!

    This function however returns:
    Line 1 = 1111111111222222222233333333333444444444455555555556666666666
    Line 2 = Hello World !!!!

    Constraints: function assumes that the message which is to be added is 
    67 chars in size. If user tries to submit longer content, we will truncate
    the input string to 27 chars. No data will get lost, but it will not look
    as pretty as for the standard case

    Parameters
    ==========
    message_to_add: 'str' 
        message string that is to be added to the list in a pretty way
        If string is longer than 67 chars, we will truncate the information
    destination_list: 'list'
        List with string elements which will be enriched with the
        'mesage_to_add' string 
    max_len: 'int':
        Max length of the list's string len. 67 for APRS messages
    separator_char: 'str'
        Separator that is going to be used for dividing the single
        elements that the user is going to add
    add_sep: 'bool'
        True = we will add the separator when more than one item
               is in our string. This is the default
        False = do not add the separator (e.g. if we add the
                very first line of text, then we don't want a
                comma straight after the location

    Returns
    =======
    weather_forecast_array: 'list'
        List array, containing 1..n human readable strings with
        the parsed wx data
    """
    # Dummy handler in case the list is completely empty
    if not destination_list:
        destination_list.append("")

    # If new message is longer than max len then split it up with 
    # max chunks of max_len bytes and add it to the array.
    # This should never happen but better safe than sorry. 
    # Keep in mind that we only transport plain text anyway.
    if len(message_to_add) > max_len:
        string_list = split_string_to_string_list(message_string=message_to_add,max_len=max_len)
        for msg in string_list:
            destination_list.append(msg)
    else:   # try to insert
        # Get very last element from list
        string_from_list = destination_list[-1]

        # element + new string > max len? no: add to existing string, else create new element in list
        if len(string_from_list)+len(message_to_add)+1 <= max_len:
            delimiter = ""
            if len(string_from_list) > 0 and add_sep:
                delimiter = separator_char
            string_from_list = string_from_list + delimiter + message_to_add
            destination_list[-1] = string_from_list
        else:
            destination_list.append(message_to_add)

        # Special treatment hack for the very first line of text
        # This will eliminate the additional comma which might end up in here
        # Code is not pretty but it works
        if (len(destination_list) == 1):
            string_from_list = destination_list[0]
            string_from_list = string_from_list.replace(f": {separator_char}",": ")
            destination_list[0]=string_from_list

    return destination_list

def split_string_to_string_list(message_string: str, max_len: int = 67):
    """
    Force-split the string into chunks of max_len size and return a list of
    strings. This function is going to be called if the string that the user
    wants to insert exceeds more than e.g. 67 characters. In this unlikely
    case, we may not be able to add the string in a pretty format - but 
    we will split it up for the user and  


    Parameters
    ==========
    message_string: 'str'
        message string that is to be divided into 1..n strings of 'max_len"
        text length
    max_len: 'int':
        Max length of the list's string len. Default = 67 for APRS messages

    Returns
    =======
    split_strings: 'list'
        List array, containing 1..n strings with a max len of 'max_len'
    """
    split_strings = [message_string[index : index + max_len] for index in range(0, len(message_string), max_len)]
    return split_strings


def log_to_stderr(message: str):
    """
    Simple print-to-stderr-console with a time stamp

    Parameters
    ==========
    message: 'str'
        message string that is going to be printed to stderr
    """

    current_timestamp = datetime.datetime.now()
    print(current_timestamp, ": ",message, file=sys.stderr)


def check_if_file_exists(file_name: str):
    """
    Simple wrapper for whether a file exists or not

    Parameters
    ==========
    file_name: 'str'
        file whose presence we want to check

    Returns
    =======
    _: 'bool'
        True if file exists
    """

    return os.path.isfile(file_name)

def read_program_config(config_file_name: str = 'mpad.cfg'):
    """
    Read the configuration file and extract the parameter values

    Parameters
    ==========
    config_file_name: 'str'
        file whose presence we want to check

    Returns
    =======
    success: 'bool'
        True if all file exists and there was no issue with extracting
        the values from the config file
    aprsdotfi_cfg_key: 'str'
        aprs.fi API key
    openweathermapdotorg_api_key: 'str'
        openweathermap.org API key
    """

    config = configparser.ConfigParser()
    success = False
    aprsdotfi_cfg_key = openweathermapdotorg_api_key = None
    if check_if_file_exists(config_file_name):
        try:
            config.read(config_file_name)
            aprsdotfi_cfg_key=config.get('mpad_config', 'aprsdotfi_api_key')
            openweathermapdotorg_api_key = config.get('mpad_config', 'openweathermapdotorg_api_key')
            success = True
        except:
            success = False
    return success, aprsdotfi_cfg_key, openweathermapdotorg_api_key

def convert_to_plain_ascii (source_string):
    """
    Tries to convert any content to plain ascii
    Also removes German Umlauts

    Parameters
    ==========
    source_string: 'str'
        string that we want to convert to plain ascii

    Returns
    =======
    _: 'str'
        Converted string
    """
    return source_string.replace("Ü","Ue").replace("Ä","Ae").replace("Ö","Oe").replace("ü","ue").replace("ä","ae").replace("ö","oe").replace("ß","ss").encode('ascii', errors='ignore').decode()

def getdaysuntil (theweekday):
    """
    Calculate offset index between system date and the requested date offset,
    based on 'calendar' presets (e.g. calendar.MONDAY, calender.TUESDAY)
    In layman's terms: "if current day is Monday, then how many days are
    between Monday and e.g Friday" (result would be '4'; index starts at
    zero).

    If the current day name is equal to the requested day name, we
    return 7 as we assume that this is a reference to the day in the
    next week

    Parameters
    ==========
    theweekday: 'int'
        enum integer, based on 'calendar' enumerations
        e.g. calendar.WEDNESDAY

    Returns
    =======
    _: 'int'
        Number of days between current day and requested day
    """

    today = datetime.date.today()
    target_date = today + datetime.timedelta( (theweekday-today.weekday()) % 7 )
    if today != target_date:
        return (target_date-today).days
    else:
        return 7

def determine_timezone(latitude: float, longitude: float):
    """
    Determine the timezone for a given set of coordinates

    Parameters
    ==========
    latitude : 'float'
        Latitude value
    longitude : 'float'
        Longitude value

    Returns
    =======
    timezone: 'str'
        Timezone string for given coordinates or 'None' in case of an error
    """

    assert type(latitude) in [float, int]
    assert type(longitude) in [float, int]

    tf = TimezoneFinder()
    timezone = tf.timezone_at(lng=longitude, lat=latitude)
    return timezone


if __name__ == '__main__':
    my_array = []

    my_array = make_pretty_aprs_messages("Hello World: ",my_array,separator_char='|',add_sep=False)
    my_array = make_pretty_aprs_messages("Wie geht es Dir", my_array,separator_char='|')
    my_array = make_pretty_aprs_messages('jdsfhjdshfjhjkshdfjhdsjfhjhdsfhjdshfjdhsfhdhsf',my_array)
    my_array = make_pretty_aprs_messages('aaaaaaaaaabbbbbbbbbbccccccccccddddddddddeeeeeeeeeeffffffffffgggggggggghhhhhhhhhh',my_array)
    my_array = make_pretty_aprs_messages('Alter Schwede',my_array)
    print (my_array)

    log_to_stderr("Scheisse")
    print (read_program_config())

