# Technical Details

## Handling of incoming duplicate APRS message requests

Due to its technical nature, the APRS network might receive the same __incoming__ APRS message more than once during a short time frame - these can be duplicate or delayed messages. Wherever possible, MPAD tries to detect these duplicate messages by applying a decaying cache mechanism to all messages:

- For each incoming message that is deemed as valid ready-to-be-processed MPAD message, the program will create a cache key value, consisting of the user's call sign, the APRS message number (or ```None``` if the  message was sent without an APRS message number) and the md5-ed content of the incoming message text.
- Prior to processing the request, MPAD checks if this particular key is already present in its decaying cache. Every cache element has a life span of 5 mins.
- If that key is present in the cache, MPAD assumes that the __current__ request is a duplicate one.  As a result, the program will neither send a message acknowledgment (whereas applicable) nor will it process the current message request.
- If the entry for that key cannot be found in the cache, MPAD will process the request. Regardless of its status, the key element will be added to the decaying cache. This means that even messages which failed MPAD processing will still be detected as a duplicate.

For the end user, sending an identical message to MPAD within 5 mins from the same call sign will cause the following results:

- Identical APRS messages requests with __different__ APRS message IDs __can be processed__ within these 5 mins __unless__ the message is already present in the cache (these would be dupes from APRS-IS but not from the user's radio)
- Identical APRS message requests __without__ an APRS message ID __will be ignored__. Based on its unique message key (md5'ed message, call sign, message ID (in this case: ```None```)), the entry is detected as 'already processed' in the decaying database. Therefore, MPAD will ignore this message.

Once the key entry in the decaying cache has expired, sending the same message to MPAD will no longer cause a duplicate detection for this single message and MPAD will process it for you.

A decaying cache for __outgoing__ messages to the user is currently not implemented but can easily be added, if necessary.

## Known issues

- Weather report data from openweathermap:
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

Both beacon and bulletin data messages will be sent as part of a fixed duty cycle. Thanks to the APRS-IS server filters, MPAD will stay in hibernation mode unless there is a user message that it needs to process.

In order to limit the access to data from external web sites to a minimum, MPAD caches data from the following web sites and refreshes it automatically:

- Amateur satellite data from Celestrak is refreshed on a daily basis
- Repeater data from repeatermap.de is refreshed every 7 days
- Airport data from aviationweather.gov is refreshed every 30 days

Additionally, all of these data files will also be refreshed whenever the program starts. Any in-between changes to sat/repeater/airport data will not be recognised, meaning that if e.g. new repeater data was added in between, MPAD might see this data only after a few days. All of these intervals can be configured, though.
