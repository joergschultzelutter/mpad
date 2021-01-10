# mpad

Multi-Purpose APRS Daemon

Python implementation of an APRS Multi-Purpose Daemon (WX/METAR/CWOP forecast, satellite data, nearest repeater, coordinates for user etc. ...)

## Supported features

- Wordwide wx forecast for address / zip code / lat/lon / maidenhead / ..., supporting both imperial and metric data with auto-detection of the respective standard based on the sender's call sign. By default, users in the U.S., Liberia and Myanmar will receive their data in imperial format whereas international users' default is the metric system. The user can choose to overwrite this auto-setting with a separate keyword.
- METAR data for IATA/ICAO codes or the nearest airport to the user's position. If an airport is specified/found that does NOT support METAR, the program automatically switches to a standard WX report
- CWOP data for a specific CWOP station (or the nearest one)
- sunrise/set and moonrise/set for a given call sign (including the sender's call sign)
- position data for a given call sign/sender's call sign (human readable address, MGRS, Maidenhead, UTM, DMS, distance between the two users, altitude)
- BETA:satellite pass data (provides e.g. the next pass of the ISS, based on the sender's call sign position)
- find your nearest repeater with optional query parameters on band and query (c4fm, dstar, fm, ...)
- Can be easily extended with additional functionality

## Program specifics

- Very low cpu/traffic foot print thanks to APRS filters and local data caches
- Pretty printing; whenever it is necessary to send more than one APRS message (e.g. text exceeds APRS msg len), the program tries to split up the text in a legible way. Rather than applying a 'hard' truncate to the message after the 67th character, MPAD tries to keep the information groups intact. This means that e.g. if you receive temperature information, that data won't be split up into multiple messages where e.g. your first temperature digit is in message 1 and the 2nd one is in message 2.
- Human-friendly parser, supporting both keyword- and non-keyword commands
- Supports APRS msg acknowledgments, beacons et al. Also tries to extract APRS msg IDs from APRS messages which do not follow the APRS standards
- Auto-detection of duplicate APRS message requests

## Usage examples and command syntax

[see USAGE](docs/USAGE.md)

## Dependencies and external data sources

[see DEPENDENCIES](DEPENDENCIES.md)

## Installation

[see INSTALLATION](INSTALLATION.md)

## Handling of duplicate APRS message requests

Due to its technical nature, the APRS network might receive the same APRS message more than once during a short time frame. MPAD tries to detect these duplicate messages by applying a decaying cache mechanism to all messages that it would normally process:

- For each incoming message that is deemed as valid MPAD message, the program will create a key value, consisting of the user's call sign, the APRS message number (or ```None``` if the  message was sent without an APRS message number) and the md5-ed content of the message text.
- Prior to processing the request, MPAD checks if this particular key is present in its decaying cache. Every element in that cache has a life span of 5 mins.
- If that key is present in the cache, MPAD assumes that the __current__ request is a duplicate one.  As a result, the program will neither send a message acknowledgment (whereas applicable) nor will it process the current message request.
- If the entry for that key cannot be found in the cache, MPAD will process the request and then add the key to the decaying cache.

For the end user, sending an identical message to MPAD within 5 mins from the same call sign will cause the following results:

- Identical APRS messages requests with __different__ APRS message IDs __can be processed__ within these 5 mins __unless__ the message is already present in the cache (these would be dupes from APRS-IS but not from the user's radio)
- Identical APRS message requests __without__ an APRS message ID __will be ignored__. Based on its unique message key (md5'ed message, call sign, message ID (in this case: ```None```)), the entry is detected as 'already processed' in the decaying database. Therefore, MPAD will ignore this message.

Once the entry within the decaying cache has expired, MPAD will again accept that message and process it for you.

## Known issues

- Weather report data from openweathermap:
    - Wx requests by hour / minute are currently not implemented. I might add this at a later point in time
    - Wx Alert data is not returned to the user. This can be added in a later version but keep in mind that the text is very long and would result in multiple (10-15) APRS messages per alert!
    - Access to openweathermap.org requires an API key which has a traffic limit
    - With its current implementation of its 'OneCall' API, Openweathermap does not return the human-readable address in case a query is performed for lat/lon coordinates - which is applicable to all queries from MAPD. As a result, additional calls to e.g. Openstreetmap etc. may be necessary in order to provide the user with a human readable address.
- Repeater data:
    - Currently, the repeater data is very much EU-centric (MPAD borrows its data from repeatermap.de). Additional _free_ repeater data sources can be added to future MPAD versions if such sources are available. If you want to see your repeater added to repeatermap.de, [please submit your data on DK3ML's site](https://www.repeatermap.de/new_repeater.php?lang=en). Alternatively, feel free to recommend free sources for repeater data and I see what I'll can do to add them to the program.
    - Apart from some internal pre-processing, the data is taken from repeatermap.de 'as is'. 
- Time zones:
    - Currently, all timestamps returned by the program use UTC as time zone. Implicitly, __this constraint also applies to the time-related program keywords__ (see [USAGE.md](USAGE.md)) which instructs the program to return data for a certain time of the day. Dependent on your geographical location, a 'give me a wx report for today noon' may result in unwanted effects as the 'noon' part __is based on GMT__. When in doubt, do NOT limit your data to a certain time slot of the day ('full' day is the program default). I might implement local time zone data at a later point in time - for now, GMT applies.
- General:
    - APRS 'TOCALL' identifier is currently still set to default 'APRS' (see WXBOT implementation); in the long run, MPAD needs its own identifier (see http://www.aprs.org/aprs11/tocalls.txt)
    - Call signs which deviate from a 'normal' call sign pattern may currently not be recognised (e.g. APRS bot call signs etc). In this case, the program may not know what to do and will perform a fallback to its default mode: generate a wx report for the user's call sign.
    - OUTERNET logic from WXBOT is not implemented

## Duty cycles and local caches

- APRS Beacon Data is sent to APRS-IS every 30 mins
- APRS Bulletin Data is sent to APRS-IS every 4 hours

Both beacon and bulletin data messages will be sent as part of a fixed duty cycle. Thanks to the APRS-IS server filters, MPAD will enter hibernation mode unless there is a user message that it needs to process.

In order to limit the access to data from external web sites to a minimum, MPAD caches data from the following web sites and refreshes it automatically:

- Amateur satellite data from Celestrak is refreshed on a daily basis
- Repeater data from repeatermap.de is refreshed every 7 days
- Airport data from aviationweather.gov is refreshed every 30 days

Additionally, all of these data files will also be refreshed whenever the program starts. Any in-between changes to sat/repeater/airport data will not be recognised, meaning that if e.g. new repeater data was added in between, MPAD might see this data only after a few days. All of these intervals can be configured, though.
## The fine print

- If you intend to host an instance of this program, you need to be a licensed ham radio operator. BYOP (Bring your own (APRS-IS) passcode) :-)
- APRS is a registered trademark of APRS Software and Bob Bruninga, WB4APR
