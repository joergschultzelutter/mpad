# mpad

Multi-Purpose APRS Daemon (Gollum might call also it _My Precious_ APRS Daemon)

Python implementation of a multi-purpose APRS daemon (WX/METAR/CWOP prediction, satellite & other sky data, find the nearest repeater to my position, user coordinates & distance etc. ...)

## Supported features

- Worldwide weather forecast for address / zip code / lat/lon / maidenhead / ... that supports both imperial and metric data with automatic detection of the respective standard based on the station's callsign. By default, users in the USA, Liberia and Myanmar receive their data in imperial format, while for international users the metric system is preset. The user can override this auto-setting with a separate keyword.
- METAR data for IATA/ICAO codes or the nearest airport to the user's position. If an airport is specified/found that does NOT support METAR, the program automatically switches to a standard WX report
- CWOP data for a given CWOP station (or the nearest one)
- Sunrise/sunset and moonrise/sunset for a given callsign (or the station's callsign)
- Position data for a given callsign/transmitter callsign (human readable address, MGRS, Maidenhead, UTM, DMS, distance between the two users, altitude)
- BETA:satellite transit data (provides e.g. the next transit of the ISS, based on the callsign position of the transmitter)
- Finds the nearest repeater to your position with optional query parameters on band and query (c4fm, dstar, fm, ...)
- Can be easily extended with additional functions and keywords

## Program specifics

- Very low cpu/traffic footprint thanks to APRS filters and local data caches.
- Pretty printing; whenever it is necessary to send more than one APRS message (e.g. when the text exceeds the APRS msg len), the program tries to split the text in a readable way. Instead of 'hard cutting' the message after the 67th character, MPAD tries to keep the information groups intact. This means that for temperature information, for example, the data is not split into multiple messages where, for example, the first temperature digit is in message 1 and the second is in message 2.
- Human-friendly parser that supports both keyword and non-keyword commands
- Supports APRS msg acknowledgments, beacons, etc. Also tries to extract APRS msg IDs from APRS messages that do not conform to APRS standards
- Automatic detection of incoming duplicate / delayed APRS message requests

## Usage examples and command syntax

[see USAGE](docs/USAGE.md)

## Dependencies and external data sources

[see DEPENDENCIES](docs/DEPENDENCIES.md)

## Installation

[see INSTALLATION](docs/INSTALLATION.md)

## Add your own keywords

[see EXTENSIONS](docs/EXTENSIONS.md)

## Technical Details and Known Issues

[see TECHNICAL_DETAILS](docs/TECHNICAL_DETAILS.md)

## The fine print

- If you intend to host an instance of this program, you must be a licensed radio amateur. BYOP (Bring your own (APRS-IS) passcode).
- Some program routines borrow logic from KI6WJP's WxBot, whose source code was immensely helpful in getting a better understanding of how to process an APRS message. If the code works, give Martin kudos. If it doesn't work, I'm the one who screwed up.
- APRS is a registered trademark of APRS Software and Bob Bruninga, WB4APR.
