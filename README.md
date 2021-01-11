# mpad

Multi-Purpose APRS Daemon (Gollum might call also it _My Precious_ APRS Daemon)

Python implementation of an APRS Multi-Purpose Daemon (WX/METAR/CWOP forecast, satellite & other celestial data, find the nearest repeater to my position, user coordinates & distance etc. ...)

## Supported features

- Wordwide wx forecast for address / zip code / lat/lon / maidenhead / ..., supporting both imperial and metric data with auto-detection of the respective standard based on the sender's call sign. By default, users in the U.S., Liberia and Myanmar will receive their data in imperial format whereas international users' default is the metric system. The user can choose to overwrite this auto-setting with a separate keyword.
- METAR data for IATA/ICAO codes or the nearest airport to the user's position. If an airport is specified/found that does NOT support METAR, the program automatically switches to a standard WX report
- CWOP data for a specific CWOP station (or the nearest one)
- sunrise/set and moonrise/set for a given call sign (including the sender's call sign)
- position data for a given call sign/sender's call sign (human readable address, MGRS, Maidenhead, UTM, DMS, distance between the two users, altitude)
- BETA:satellite pass data (provides e.g. the next pass of the ISS, based on the sender's call sign position)
- find the nearest repeater to your position with optional query parameters on band and query (c4fm, dstar, fm, ...)
- Can be easily extended with additional functionality and keywords

## Program specifics

- Very low cpu/traffic foot print thanks to APRS filters and local data caches
- Pretty printing; whenever it is necessary to send more than one APRS message (e.g. text exceeds APRS msg len), the program tries to split up the text in a legible way. Rather than applying a 'hard' truncate to the message after the 67th character, MPAD tries to keep the information groups intact. This means that e.g. if you receive temperature information, that data won't be split up into multiple messages where e.g. your first temperature digit is in message 1 and the 2nd one is in message 2.
- Human-friendly parser, supporting both keyword- and non-keyword commands
- Supports APRS msg acknowledgments, beacons et al. Also tries to extract APRS msg IDs from APRS messages which do not follow the APRS standards
- Auto-detection of incoming duplicate / delayed APRS message requests

## Usage examples and command syntax

[see USAGE](docs/USAGE.md)

## Dependencies and external data sources

[see DEPENDENCIES](docs/DEPENDENCIES.md)

## Installation

[see INSTALLATION](docs/INSTALLATION.md)

## Technical Details and Known Issues

[see TECHNICAL_DETAILS](docs/TECHNICAL_DETAILS.md)

## The fine print

- If you intend to host an instance of this program, you need to be a licensed ham radio operator. BYOP (Bring your own (APRS-IS) passcode).
- Some program routines borrow logic from KI6WJP's WxBot whose source code was tremendously helpful for getting a better understanding on how an APRS message has to be processed. If the code works, give Martin some credit. If it doesn't work, I am the one who screwed it up.
- APRS is a registered trademark of APRS Software and Bob Bruninga, WB4APR
