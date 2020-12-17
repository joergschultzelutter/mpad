# mpad
Multi-Purpose APRS Daemon

Python implementation of an APRS Multi-Purpose Daemon

Supported features:
- Wordwide wx forecast for address / zip code / lat/lon / maidenhead / ..., supporting both imperial and metric data with auto-detection of the respective standard based on the user's call sign
- METAR data for IATA/ICAO codes or the nearest airport to the user's position
- sunrise/set and moonrise/set for a given call sign
- position data for a given call sign (human readable address, MGRS, maidenhead, dms)
- satellite pass data (e.g. next pass of the ISS)
- find the nearest repeater, based on band and query (c4fm, dstar, fm, ...) parameters
- very low cpu/traffic foot print
- Pretty printing; whenever necessary, the program tries to split up the text in a legible format. This means that e.g. temperature information will not be ripped apart whenever you receive more than 1 aprs message

Reimplements and uses programs and services:
- portions from WXBOT (Martin Nile, KI6WJP)
- MGRS coordinate converter (https://github.com/aydink/pymgrs)
- aprs.fi for call sign's location retrieval
- openweathermap.org for wx data
- APRSlib (https://pypi.org/project/aprslib/) for sending and receiving data

APRS is a registered trademark Bob Bruninga, WB4APR
