#
# Multi-Purpose APRS Daemon: Command parser
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: Core parser. Takes a look at the command that the user
# has sent to us and then tries to figure out what to do
#

import re
import maidenhead
from geopy_modules import get_reverse_geopy_data, get_geocode_geopy_data, validate_country
import calendar
import string
from airport_data_modules import validate_icao, validate_iata, get_nearest_icao
from utility_modules import convert_to_plain_ascii, getdaysuntil, log_to_stderr
from aprsdotfi_modules import get_position_on_aprsfi


from utility_modules import read_program_config
aprsdotfi_api_key = openweathermap_api_key = None

errmsg_cannot_find_coords_for_address: str = 'Cannot find coordinates for requested address'
errmsg_cannot_find_coords_for_user: str = 'Cannot find coordinates for user'
errmsg_invalid_country: str = 'Invalid country code (need ISO3166-a2)'
errmsg_invalid_state: str = 'Invalid US state'
errmsg_invalid_command: str = 'Cannot grok command'

def parsemessage(aprs_message: str, users_callsign: str, aprsdotfi_api_key: str):
    """
    Core parser. Takes care of analyzing the user's request and tries to
    figure out what has been requested (weather report, position report, ..)

    Parameters
    ==========
    aprs_message : 'str'
        up to 67 bytes of content that the user has submitted to us
    users_callsign : 'str'
        User's ham radio call sign that was used to submit the message to us

    Returns
    =======
    latitude: 'float'
        If the user has requested info related to a specific position, then
        this field contains the respective latitude.
    longitude: 'float'
        If the user has requested info related to a specific position, then
        this field contains the respective longitude.
    when: 'str'
        If the user has requested info related to a specific point in time,
        then this field contains the respective day (e.g. Monday). Related
        day references ("Today", "Tomorrow") are also possible.
    when_daytime: 'str'
        If the user has requested info related to a specific point in time,
        then this field contains the respective time of the day (e.g. "night",
        "morning"). If no specific daytime is requested, the default setting
        is "full" (returning all values for the requested day)
    what: 'str'
        Contains the actual command that the user has requested. Possible
        content: wx, help, metar, ....
    units: 'str'
        Unit of measure. Can either be "metric" (default) or
        "imperial"
    call_sign: 'str'
        Call sign if some content was requested in relation to
        a call sign (either the user's call sign or a foreign one)
    language: 'str'
        ISO 639-2 country code (currently unused)
    icao: 'str'
        ICAO code (mainly used in combination with METAR reports)
    human_readable_message: 'str'
        This is the human-readable message string that the 
        APRS response message will start with. Can be a reference
        to a position, an error message, ...
    date_offset: 'int'
        This is the numeric offset to sysdate to the 'when' day.
        Examples:
        Today = Tuesday, 'when' requested = 'Thursday' -->
        'date_offset' is '2'. 
        Today = Tuesday, 'when' requested = 'Tuesday' -->
        'date_offset' is '7' (we assume that the user wants the
        data for Tuesday next week)
    err: 'bool'
        True if an error has occurred and the message's content
        needs to be discarded. The user will receive an error 
        message
    """
    # default settings for units of measure and language
    units = "metric"
    language = "en"

    # initialize the fields that we intend to parse
    # default 'an error has occurred' marker
    err = False

    latitude = longitude = altitude = 0.0
    date_offset = -1
    when = when_daytime = what = city = state = country = zipcode = cwop_id = None
    icao = human_readable_message = satellite = repeater_band = repeater_mode = None

    # Call sign reference (either the user's call sign or someone
    # else's call sign
    call_sign = None

    # This is the general 'we have found something and we know what to do'
    # marker. If set to true, it will prevent any further attempts to parse other
    # parts of the message wrt position information (first-come-first-serve)
    found_my_duty_roster = False

    # Booleans for 'what information were we able to retrieve from the msg'
    found_when = found_when_daytime = False

    # Start the parsing process
    #
    # Have a look at the user's call sign who has sent me the message.
    # Ignore the SSID data.
    # If my user is located in the U.S., then assume that user wants data
    # not in metric but in imperial format. Note: this is an auto-prefix
    # which can be overridden by the user at a later point in time
    # Note: we do NOT examine any call sign within the APRS message text but
    # have a look at the (source) user's call sign
    matches = re.search(r"^[AKNW][a-zA-Z]{0,2}[0-9][A-Z]{1,3}", users_callsign,re.IGNORECASE)
    if matches:
        units = "imperial"

    # Now let's start with examining the message text.
    # Rule of thumb:
    # 1) the first successful match will prevent
    # parsing of *location*-related information
    # 2) If we find some data in this context, then it will
    # be removed from the original message in order to avoid
    # any additional occurrences at a later point in time.


    # Check if we have been given a specific address (city, state, country)
    if not found_my_duty_roster and not err:
        geopy_query = None
        # City / State / Country?
        regex_string = r"([\D\s]+),\s*?(\w+);\s*([a-zA-Z]{2})"
        matches = re.findall(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
        if matches:
            (city, state, country) = matches[0]
            city = string.capwords(city)
            country = country.upper()
            state = state.upper()   # in theory, this could also be a non-US state
            aprs_message = re.sub(regex_string, "", aprs_message, flags=re.IGNORECASE).strip()
            geopy_query = {'city': city, 'state': state, 'country': country}
            found_my_duty_roster = True
        # City / State
        if not found_my_duty_roster:
            regex_string = r"([\D\s]+),\s*?(\w+)"
            matches = re.findall(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
            if matches:
                (city, state) = matches[0]
                country = 'US'
                city = string.capwords(city)
                state = state.upper()
                aprs_message = re.sub(regex_string, "", aprs_message, flags=re.IGNORECASE).strip()
                geopy_query = {'city': city, 'state': state, 'country': country}
                found_my_duty_roster = True
        # City / Country
        if not found_my_duty_roster:
            regex_string = r"([\D\s]+);\s*([a-zA-Z]{2})"
            matches = re.findall(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
            if matches:
                (city, country) = matches[0]
                city = string.capwords(city)
                country = country.upper()
                state = None
                geopy_query = {'city': city, 'country': country}
                aprs_message = re.sub(regex_string, "", aprs_message, flags=re.IGNORECASE).strip()
        # Did I find something at all?
        # Yes; send the query to GeoPy and get lat/lon for the address
        if found_my_duty_roster:
            # Let's validate the given iso3166 country code
            if not validate_country(country):
                human_readable_message = f"{errmsg_invalid_country}: '{country}'"
                err = True
            # Everything seems to be ok. Try to retrieve
            # lat/lon for the given data
            if not err:
                _success, latitude, longitude = get_geocode_geopy_data(geopy_query)
                if _success:
                    human_readable_message = city
                    if state and country == "US":
                        human_readable_message += f',{state}'
                    if country and country != "US":
                        human_readable_message += f';{country}'
                else:
                    err = True
                    human_readable_message = errmsg_cannot_find_coords_for_address

    # Look for postal/zip code information
    # First, let's look for an international zip code
    # Format: zip[zipcode];[country]
    # Country = iso3166-2
    if not found_my_duty_roster and not err:
        geopy_query = None
        regex_string = r"(zip)\s*([a-zA-Z0-9-( )]{3,10});\s*([a-zA-Z]{2})"
        matches = re.findall(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
        if matches:
            (_, zipcode, country) = matches[0]
            state = None
            country = country.upper()
            aprs_message = re.sub(regex_string, "", aprs_message, flags=re.IGNORECASE).strip()
            found_my_duty_roster = True
            geopy_query = {"postalcode": zipcode, "country": country}
        if not found_my_duty_roster:
            # check for a 5-digit zip code with prefix and assume
            # that the user wants a US zip code if matched
            regex_string = r"(zip)\s*([0-9]{5})"
            matches = re.findall(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
            if matches:
                (_, zipcode) = matches[0]
                state = None
                country = "US"
                aprs_message = re.sub(regex_string, "", aprs_message, flags=re.IGNORECASE).strip()
                found_my_duty_roster = True
                geopy_query = {"postalcode": zipcode, "country": country}
        # Did I find something at all?
        # Yes; send the query to GeoPy and get lat/lon for the address
        if found_my_duty_roster:
            # First, let's validate the given iso3166 country code
            if not validate_country(country):
                human_readable_message = f"{errmsg_invalid_country}: '{country}'"
                err = True
                if not err:
                    _success, latitude, longitude = get_geocode_geopy_data(geopy_query)
                    if _success:
                        human_readable_message = f'Zip {zipcode};{country}'
                    else:
                        err = True
                        human_readable_message = errmsg_cannot_find_coords_for_address
            else:
                err = True
                human_readable_message = errmsg_cannot_find_coords_for_address

    # check if the user has requested a set of maidenhead coordinates
    # Can either be 4- or 6-character set of maidenhead coordinates
    # if found, then transform to latitude/longitude coordinates
    # and remember that the user did specify maidenhead data, henceforth
    # we will not try to convert the coordinates to an actual
    # human-readable address
    if not found_my_duty_roster and not err:
        regex_string = r"(grid|mh)\s*([a-zA-Z]{2}[0-9]{2}[a-zA-Z]{0,2})"
        matches = re.search(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
        if matches:
            (latitude, longitude) = maidenhead.to_location(matches[2])
            found_my_duty_roster = True
            human_readable_message = f"{matches[2]}"
            aprs_message = re.sub(regex_string, "", aprs_message, flags=re.IGNORECASE).strip()

    # Check if the user has requested information wrt a 4-character ICAO code
    # if we can find the code, then check if the airport is METAR-capable. If
    # that is not the case, then return the do not request METAR data but a
    # regular wx report
    #
    if not found_my_duty_roster and not err:
        regex_string = r"(icao)\s*([a-zA-Z0-9]{4})"
        matches = re.findall(pattern=regex_string,string=aprs_message, flags=re.IGNORECASE)
        if matches:
            (_, icao) = matches[0]
            aprs_message = re.sub(regex_string, "", aprs_message).strip()
            # try to look up the airport coordinates based on the ICAO code
            _success, latitude, longitude, metar_capable, icao = validate_icao(icao)
            if _success:
                what = "metar"
                found_my_duty_roster = True
                human_readable_message = f"METAR for '{icao}'"
                # If we did find the airport but it is not METAR-capable,
                # then supply a wx report instead
                if not metar_capable:
                    what = "wx"
                    icao = None
                    human_readable_message = f"Wx for '{icao}'"
            else:
                icao = None

    # Check if the user has requested information wrt a 3-character IATA code
    # if we can find the code, then check if the airport is METAR-capable. If
    # that is not the case, then return the do not request METAR data but a
    # regular wx report
    #
    if not found_my_duty_roster and not err:
        regex_string = r"(iata)\s*([a-zA-Z0-9]{3})"
        matches = re.findall(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
        if matches:
            (_, iata) = matches[0]
            aprs_message = re.sub(regex_string, "", aprs_message).strip()
            # try to look up the airport coordinates based on the IATA code
            _success, latitude, longitude, metar_capable, icao = validate_iata(iata)
            if _success:
                what = "metar"
                found_my_duty_roster = True
                human_readable_message = f"METAR for '{icao}'"
                # If we did find the airport but it is not METAR-capable,
                # then supply a wx report instead
                if not metar_capable:
                    what = "wx"
                    icao = None
                    human_readable_message = f"Wx for '{icao}'"
            else:
                icao = None

    # Check if the user has specified lat/lon information
    if not found_my_duty_roster and not err:
        regex_string = r"([\d\.,\-]+)\/([\d\.,\-]+)"
        matches = re.search(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
        if matches:
            _success = True
            try:
                latitude = float(matches[1])
                longitude = float(matches[2])
            except:
                latitude = longitude = 0
                _success = False
            if _success:
                # try to get human-readable coordinates
                _success, city, state, country, zipcode = get_reverse_geopy_data(latitude=latitude, longitude=longitude, language=language)
                if _success:
                    if city:
                        human_readable_message = city
                        if country:
                            # Geopy returns the state information as full-length
                            # text. Let's use the zip code in order to limit the
                            # space that is used in the message
                            if zipcode and country == 'US':
                                human_readable_message = f'{human_readable_message},{zipcode}'
                            human_readable_message += f';{country}'
                else:
                    # We didn't find anything; use the original input
                    human_readable_message = f"latitude {latitude}/longitude {longitude}"
                aprs_message = re.sub(regex_string, "", aprs_message).strip()
                found_my_duty_roster = True
            else:
                human_readable_message = "Error while parsing coordinates"
                err = True

    # Check if the user wants one of the following info
    # for a specific call sign WITH or withOUT SSID:
    # wx (Weather report for the user's position)
    # whereis (location information for the user's position)
    # riseset (Sunrise/Sunset and moonrise/moonset info)
    # metar (nearest METAR data for the user's position)
    # CWOP (nearest CWOP data for user's position)
    #
    # First check the APRS message and see if the user has submitted
    # a call sign with the message (we will first check for a call
    # sign with SSID, followed by a check for the call sign without
    # SSID). If no SSID was found, then just check for the command
    # sequence and -if found- use the user's call sign
    #
    if not found_my_duty_roster and not err:
        regex_string=r"(wx|whereis|riseset|cwop|metar)\s*([a-zA-Z0-9]{1,3}[0-9][a-zA-Z0-9]{0,3}-[0-9]{1,2})"
        matches = re.search(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
        if matches:
            what = matches[1].lower()
            call_sign = matches[2].upper()
            aprs_message = re.sub(regex_string, "", aprs_message).strip()
            found_my_duty_roster = True
        if not found_my_duty_roster:
            regex_string = r"(wx|whereis|riseset|cwop|metar)\s*([a-zA-Z0-9]{1,3}[0-9][a-zA-Z0-9]{0,3})"
            matches = re.search(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
            if matches:
                what = matches[1].lower()
                call_sign = matches[2].upper()
                found_my_duty_roster = True
                aprs_message = re.sub(regex_string, "", aprs_message).strip()
        if not found_my_duty_roster:
            regex_string = r"(wx|whereis|riseset|cwop|metar)"
            matches = re.search(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
            if matches:
                what = matches[1].lower()
                call_sign = users_callsign
                found_my_duty_roster = True
                aprs_message = re.sub(regex_string, "", aprs_message).strip()
        if found_my_duty_roster:
            _success, latitude, longitude, altitude, call_sign = get_position_on_aprsfi(call_sign, aprsdotfi_api_key)
            if _success:
                if what =='wx':
                    human_readable_message = f'Wx of {call_sign}'
                elif what == 'riseset':
                    human_readable_message = f'Rise/Set for {call_sign}'
                elif what == 'whereis':
                    human_readable_message = f'Pos for {call_sign}'
                elif what == 'cwop':
                    human_readable_message = f'CWOP for {call_sign}'
                elif what == 'metar':
                    icao = get_nearest_icao(latitude, longitude)
                    if icao:
                        _success, latitude, longitude, metar_capable, icao = validate_icao(icao)
                        if _success:
                            what = "metar"
                            found_my_duty_roster = True
                            human_readable_message = f"METAR for '{icao}'"
                            aprs_message = re.sub(r"(icao)([a-zA-Z0-9]{4})", "", aprs_message).strip()
                            # If we did find the airport but it is not METAR-capable,
                            # then supply a wx report instead
                            if not metar_capable:
                                what = "wx"
                                icao = None
                                human_readable_message = f"Wx for '{icao}'"
                        else:
                            icao = None
            else:
                human_readable_message = f"{errmsg_cannot_find_coords_for_user} {call_sign}"
                err = True

    # Check if the user wants information about aspecific CWOP ID
    if not found_my_duty_roster and not err:
        regex_string = r"cwop\s*(\w*)"
        matches = re.search(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
        if matches:
            cwop_id = matches[1].upper()
            what = 'cwop'
            human_readable_message = f'CWOP for {cwop_id}'
            found_my_duty_roster = True
            aprs_message = re.sub(regex_string, "", aprs_message, flags=re.IGNORECASE).strip()

    # Check if the user wants to gain information about an upcoming satellite pass
    if not found_my_duty_roster and not err:
        regex_string = r"satpass\s*(\w*)"
        matches = re.search(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
        if matches:
            satellite = matches[1].upper()
            what = 'satpass'
            human_readable_message = f'SatPass of {satellite}'
            found_my_duty_roster = True
            aprs_message = re.sub(regex_string, "", aprs_message, flags=re.IGNORECASE).strip()

    # Check if the user wants us to search for the nearest repeater
    # this function always relates to the user's own call sign and not to
    # foreign ones. The user can ask us for the nearest repeater in
    # optional combination with band and/or mode (FM, C4FM, DSTAR et al)
    #
    # Search for repeater-mode-band
    if not found_my_duty_roster and not err:
        regex_string = r"repeater\s*(fm|dstar|d-star|dmr|c4fm|tetra|atv)\s*(\d.?\d*(?:cm|m)\b)"
        matches = re.search(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
        if matches:
            repeater_mode = matches[1].upper()
            repeater_band = matches[2].lower()
            found_my_duty_roster = True
            aprs_message = re.sub(regex_string, "", aprs_message, flags=re.IGNORECASE).strip()
        # If not found, search for repeater-band-mode
        if not found_my_duty_roster:
            regex_string = r"repeater\s*(\d.?\d*(?:cm|m)\b)\s*(fm|dstar|d-star|dmr|c4fm|tetra|atv)\b"
            matches = re.search(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
            if matches:
                repeater_mode = matches[2].upper()
                repeater_band = matches[1].lower()
                found_my_duty_roster = True
                aprs_message = re.sub(regex_string, "", aprs_message, flags=re.IGNORECASE).strip()
        # if not found, search for repeater - mode
        if not found_my_duty_roster:
            regex_string = r"repeater\s*(fm|dstar|d-star|dmr|c4fm|tetra|atv)\b"
            matches = re.search(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
            if matches:
                repeater_mode = matches[1].upper()
                repeater_band = None
                found_my_duty_roster = True
                aprs_message = re.sub(regex_string, "", aprs_message, flags=re.IGNORECASE).strip()
        # if not found, search for repeater-band
        if not found_my_duty_roster:
            regex_string = r"repeater\s*(\d.?\d*(?:cm|m)\b)"
            matches = re.search(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
            if matches:
                repeater_band = matches[1].lower()
                repeater_mode = None
                found_my_duty_roster = True
                aprs_message = re.sub(regex_string, "", aprs_message, flags=re.IGNORECASE).strip()
        # If not found, just search for the repeater keyword
        if not found_my_duty_roster:
            regex_string = r"repeater"
            matches = re.search(pattern=regex_string, string=aprs_message, flags=re.IGNORECASE)
            if matches:
                repeater_band = None
                repeater_mode = None
                found_my_duty_roster = True
                aprs_message = re.sub(regex_string, "", aprs_message, flags=re.IGNORECASE).strip()
        if found_my_duty_roster:
            what = "repeater"
            human_readable_message = "Repeater"
            if repeater_band:
                human_readable_message+= f' {repeater_band}'
            if repeater_mode:
                human_readable_message += f' {repeater_mode}'
            _success, latitude, longitude, altitude, call_sign = get_position_on_aprsfi(users_callsign, aprsdotfi_api_key)
            if not _success:
                err = True
                human_readable_message = f"{errmsg_cannot_find_coords_for_user} {call_sign}"

    #
    # We have reached the end of the 'standard' position data processing
    # for that kind of data which may come with a command AND an associated
    # parameter. By this point in time, we may know 'what' the user wants.
    # However, we still don't know for what time slot the user wants the
    # data. In addition, the 'what' question might still be unanswered.
    # Henceforth, the remainder of the original message is going to be
    # split up into separate sub string which we are now going to examine
    # in a more detailed approach.
    #
    # Hint: unlike the previous parse attempts, we no longer discard the
    # parsed information from the original string. We also don't abort
    # the search with an error in case some content could not get parsed
    # as the next iteration may contain still some valid data

    # Split up the remainder of the string into multiple single strings
    if not err:
        wordlist = aprs_message.split()
        for word in wordlist:

            # Look for a single 5-digit code
            # if found then assume that it is a zip code from the US
            # and set all variables accordingly
            if not found_my_duty_roster and not err:
                matches = re.findall(pattern=r"^([0-9]{5})$", string=word)
                if matches:
                    zipcode = matches[0]
                    state = None
                    country = "US"
                    found_my_duty_roster = True
                    human_readable_message = f"Zip {zipcode};{country}"
                    _success, latitude, longitude = get_geocode_geopy_data({"postalcode": zipcode, "country": country})
                    if not _success:
                        err = True
                        human_readable_message = errmsg_cannot_find_coords_for_address
                        break

            # Look for a 4..6 character Maidenhead coordinate
            if not found_my_duty_roster and not err:
                matches = re.search(pattern=r"^([a-zA-Z]{2}[0-9]{2}[a-zA-Z]{0,2})$", string=word, flags=re.IGNORECASE)
                if matches:
                    (latitude, longitude) = maidenhead.to_location(matches[0])
                    found_my_duty_roster = True
                    human_readable_message = f"{matches[0]}"

            # Look for a call sign either with or without SSID
            # note: in 99% of all cases, a single call sign means that
            # the user wants to get wx data - but we are not going to
            # assign the 'what' info for now and just extract the call sign
            if not found_my_duty_roster and not err:
                matches = re.search(pattern=r"^([a-zA-Z0-9]{1,3}[0-9][a-zA-Z0-9]{0,3}-[0-9]{1,2})$", string=word)
                if matches:
                    call_sign = matches[0].upper()
                    found_my_duty_roster = True
                if not found_my_duty_roster:
                    matches = re.search(pattern=r"^([a-zA-Z0-9]{1,3}[0-9][a-zA-Z0-9]{0,3})$", string=word)
                    if matches:
                        call_sign = matches[0].upper()
                        found_my_duty_roster = True
                if found_my_duty_roster:
                    _success, latitude, longitude, altitude, call_sign = get_position_on_aprsfi(call_sign, aprsdotfi_api_key)
                    if not _success:
                        human_readable_message = f"{errmsg_cannot_find_coords_for_user} {call_sign}"
                        err = True
                    else:
                        human_readable_message = call_sign

            # Try to check if the user has submitted an IATA code without
            # submitting a specific pre- qualifier prefix
            # If yes, then assume that we want METAR data unless the airport
            # does not support METAR (in that case, we will go for standard wx)
            if not found_my_duty_roster and not err:
                matches = re.search(pattern=r"^([a-zA-Z0-9]{4})$", string=word)
                if matches:
                    _success, latitude, longitude, metar_capable, icao = validate_icao(word)
                    if _success:
                        what = "metar"
                        found_my_duty_roster = True
                        human_readable_message = f"METAR for '{icao}'"
                        # If we did find the airport but it is not METAR-capable,
                        # then supply a wx report instead
                        if not metar_capable:
                            what = "wx"
                            icao = None
                            human_readable_message = f"Wx for '{icao}'"

            # Try to check if the user has submitted an IATA code without
            # submitting a specific pre- qualifier prefix
            # If yes, then assume that we want METAR data unless the airport
            # does not support METAR (in that case, we will go for standard wx)
            if not found_my_duty_roster:
                matches = re.search(pattern=r"^([a-zA-Z0-9]{3})$", string=word)
                if matches:
                    _success, latitude, longitude, metar_capable, icao = validate_iata(word)
                    if _success:
                        found_my_duty_roster = True
                        what = "metar"
                        found_my_duty_roster = True
                        human_readable_message = f"METAR for '{icao}'"
                        # If we did find the airport but it is not METAR-capable,
                        # then supply a wx report instead
                        if not metar_capable:
                            what = "wx"
                            icao = None
                            human_readable_message = f"Wx for '{icao}'"

            # if the user has specified the 'metar' request, then
            # try to determine the nearest airport in relation to
            # the user's own call sign position
            matches = re.search(r"^(metar)$", word,re.IGNORECASE)
            if matches:
                _success, latitude, longitude, altitude, call_sign = get_position_on_aprsfi(users_callsign, aprsdotfi_api_key)
                if _success:
                    icao = get_nearest_icao(latitude, longitude)
                    if icao:
                        _success, latitude, longitude, metar_capable, icao = validate_icao(icao)
                        if _success:
                            what = "metar"
                            human_readable_message = f"METAR for '{icao}'"
                            found_my_duty_roster = True
                            # If we did find the airport but it is not METAR-capable,
                            # then supply a wx report instead
                            if not metar_capable:
                                what = "wx"
                                icao = None
                                human_readable_message = f"Wx for '{icao}'"
            #
            #
            #
            # At this point, we should know now what data the user wants
            # from us and have retrieved the associated lat/lon information
            # (if applicable).
            #
            # Let's now check for other relevant keywords
            #

            # User wants his own position on aprs.fi?
            if not found_my_duty_roster and not err:
                matches = re.search(r"^(whereami)$", word, re.IGNORECASE)
                if matches:
                    what = 'whereis'
                    call_sign = users_callsign
                    found_my_duty_roster = True
                    human_readable_message = f'Pos for {call_sign}'
                    _success, latitude, longitude, altitude, call_sign = get_position_on_aprsfi(users_callsign, aprsdotfi_api_key)
                    if not _success:
                        err = True
                        human_readable_message = f"{errmsg_cannot_find_coords_for_user} {call_sign}"

            # Parse the "when" information if we don't have an error
            # and if we haven't retrieved the command data in a previous run
            if not found_when and not err:
                found_when, when, date_offset = parse_when(word)

            # Parse the "when_daytime" information if we don't have an error
            # and if we haven't retrieved the command data in a previous run
            if not found_when_daytime and not err:
                found_when_daytime, when_daytime = parse_when_daytime(word)

            # check if the user wants to receive the help pages
            if not found_my_duty_roster and not err:
                matches = re.search(r"^(info|help)$", word, re.IGNORECASE)
                if matches and not what:
                    what = "help"
                    found_my_duty_roster = True

            # check if the user wants to change the numeric format
            # metric is always default, but we also allow imperial
            # format if the user explicitly asks for it
            # hint: these settings are not tied to the program's
            # duty roster
            matches = re.search(r"^(mtr|metric)$", word, re.IGNORECASE)
            if matches:
                units = "metric"
            matches = re.search(r"^(imp|imperial)$", word, re.IGNORECASE)
            if matches:
                units = "imperial"

            # check if the user wants to change the language
            # for openweathermap.com (currently fix for 'en' but
            # might change in the future
            # hint: setting is not tied to the program's duty roster
            matches = re.search(r"^(lang|lng)([a-zA-Z]{2})$", word, re.IGNORECASE)
            if matches:
                language = matches[2].lower()

    # Default checks outside of the 'for' loop - we may not have everything
    # we need so let's have a look.

    # Check if there is no reference to any position. This can be the case if
    # the user has requested something like 'tonight' where MPAD is to return
    # the weather for the user's call sign position. However, only do this if
    # the user has submitted a 'when' information (we don't care about the
    # 'when_daytime') as otherwise, garbage data will trigger a wx report

    if not found_my_duty_roster:
        # the user has specified a time setting (e.g. 'today') so we know that
        # he actually wants us something to do (rather than just sending
        # random garbage data to us
        if when:
            # First, have a look at the user's complete call sign
            #including SSID
            _success, latitude, longitude, altitude, call_sign = get_position_on_aprsfi(users_callsign, aprsdotfi_api_key)
            if _success:
                human_readable_message = f"{call_sign}"
                found_my_duty_roster = True
            else:
                # we haven't found anything? Let's get rid of the SSID and
                # give it one final try. If we still can't find anything,
                # then we will give up
                matches = re.search(r"^(([A-Z0-9]{1,3}[0123456789][A-Z0-9]{0,3})-([A-Z0-9]{1,2}))$", users_callsign)
                if matches:
                    _success, latitude, longitude, altitude, call_sign = get_position_on_aprsfi(matches[2].upper(), aprsdotfi_api_key)
                    if _success:
                        found_my_duty_roster = True
                        human_readable_message = f"{call_sign}"
                    else:
                        human_readable_message = errmsg_cannot_find_coords_for_user
                        err = True
        else:
            human_readable_message = errmsg_invalid_command
            err = True

    # Apply default to 'when' setting if still not populated
    if not found_when and not err:
        when = 'today'
        found_when = True
        date_offset = 0

    # apply default to 'when_daytime' if still not populated
    if not found_when_daytime and not err:
        when_daytime = 'full'
        found_when_daytime = True

    # apply default to 'what' if still not populated
    if not what and not err:
        what = 'wx'

    # finally, convert the requested address to plain ascii
    if human_readable_message:
        human_readable_message = convert_to_plain_ascii(human_readable_message)

    response_parameters = {
        'latitude': latitude,
        'longitude': longitude,
        'altitude': altitude,
        'when': when,
        'when_daytime': when_daytime,
        'what': what,
        'units': units,
        'call_sign': call_sign,
        'language': language,
        'icao': icao,
        'human_readable_message': human_readable_message,
        'date_offset': date_offset,
        'satellite': satellite,
        'repeater_band': repeater_band,
        'repeater_mode': repeater_mode,
        'city': city,
        'state': state,
        'country': country,
        'zipcode': zipcode,
        'cwop_id': cwop_id
    }
    _success = True
    if err:
        _success = False

    return _success, response_parameters

def parse_when(word: str):
    """
    Parse the 'when' information of the user's message
    (specific day or relative day such as 'tomorrow'
    Parameters
    ==========
    word : 'str'
        portion from the original APRS message that we want to examine

    Returns
    =======
    found_when: 'bool'
        Current state of the 'when' parser. True if content has been found
    when: 'str'
        If we found some 'when' content, then its normalized content is
        returned with this variable
    date_offset: 'int'
        If we found some 'when' content, then this
        field contains the tnteger offset in reference to the current day.
        Value between 0 (current day) and 7
    """
    found_when = False
    when = None
    date_offset = -1

    matches = re.search(r"^(tonite|tonight)$", word, re.IGNORECASE)
    if matches and not found_when:
        when = "today"
        found_when = True
        date_offset = 0
    matches = re.search(r"^(today)$", word, re.IGNORECASE)
    if matches and not found_when:
        when = "today"
        found_when = True
        date_offset = 0
    matches = re.search(r"^(tomorrow)$", word, re.IGNORECASE)
    if matches and not found_when:
        when = "tomorrow"
        found_when = True
        date_offset = 1
    matches = re.search(r"^(monday|mon)$", word, re.IGNORECASE)
    if matches and not found_when:
        when = "monday"
        found_when = True
        date_offset = getdaysuntil(calendar.MONDAY)
    matches = re.search(r"^(tuesday|tue)$", word, re.IGNORECASE)
    if matches and not found_when:
        when = "tuesday"
        found_when = True
        date_offset = getdaysuntil(calendar.TUESDAY)
    matches = re.search(r"^(wednesday|wed)$", word, re.IGNORECASE)
    if matches and not found_when:
        when = "wednesday"
        found_when = True
        date_offset = getdaysuntil(calendar.WEDNESDAY)
    matches = re.search(r"^(thursday|thu)$", word, re.IGNORECASE)
    if matches and not found_when:
        when = "thursday"
        found_when = True
        date_offset = getdaysuntil(calendar.THURSDAY)
    matches = re.search(r"^(friday|fri)$", word, re.IGNORECASE)
    if matches and not found_when:
        when = "friday"
        found_when = True
        date_offset = getdaysuntil(calendar.FRIDAY)
    matches = re.search(r"^(saturday|sat)$", word, re.IGNORECASE)
    if matches and not found_when:
        when = "saturday"
        found_when = True
        date_offset = getdaysuntil(calendar.SATURDAY)
    matches = re.search(r"^(sunday|sun)$", word, re.IGNORECASE)
    if matches and not found_when:
        when = "sunday"
        found_when = True
        date_offset = getdaysuntil(calendar.SUNDAY)
    matches = re.search(r"^(current|now)$", word, re.IGNORECASE)
    if matches and not found_when:
        when = "now"
        found_when = True
        date_offset = 0
    return found_when, when, date_offset
    
def parse_when_daytime(word: str):
    """
    Parse the 'when_daytime' information of the user's message
    (can either be the 'full' day or something like 'night','morning')
    ==========
    word : 'str'
        portion from the original APRS message that we want to examine

    Returns
    =======
    found_when_daytime: 'bool'
        Current state of the 'when_daytime' parser. True if content has been found
    when_daytime: 'str'
        If we found some 'when_daytime' content, then its normalized content is
        returned with this variable
    """
    found_when_daytime = False
    when_daytime = None

    # Parse the 'when_daytime' information
    matches = re.search(r"^(full)$", word, re.IGNORECASE)
    if matches and not found_when_daytime:
        when_daytime = "full"
        found_when_daytime = True
    matches = re.search(r"^(morn|morning)$", word, re.IGNORECASE)
    if matches and not found_when_daytime:
        when_daytime = "morning"
        found_when_daytime = True
    matches = re.search(r"^(day|daytime|noon)$", word, re.IGNORECASE)
    if matches and not found_when_daytime:
        when_daytime = "daytime"
        found_when_daytime = True
    matches = re.search(r"^(eve|evening)$", word, re.IGNORECASE)
    if matches and not found_when_daytime:
        when_daytime = "evening"
        found_when_daytime = True
    matches = re.search(r"^(nite|night|tonite|tonight)$", word, re.IGNORECASE)
    if matches and not found_when_daytime:
        when_daytime = "night"
        found_when_daytime = True

    return found_when_daytime, when_daytime



if __name__ == '__main__':
    success, aprsdotfi_api_key, openweathermap_api_key = read_program_config()
    print(parsemessage('repeater 70cm dmr','df1jsl-1', aprsdotfi_api_key))
