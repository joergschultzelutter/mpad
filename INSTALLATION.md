# Installation

- Clone repository
- Install Python packages - see [external dependencies](DEPENDENCIES.md) 
- [MGRS coordinate converter](https://github.com/aydink/pymgrs) is already part of this repo so you don't need to install it

## Configuration

### API Access

Currently, MPAD uses two APIs for its purposes:

- aprs.fi
- openweathermap.org

If you want to host your own MPAD instance, you need to acquire your personal API access keys for both APIs and add them to MPAD's API config file. 

```bash
[mpad_config]

# API key for www.openweathermap.org
openweathermapdotorg_api_key = abcdef1234567890abcdef

# API key for www.aprs.fi
aprsdotfi_api_key = 123456.abcdefGHIJKLMN
```

### Program config

Open the program configuration file (mpad_config.py). Change the following values:

- __mpad_latitude__ and __mpad_longitude__. These are the coordinates of your local instance.
- __mpad_alias__. This is the ID which will be used by the program for all outgoing APRS messages.
- __aprsis_login_callsign__. By default, this value is set to "N0CALL" which does permit the program to connect to APRS_IS in read-only mode. You can still receive and process messages which are directed to your filter settings' call signs. However, the processed data will not be sent to the user but does end up in the program's log file.
- Filter settings. You NEED to tweak these if you intend to run your own instance. MPAD uses two filters:
    - __aprsis_server_filter__. This is the filter that MPAD used for connecting to APRS-IS. It is also MPAD's __primary__ filter. If an APRS message does not pass this filter, then the program won't process it. You can specify one or many call signs: Format __g/callsign1/callsign2/callsign_n__. Example: __g/MPAD__. See [APRS-IS Server-Side Filter Commands](http://www.aprs-is.net/javAPRSFilter.aspx) for further details.
    - __mpad_callsigns_to_parse__. This is the secondary filter. In general, it is identical to the first filter but this time, it is controlled by MPAD itself. Similar to the APRS-IS filter, you can specify 1..n call signs. Obviously, these call signs must be present in the APRS-IS filter because otherwise, the program won't see the messages. This 2nd filter mainly exists for debugging purposes; you can broaden the APRS-IS filter (e.g. program call sign and your personal call sign) and then use the 2nd filter for some software development magic.
- __aprsis_server_name__ and __aprsis_server_port__. APRS-IS server/port that the program tries to connect with. Self-explanatory.


Excerpt from mpad_config.py:
```python
##########################
# Configuration settings #
##########################
#
#################################
# General Program Configuration #
#################################
#
# Location of our process (Details: see aprs101.pdf see aprs101.pdf chapter 6 pg. 23)
mpad_latitude: str = "51.8388N"  # 8 chars fixed length, ddmm.mmN
mpad_longitude: str = "008.3266E"  # 9 chars fixed length, dddmm.mmE
#
# Program alias: This is the APRS name that will be used for all outgoing messages
mpad_alias: str = "MPAD"  # Identifier for sending outgoing data to APRS-IS
#
# APRS "TOCALL" identifier - see http://aprs.org/aprs11/tocalls.txt
# Needs to get its own identifier at a later point in time
mpad_aprs_tocall: str = "APRS"  # APRS "TOCALL"
#
####################
# APRS-IS Settings #
####################
#
# APRS-IS login user / password
aprsis_login_callsign = "N0CALL"  # APRS-IS login
aprsis_login_passcode = "-1"    # APRS-IS Passcode
#
# APRS-IS login Server / login Port
aprsis_server_name = "euro.aprs2.net"  # our login server
aprsis_server_port = 14580  # server port
#
# APRS-IS server filter setting (This is the program's PRIMARY message filter)
# Syntax: see http://www.aprs-is.net/javAPRSFilter.aspx
# If you remove/disable this filter, MPAD will 'see' all aprs-is messages
# (the whole APRS-IS traffic)
aprsis_server_filter = "g/WXBOT/WXYO"  # server filter criteria for aprs.is
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
mpad_callsigns_to_parse = ["WXBOT", "WXYO"]  # (additional) call sign filter
```