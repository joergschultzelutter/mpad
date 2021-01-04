# Installation

- Clone repository
- Install Python packages 
- [MGRS coordinate converter](https://github.com/aydink/pymgrs) is already part of this repo so you don't need to install it

## Configuration

### API Access

Currently, MPAD uses two APIs for its purposes:

- aprs.fi
- openweathermap.org

If you want to host your own MPAD instance, you need to acquire your personal API access keys for both APIs and add them to MPAD's API config file. 

```
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
- __myaprsis_login_callsign__. By default, this value is set to "N0CALL" which does permit the program to connect to APRS_IS in read-only mode. Outgoing messages that respond to commands which your instance has received (see filter settings!) will only be sent to the program's log file. 
- Filter settings: MPAD uses two filters:
    __myaprs_server_filter__. This is the filter that MPAD used for connecting to APRS-IS. It is also MPAD's __primary__ filter. If an APRS message does not pass this filter, then the program won't process it. You can specify one or many call signs: Format __g/callsign1/callsign2/callsign_n__. Example: __g/MPAD__. See [APRS-IS Server-Side Filter Commands](http://www.aprs-is.net/javAPRSFilter.aspx) for further details.
    __mycallsigns_to_parse__. This is the secondary filter. In general, it is identical to the first filter but this time, it is controlled by MPAD itself. Similar to the APRS-IS filter, you can specify 1..n call signs. Obviously, these call signs must be present in the APRS-IS filter because otherwise, the program won't see the messages. This 2nd filter mainly exists for debugging purposes; you can broaden the APRS-IS filter (e.g. program call sign and your personal call sign) and then use the 2nd filter for some software development magic.
- __myaprs_server_name__ and __myaprs_server_port__. APRS-IS server/port that the program tries to connect with. Self-explanatory.
