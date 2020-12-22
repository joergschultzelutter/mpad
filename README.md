# mpad
Multi-Purpose APRS Daemon

Python implementation of an APRS Multi-Purpose Daemon (wx forecast, sat data, get your nearest repeater ...)

Supported features:
- Wordwide wx forecast for address / zip code / lat/lon / maidenhead / ..., supporting both imperial and metric data with auto-detection of the respective standard based on the sender's call sign. By default, a user in the U.S. will receive his data in imperial format whereas international users' default will be the metric system. 
- METAR data for IATA/ICAO codes or the nearest airport to the user's position. If an airport is specified/found that does NOT support METAR, the program automatically switches to a standard WX report
- CWOP data for a specific CWOP station (or the nearest one)
- sunrise/set and moonrise/set for a given call sign (including the sender's call sign)
- position data for a given call sign/sender's call sign (human readable address, MGRS, Maidenhead, UTM, DMS)
- satellite pass data (provides e.g. the next pass of the ISS, based on the sender's call sign position)
- find your nearest repeater with optional query parameters on band and query (c4fm, dstar, fm, ...)
- Can be easily extended with additional functionality

Program features:
- very low cpu/traffic foot print (APRS filters)
- Pretty printing; whenever it is necessary to send more than one APRS message (e.g. text too long), the program tries to split up the text in a legible way. Rather than e.g. truncating the message after the 67th character, MPAD tries to keep the information groups intact. This means that e.g. if you receive temperature information, that data won't be split up into multiple messages where e.g. your first teperature digit is in message 1 and the 2nd one is in message 2.
- human-friendly keyword parser
- external (static) resources such as the list of airports, repeaters e.g. is only retrieved in e.g. weekly intervals and then stored on the local hard drive

Reimplements and uses programs and services:
- portions from WXBOT (Martin Nile, KI6WJP)
- MGRS coordinate converter (https://github.com/aydink/pymgrs)
- aprs.fi for call sign location retrieval
- openweathermap.org for wx data
- Openstreetmap / geopy for address data retrieval and conversion
- findu.com for CWOP and METAR data
- repeatermap.de for for repeater information
- APRSlib (https://pypi.org/project/aprslib/) for sending and receiving data
- and various other Python modules

Currently out of scope / known issues:
- OUTERNET logic from WXBOT is not implemented
- With its current implementation, the Openweathermap Onecall API does not return the human-readable address. Therefore, additional calls to e.g. Openstreetmap etc. are necessary.
- The available repeater data is very much EU-centric (the program uses data from repeatermap.de). Additional _free_ data sources can be added whereas available.

APRS is a registered trademark Bob Bruninga, WB4APR
