#
# Multi-Purpose APRS Daemon: Output generator
# Author: Joerg Schultze-Lutter, 2020
#
# Purpose: Generate the output that is to be sent to the user
# (based on the successfully parsed content's input message)
#

from openweathermap_modules import get_daily_weather_from_openweathermapdotorg, parse_daily_weather_from_openweathermapdotorg

def generate_output_message():


    log_to_stderr(response_parameters)
    what = response_parameters['what']
    if what == "wx":
        latitude = response_parameters['latitude']
        longitude = response_parameters['longitude']
        units = response_parameters['units']
        date_offset = response_parameters['date_offset']
        success, myweather, tz_offset, tz = get_daily_weather_from_openweathermapdotorg(latitude=latitude, longitude=longitude, units=units, date_offset=date_offset, openweathermap_api_key=openweathermapdotorg_api_key)
        if success:
            weather_forecast_array = parse_daily_weather_from_openweathermapdotorg(myweather, units, requested_address, when, when_dt)
            SendAprsMessageList(AIS, aprsis_simulate_send, weather_forecast_array, from_string, msg_no_supported)
    elif what == "help":
        SendAprsMessageList(AIS, aprsis_simulate_send, help_text_array, from_string, msg_no_supported)
    elif what == "metar":
        icao_code = response_parameters['icao']
        metar_response, found = get_metar_data(icao_code=icao_code)
        if found:
            SendSingleAprsMessage(AIS, aprsis_simulate_send, metar_response, from_string, msg_no_supported)
        else:
            print("metar nicht gefunden; noch Suche anhand Geokoordinaten implementieren")
    elif what == 'satpass':
        satellite = response_parameters['satellite']
        latitude = response_parameters['latitude']
        longitude = response_parameters['longitude']
        altitude = response_parameters['altitude']
        when_daytime = response_parameters['when_daytime']
        when = response_parameters['when']
        print("Satpass")
    elif what == 'cwop':
        latitude = response_parameters['latitude']
        longitude = response_parameters['longitude']
        cwop_id = response_parameters['cwop_id']
        print("CWOP")
    elif what == 'riseset':
        latitude = response_parameters['latitude']
        longitude = response_parameters['longitude']
        altitude = response_parameters['altitude']
        print('Riseset')
    elif what == "whereis":
        latitude = response_parameters['latitude']
        longitude = response_parameters['longitude']
        altitude = response_parameters['altitude']
        when_daytime = response_parameters['when_daytime']
        print("Eigene Position ermitteln")
    elif what == "repeater":
        latitude = response_parameters['latitude']
        longitude = response_parameters['longitude']
        altitude = response_parameters['altitude']
        repeater_band = response_parameters['repeater_band']
        repeater_mode = response_parameters['repeater_mode']
        print("Repeater ermitteln")
    else:
        # nichts gefunden; Fehlermeldung an User senden
        SendSingleAprsMessage(AIS, aprsis_simulate_send, requested_address, from_string, msg_no_supported)
        log_to_stderr(f"Unable to grok packet {packet}")
    else:
    # nichts gefunden; Fehlermeldung anm User senden
    SendSingleAprsMessage(AIS, aprsis_simulate_send, requested_address, from_string, msg_no_supported)
    log_to_stderr(f"Unable to grok packet {packet}")