# mpad

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![CodeQL](https://github.com/joergschultzelutter/mpad/actions/workflows/codeql.yml/badge.svg)](https://github.com/joergschultzelutter/mpad/actions/workflows/codeql.yml)

Multi-Purpose APRS Daemon (Gollum might also call it _My Precious_ APRS Daemon)

Python implementation of a multi-purpose APRS daemon (WX/METAR/TAF/CWOP reports, satellite & other celestial data, find the nearest repeater to my position, user coordinates & distance etc. ...)

## Supported features

- Worldwide daily/hourly weather forecast for address / zip code / lat,lon / maidenhead / ...
- METAR/TAF data for IATA/ICAO codes or the nearest airport to a user's position
- CWOP data for a given CWOP station (or the nearest one)
- Sunrise/sunset and moonrise/sunset for a given callsign (or the station's callsign)
- Extensive position data for your own callsign or a different callsign (human readable address, MGRS, Maidenhead, UTM, DMS, distance between the two users, altitude)
- Satellite transit data (provides e.g. the next transit of the ISS, based on the callsign position of the transmitter). Can distinguish between visible and non-visible passes.
- Finds the nearest repeater to your position with optional query parameters on band and mode, e.g. 2m/70cm, c4fm/dstar
- Provides uplink/downlink frequencies for a specific satellite
- Find a place of interest nearby, e.g. fuel station, supermarket
- Send a message to a DAPNET user
- Magic 8 Ball predictions
- Send an extensive APRS position report for your call sign's location to an email address via SMTP
- Radiosonde landing predictions
- Deutscher Wetterdienst WX warning broadcasts (for German users)
- Can be easily extended with additional functions and keywords

## Program specifics

- Very low cpu/traffic footprint thanks to APRS filters and local data caches.
- Pretty printing of APRS messages. Rather than splitting up the content after a max message len of 67 bytes, the program tries to split the text in a readable way which will keep the logical context of the message intact.
- Human-friendly parser that supports both keyword and also non-keyword commands
- Auto-detection of the user's system of units. Callsigns from the USA, Liberia and Myanmar will receive their data in imperial format (Miles, Fahrenheit, Feet etc), while for the rest of the world the metric system is preset. This auto-setting can be overriden with a separate keyword.
- Supports APRS msg acknowledgments, beacons, etc.
- Automatic detection of incoming duplicate / delayed APRS message requests
- Full UTF-8 support for incoming messages. For outgoing APRS messages, the configuration can be set to either 'plain ASCII' (default) or UTF-8. Email messages are not affected by this restriction

## MPAD in the media

Thank you Jason/KM4ACK for your kind video review!
[![MPAD on YouTube](https://img.youtube.com/vi/75W0UTL5eOY/0.jpg)](https://www.youtube.com/watch?v=75W0UTL5eOY)

MPAD has been added to KC2SAH's excellent off-grid radio reference. [Order yours here!](https://offgridweather.com/)
[![Great Off-Grid Radio Reference Solution!](https://img.youtube.com/vi/65AeOBy7fDM/0.jpg)](https://www.youtube.com/watch?v=65AeOBy7fDM)

## Sample dialogue with MPAD

![Screencast](https://github.com/joergschultzelutter/mpad/blob/master/docs/screencast.gif)

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

## MPAD Live Instance

(also known as 'I just want to use the damn thing')

[My MPAD instance](https://aprs.fi/#!call=a%2FMPAD&timerange=3600&tail=3600) runs on a Raspberry Pi 4 which also hosts my Pi-Hole server. I have tested MPAD on other less-performant Linux-/Mac-based hardware. If you are a tad patient, you can even run MPAD on a Raspberry Pi Zero W.

## The fine print

- If you intend to host an instance of this program, you must be a licensed radio amateur. BYOP: Bring your own (APRS-IS) passcode. If you don't know what this is, then this program is not for you.
- Some program routines borrow logic from KI6WJP's WxBot, whose source code was immensely helpful in getting a better understanding of how to process an APRS message. If the code works, give Martin kudos. If it doesn't work, I'm the one who screwed up.
- APRS is a registered trademark of APRS Software and Bob Bruninga, WB4APR.
