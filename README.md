# mpad

Multi-Purpose APRS Daemon (Gollum might call also it _My Precious_ APRS Daemon)

Python implementation of a multi-purpose APRS daemon (WX/METAR/CWOP prediction, satellite & other sky data, find the nearest repeater to my position, user coordinates & distance etc. ...)

## Supported features

- Worldwide daily/hourly weather forecast for address / zip code / lat,lon / maidenhead / ...
- METAR data for IATA/ICAO codes or the nearest airport to the user's position
- CWOP data for a given CWOP station (or the nearest one)
- Sunrise/sunset and moonrise/sunset for a given callsign (or the station's callsign)
- Extensive position data for your own callsign or a different callsign (human readable address, MGRS, Maidenhead, UTM, DMS, distance between the two users, altitude)
- Satellite transit data (provides e.g. the next transit of the ISS, based on the callsign position of the transmitter). Can distinguish between visible and non-visible passes.
- Finds the nearest repeater to your position with optional query parameters on band and query (c4fm, dstar, fm, ...)
- Find a place of interest nearby (e.g. fuel station, supermarket, ...)
- Send a message to a DAPNET user
- Magic 8 Ball predictions :-)
- Send an extensive APRS position report for your call sign's location to an email address via SMTP 
- Can be easily extended with additional functions and keywords

## Program specifics

- Very low cpu/traffic footprint thanks to APRS filters and local data caches. Can even be run on a Raspberry Pi Zero (if you are a bit patient)
- Pretty printing of APRS messages. Rather than splitting up the content after a max message len of 67 bytes, the program tries to split the text in a readable way which will keep the logical context of the message intact.
- Human-friendly parser that supports both keyword and also non-keyword commands
- Auto-detection of the user's system of units. Callsigns from the USA, Liberia and Myanmar will receive their data in imperial format (Miles, Fahrenheit, Feet etc), while for the rest of the world the metric system is preset. This auto-setting can be overriden with a separate keyword.
- Supports APRS msg acknowledgments, beacons, etc.
- Automatic detection of incoming duplicate / delayed APRS message requests
- Full UTF-8 support for incoming messages. For outgoing APRS messages, the configuration can be set to either 'plain ASCII' (default) or UTF-8. Email messages are not affected by this restriction

## Usage and command syntax

[Usage information](docs/USAGE.md) and the command keywords:

- [Action commands](docs/COMMANDS/ACTION_KEYWORDS.md)

- [Date settings](docs/COMMANDS/DATE_KEYWORDS.md)

- [Daytime settings](docs/COMMANDS/DAYTIME_KEYWORDS.md)

## Example requests and responses

[see EXAMPLES](docs/EXAMPLES.md)

## Dependencies and external data sources

[see DEPENDENCIES](docs/DEPENDENCIES.md)

## Install your own MPAD instance

[see INSTALLATION](docs/INSTALLATION.md)

## Add your own keywords

[see EXTENSIONS](docs/EXTENSIONS.md)

## Technical Details and known issues

[see TECHNICAL_DETAILS](docs/TECHNICAL_DETAILS.md)

## The fine print

- If you intend to host an instance of this program, you must be a licensed radio amateur. BYOP: Bring your own (APRS-IS) passcode. If you don't know what this is, then this program is not for you.
- Some program routines borrow logic from KI6WJP's WxBot, whose source code was immensely helpful in getting a better understanding of how to process an APRS message. If the code works, give Martin kudos. If it doesn't work, I'm the one who screwed up.
- APRS is a registered trademark of APRS Software and Bob Bruninga, WB4APR.
