# Technical Details

## Handling of incoming duplicate APRS message requests

Due to its technical nature, the APRS network might receive the same __incoming__ APRS message more than once during a short time frame - these can be duplicate or delayed messages. Wherever possible, MPAD tries to detect these duplicate messages by applying a decaying cache mechanism to all messages:

- For each incoming message that is deemed as valid ready-to-be-processed MPAD message, the program will create a cache key value, consisting of the user's call sign, the APRS message number (or ```None``` if the  message was sent without an APRS message number) and the md5-ed content of the incoming message text.
- Prior to processing the request, MPAD checks if this particular key is already present in its decaying cache. Every cache element has a life span of 60 mins and the cache accepts up to 2160 entries (default settings; configurable in ```mpad_config.py```)
- If that key is present in the cache, MPAD assumes that the __current__ request is a duplicate one.  As a result, the program will neither send a message acknowledgment (whereas applicable) nor will it process the current message request.
- If the entry for that key cannot be found in the cache, MPAD will process the request. Regardless of its status, the key element will be added to the decaying cache. This means that even messages which failed MPAD processing will still be detected as a duplicate.

For the end user, sending an identical message to MPAD within 60 mins from the same call sign will cause the following results:

- Identical APRS messages requests with __different__ APRS message IDs __can be processed__ within these 60 mins __unless__ the message is already present in the cache (these would be dupes from APRS-IS but not from the user's radio)
- Identical APRS message requests __without__ an APRS message ID __will be ignored__. Based on its unique message key (md5'ed message, call sign, message ID (in this case: ```None```)), the entry is detected as 'already processed' in the decaying database. Therefore, MPAD will ignore this message.

Once the key entry in the decaying cache has expired, sending the same message to MPAD will no longer cause a duplicate detection for this single message and MPAD will process it for you.

A decaying cache for __outgoing__ messages to the user is currently not implemented but can easily be added, if necessary.

## Known issues

- Weather report data from openweathermap:
    - Wx Alert data is not returned to the user. This can be added in a later version but keep in mind that the text is very long and would result in multiple (10-15) APRS messages per alert!
    - Access to openweathermap.org requires an API key which has a traffic limit
    - With its current implementation of its 'OneCall' API, Openweathermap does not return the human-readable address in case a query is performed for lat/lon coordinates - which is applicable to all queries from MAPD. As a result, additional calls to e.g. Openstreetmap etc. may be necessary in order to provide the user with a human readable address.
- Repeater data:
    - Currently, the repeater data may be very much EU-centric (MPAD borrows its data from repeatermap.de as well as from hearham.com). Additional _free_ repeater data sources can be added to future MPAD versions if such sources are available. If you want to see your repeater added to repeatermap.de, [please submit your data on DK3ML's site](https://www.repeatermap.de/new_repeater.php?lang=en). Alternatively, feel free to recommend free sources for repeater data and I see what I'll can do to add them to the program.
    - Apart from some internal pre-processing, the data from both input sites is taken 'as is'. There are also no dupe checks wrt the given data. When in doubt, request more than one result.
    - There are plans for migrating to a single repeater data source in one of the upcoming releases. The keyword command structure will likely stay the same.
- Time zones:
    - Currently, all timestamps returned by the program use UTC as time zone. Implicitly, __this constraint also applies to the time-related program keywords__ (see [USAGE.md](USAGE.md)) which instructs the program to return data for a certain time of the day. Dependent on your geographical location, a 'give me a wx report for today noon' may result in unwanted effects as the 'noon' part __is based on GMT__. When in doubt, do NOT limit your data to a certain time slot of the day ('full' day is the program default). I might implement local time zone data at a later point in time - for now, GMT applies.
- Satellite frequency data:
    - The creation of MPAD's local satellite database (which contains both satellite TLE and satellite frequency data) is an automated process; the matching process is based on the satellite ID. As both data sources heavily differ in data formats, some satellites may not get recognised within the satellite frequency database and therefore won't show up with available frequencies when queried via the ```satfreq``` keyword.
    - The satellite master data file is Celestrak's Amateur Radio Satellite file. Any satellites which are present in JE9PEL's datebase but are not present in the Celestrak data will be ignored.
- Openstreetmap category data:
    - MPAD honors OSM's [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim) by artificially delaying requests to OSM. Whenever you request OSM category data and you have requested more than one result, each follow-up request of that same command experiences an artificial delay between 1.2 and 3.0 seconds (random value). Therefore, requesting 5 results can take between 6 and 15 secs (excluding any additional delays for the outgoing APRS messages)
- General:
    - This program is single-threaded and will take care of one message at a time. Parallel processing of messages is not implemented.
    - APRS 'TOCALL' identifier is currently still set to default 'APRS' (see WXBOT implementation); in the long run, MPAD needs its own identifier (see http://www.aprs.org/aprs11/tocalls.txt)
    - Call signs which deviate from a 'normal' call sign pattern may not be recognised (e.g. APRS bot call signs etc) at all times. In this case, the program may not know what to do and will perform a fallback to its default mode: generate a wx report for the user's call sign.
    - Keyword-less requests or request data that was supplied in an incorrect manner is prone to misinterpretation. Mainly, that misinterpretation happens if you request a wx report for a city whose name consists of multiple parts - and you forget to specify state or country code. Example: a request for the German city of ```Bad Driburg``` (note the missing state/country data) would get misinterpreted as METAR request for the airport of Barksdale, LA (IATA code BAD / ICAO code KBAD). Specify the wx report in the official format (```Bad Driburg;de```) and you'll be fine. MPAD will notice the format qualifiers and -despite having a match on the valid IATA Code- will interpret the data as a Wx request. Nevertheless, other side effects may happen.
    - OUTERNET logic from WXBOT is not implemented

## Duty cycles and local caches

- APRS Beacon Data is sent to APRS-IS every 30 mins
- APRS Bulletin Data is sent to APRS-IS every 4 hours

Both beacon and bulletin data messages will be sent as part of a fixed duty cycle. Thanks to the APRS-IS server filters, MPAD will stay in hibernation mode unless there is a user message that it needs to process.

In order to limit the access to data from external web sites to a minimum, MPAD caches data from the following web sites and refreshes it automatically:

- Amateur satellite data (TLE data from Celestrak and JE9PEL's frequency database) is refreshed every 2 days
- Repeater data from repeatermap.de and hearham.com is refreshed every 7 days
- Airport data (IATA/ICAO airport list) from aviationweather.gov is refreshed every 30 days

Additionally, all of these data files will also be refreshed whenever the program starts. Any in-between changes to sat/repeater/airport data will not be recognised, meaning that if e.g. new repeater data was added in between, MPAD might see this data only after a few days. All of these intervals can be configured, though.

MPAD can also generate email position reports for the user. All associated emails that were sent by the program will get purged from MPAD's associated email account after 48 hrs (default setting).

## 'New' ack/rej processing

MPAD provides support for the 'old' ack/rej process (as described in aprs101.pdf) as well as for the 'new' process [http://www.aprs.org/aprs11/replyacks.txt](http://www.aprs.org/aprs11/replyacks.txt). The program does not implement the retry/backoff algorithm for retransmission of un-acknowleged messages.  It relies on the origination station to retransmit the original message that prompted the reply.
