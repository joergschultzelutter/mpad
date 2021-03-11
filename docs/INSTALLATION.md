# Installation

- Clone the repository
- Install Python packages - see [external dependencies](DEPENDENCIES.md)
- Populate the API access keys and amend the program configuration (see next paragraphs). You can keep the default settings for ```aprsis_login_callsign``` and ```aprsis_login_passcode``` if you just want to listen to the traffic that __my local MPAD instance__ processes. However, if you intend to __send__ data to APRS-IS, you must change these settings as well as the values for the primary/secondary filter and the program's alias.
- Once you have finished the setup of the config data, you can run the ```parser_test.py``` program. Running this test cose is literally equivalent to processing an APRS message - the only thing that's missing is the connection and data exchange between MPAD and APRS-IS. Populate the message text and run the ```parser_test.py``` module. If an output message is generated then you can assume that all program modules have been successfully installed.

```python
if __name__ == "__main__":
    testcall(message_text="deensen;de tomorrow", from_callsign="df1jsl-8")
```

## Configuration

### API Access

Currently, MPAD uses three APIs for its purposes:

- aprs.fi
- openweathermap.org
- DAPNET API

If you want to host your own MPAD instance, you need to acquire your personal API access keys for aprs.fi and openweathermap.org APIs and add these to MPAD's API config file (```mpad_api_access_keys.cfg```). An empty config template file is part of the repository. If you are not a registered DAPNET user, set the DAPNET callsign in the config file to N0CALL. When MPAD encounters this DAPNET user, it will refrain from sending content to DAPNET.

Additionally, you also need to set your APRS-IS login credentials (callsign and passcode). By default, the login callsign is set to ```N0CALL``` which does permit the program to connect to APRS_IS in read-only mode. You can still receive and process messages (based on your filter settings' call signs). However, any outgoing message will not be sent to the user (via APRS-IS) but ends up in the program's log file. Setting the user's call sign to ```N0CALL``` will automatically enforce the program to enter read-only mode. ```aprsis_login_passcode``` is automatically set to ```-1``` and no data will be sent to APRS-IS.

```python
[mpad_config]

# API key for www.openweathermap.org
openweathermapdotorg_api_key = abcdef1234567890abcdef

# API key for www.aprs.fi
aprsdotfi_api_key = 123456.abcdefGHIJKLMN

# Access credentials for aprs-id
# Any callsign different from N0CALL will disable the listen-only
# mode, meaning that MPAD will send data to APRS-IS
aprsis_login_callsign = N0CALL
aprsis_login_passcode = -1

# DAPNET access credentials
# If the callsign is set to N0CALL, APRS-DAPNET gateway
# will be disabled
dapnet_login_callsign = N0CALL
dapnet_login_passcode = -1
```

### Program configuration

Open the program configuration file (```mpad_config.py```). Change/Review the following base settings:

- ```mpad_latitude``` and ```mpad_longitude```. These are the coordinates of your local instance. Once your instance of MPAD is up and running, it will submit APRS broadcasts to APRS, thus allowing other users to see your station info on services such as aprs.fi
- ```mpad_alias```. This is the identifier/station name which will be used by the program for all outgoing APRS messages
- ```mpad_aprs_tocall``` - The program's (unique) APRS "TOCALL" identifier. MPAD has just hatched and currently has no "TOCALL" identifier of its own. This may change in the future.

You also need to set the APRS-IS access and server credentials:

- Filter settings. You NEED to tweak these if you intend to run your own instance with your own call sign (see also ```mpad_alias```). MPAD uses two filters:
    - ```aprsis_server_filter```. This is the filter that MPAD used for connecting to APRS-IS. It is also MPAD's __primary filter__. If an APRS message does not pass this filter, then the program won't process it. You can specify one or many call signs: Format ```g/callsign1/callsign2/callsign_n```. Example: ```g/MPAD```. See [APRS-IS Server-Side Filter Commands](http://www.aprs-is.net/javAPRSFilter.aspx) for further details.
    - ```mpad_callsigns_to_parse```. This is the __secondary filter__. Unlike the primary filter, this one is controlled by MPAD itself and similar to the APRS-IS filter, you can specify 1..n call signs. Obviously, at least a subset of these call signs must be present in the APRS-IS filter because otherwise, MPAD won't even see the message. This 2nd filter mainly exists for debugging purposes; you can broaden the APRS-IS filter (e.g. program call sign and your personal call sign) and then use the 2nd filter for some software development magic.
- ```aprsis_server_name``` and ```aprsis_server_port```. APRS-IS server/port that the program tries to connect with. Self-explanatory (I hope).
- Tune the ```mpad_msg_cache_time_to_live``` and/or ```mpad_msg_cache_max_entries``` parameter if too many messages are detected as duplicates and are not getting processed. Default is 60 mins
- Configure the ```mpad_beacon_altitude_ft``` parameter. This is the beacon's altitude in __feet__ (not in meters)
- By default, MPAD will send out ASCII messages. If you prefer to send unicode messages to the user, set the ```mpad_enforce_unicode_messages``` flag to ```True```. Note that this flag only applies to outgoing messages; incoming messages in unicode format are always honored.
- By default, MPAD already supports a couple of OpenStreetMap object categories. If you want to add more categories, change the ```osm_supported_keyword_categories``` list. Note that you are required to use the OSM native category wording - see comment below.
- Change the ```mpad_default_user_agent``` of you run your own MPAD instance and/or fork the repo.

Excerpt from ```mpad_config.py```:
```python
###########################
# Constants, do not change#
###########################
#
mpad_version: str = "0.01"
#
# APRS position report: message symbol
# see also http://www.aprs.org/symbols/symbolsX.txt and aprs_communication.py
# on how this is used. Normally, you don't want to change these settings
#
aprs_table: str = "/"  # APRS symbol table (/=primary \=secondary, or overlay)
aprs_symbol: str = "?"  # APRS symbol: Server
#
# Delay settings: These sleep settings are applied for each SINGLE message that is sent out
# to APRS-IS. If the program has to send two bulletin messages, then the total run time of\
# sending out those bulletins is 2 * 3 secs
#
packet_delay_long: float = 5.0  # packet delay in seconds after sending data to aprs-is
packet_delay_short: float = 3.0  # packet delay after sending an acknowledgment, bulletin or beacon
#
##########################
# Configuration settings #
##########################
#
#################################
# General Program Configuration #
#################################
#
# Location of our process (Details: see aprs101.pdf see aprs101.pdf chapter 6 pg. 23)
# Ensure to honor the format settings as described in the specification, otherwise
# your package might get rejected and/or not surface on aprs.fi
# Degrees: lat: 0-90, lon: 0-180
# Minutes and Seconds: 00-60
mpad_latitude: str = "ddmm.ssN"  # 8 chars fixed length, ddmm.ssN
mpad_longitude: str = "dddmm.ssE"  # 9 chars fixed length, dddmm.ssE
#
# Program alias: This is the APRS name that will be used for all outgoing messages
mpad_alias: str = "MPAD"  # Identifier for sending outgoing data to APRS-IS
#
# Altitude in *FEET* (not meters) for APRS beacon. Details: see aprs101.pdf chapter 8
mpad_beacon_altitude_ft = 123
#
# APRS "TOCALL" identifier - see http://aprs.org/aprs11/tocalls.txt
# Needs to get its own identifier at a later point in time
mpad_aprs_tocall: str = "APRS"  # APRS "TOCALL"
#
####################
# APRS-IS Settings #
####################
#
# APRS-IS login Server / login Port
aprsis_server_name = "euro.aprs2.net"  # our login server
aprsis_server_port = 14580  # server port
#
# APRS-IS server filter setting (This is the program's PRIMARY message filter)
# Syntax: see http://www.aprs-is.net/javAPRSFilter.aspx
# If you remove/disable this filter, MPAD will 'see' all aprs-is messages
# (the whole APRS-IS traffic)
aprsis_server_filter = "g/MPAD"  # server filter criteria for aprs.is
#
#############################
# Secondary filter settings #
#############################
#
#
# MPAD SECONDARY filter setting. This filter will be applied to those
# messages which have made it past the PRIMARY filter (from APRS-IS)
# If that secondary filter is also passed, then we will have a look
# at the user's message and try to process it
#
mpad_callsigns_to_parse = ["MPAD"]  # (additional) call sign filter
#
##############################################################
# Time-to-live settings for the decaying APRS message cache #
#############################################################
#
# The first value represents the time span for how long MPAD considers incoming
# messages as duplicates if these messages have been sent to the program
# For each processed message (regardless of its actual success state), MPAD
# is going to add a key to a decaying dictionary. That key consists of
# the user's call sign, the APRS message ID (or - if not present - 'None) and
# an md5'ed version of the message text. If another delayed or duplicate
# message is received within that specified time frame, that message is going
# to be ignored by the program
# The 2nd value represents the max. number of entries that the decaying cache
# is going to accept
#
mpad_msg_cache_time_to_live = 60 * 60  # ttl = 60 minutes
mpad_msg_cache_max_entries = 2160  # 2160 possible entries (max. of 36 per min is possible)
#
############################################
# Character encoding for outgoing messages #
############################################
#
# By default, MPAD will send out ASCII messages to its users even though UTF-8 is
# supported (see http://www.aprs.org/aprs12/utf-8.txt) for both incoming and
# outgoing messages. However, many radios such as my FTM-400XDE and the FT3DE
# are unable to cope with UTF-8 messages and don't display these messages in a
# proper way.
# If you do want MPAD to enable for OUTGOING unicode messages, then set this
# marker to True. INCOMING messages are always processed with unicode in mind.
#
# Future versions of this switch should check whether it is possible to build a
# list of supported unicode 'TOCALL' devices from the official list tocall list
# (http://www.aprs.org/aprs11/tocalls.txt). MPAD could then decide whether a
# device is unicode capable or not - and activate unicode whenever it is supported.
#
mpad_enforce_unicode_messages = True
#
# Openstreetmap 'special phrases'
# The values in this list need to match the ones in the OSM
# documentation: https://wiki.openstreetmap.org/wiki/Nominatim/Special_Phrases/EN
# Add/remove categories if necessary but ensure that the keywords' writing
# matches the one in the OSM documentation (this is case sensitive data!)
#
osm_supported_keyword_categories = [
    "aerodrome",
    "alpine_hut",
    "ambulance_station",
    "atm",
    "bakery",
    "bank",
    "butcher",
    "car_rental",
    "car_repair",
    "charging_station",
    "chemist",
    "clinic",
    "college",
    "deli",
    "dentist",
    "department_store",
    "doctor",
    "drinking_water",
    "dry_cleaning",
    "electronics",
    "fire_station",
    "fuel",
    "hairdresser",
    "hospital",
    "hostel",
    "hotel",
    "information",
    "laundry",
    "mall",
    "motorcycle",
    "optician",
    "pharmacy",
    "phone",
    "photographer",
    "police",
    "post_box",
    "post_office",
    "pub",
    "shoes",
    "subway",
    "supermarket",
    "taxi",
    "telephone",
    "tobacco",
    "toilets",
    "train_station",
    "university",
]
#
# Default user agent for accessing aprs.fi, openstreetmap et al
# Change this if you run your own MPAD instance
mpad_default_user_agent = (
    "multi-purpose-aprs-daemon/0.0.1 (+https://github.com/joergschultzelutter/mpad/)"
)
#
# DAPNET API server and transmitter group
#
mpad_dapnet_api_server = "http://www.hampager.de:8080/calls"
mpad_dapnet_api_transmitter_group = "dl-all"
```
