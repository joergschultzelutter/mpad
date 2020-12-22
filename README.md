# mpad
Multi-Purpose APRS Daemon

Python implementation of an APRS Multi-Purpose Daemon (wx forecast, sat data, get your nearest repeater ...)

## Supported features:
- Wordwide wx forecast for address / zip code / lat/lon / maidenhead / ..., supporting both imperial and metric data with auto-detection of the respective standard based on the sender's call sign. By default, a user in the U.S. will receive his data in imperial format whereas international users' default will be the metric system. 
- METAR data for IATA/ICAO codes or the nearest airport to the user's position. If an airport is specified/found that does NOT support METAR, the program automatically switches to a standard WX report
- CWOP data for a specific CWOP station (or the nearest one)
- sunrise/set and moonrise/set for a given call sign (including the sender's call sign)
- position data for a given call sign/sender's call sign (human readable address, MGRS, Maidenhead, UTM, DMS)
- satellite pass data (provides e.g. the next pass of the ISS, based on the sender's call sign position)
- find your nearest repeater with optional query parameters on band and query (c4fm, dstar, fm, ...)
- Can be easily extended with additional functionality

## Program features:
- very low cpu/traffic foot print (APRS filters)
- Pretty printing; whenever it is necessary to send more than one APRS message (e.g. text exceeds APRS msg len), the program tries to split up the text in a legible way. Rather than applying a 'hard' truncate  of the message after the 67th character, MPAD tries to keep the information groups intact. This means that e.g. if you receive temperature information, that data won't be split up into multiple messages where e.g. your first teperature digit is in message 1 and the 2nd one is in message 2.
- human-friendly parser with keywords
- external (static) resources such as the list of airports, repeaters e.g. are  only retrieved in e.g. weekly intervals and then stored on the local hard drive
- supports msg acknowledgment, beacons et al. Also tries to extract APRS msg IDs from APRS messages which do not follow the APRS standards

## Reimplements and uses programs and services:
- portions from WXBOT (Martin Nile, KI6WJP)
- MGRS coordinate converter (https://github.com/aydink/pymgrs)
- aprs.fi for call sign location retrieval
- openweathermap.org for wx data
- Openstreetmap / geopy for address data retrieval and conversion
- findu.com for CWOP and METAR data
- repeatermap.de for for repeater information
- APRSlib (https://pypi.org/project/aprslib/) for sending and receiving data
- and various other Python modules

## Currently out of scope / known issues:
- OUTERNET logic from WXBOT is not implemented
- With its current implementation, the Openweathermap Onecall API does not return the human-readable address. Therefore, additional calls to e.g. Openstreetmap etc. are necessary.
- The available repeater data is very much EU-centric (the program uses data from repeatermap.de). Additional _free_ data sources can be added whereas available.
- Wx alert data from openweathermap.org is not returned to the user. This can be added in a later version but keep in mind that the text is very long and would result in multiple APRS messages
- Access to openweathermap.org requires an API key which has a certain traffic limit
- 

## Usage examples
### WX data inquiries

One or multiple spaces between the respective separators are permitted

#### City, State and/or Country
Formats: 
```
<city>, <state>; <country> or
<city>, <state> or
<city>; <country>
```

Country = iso3166-a2 country

Examples:

```
Los Angeles, CA
Mountain View, CA; US
Holzminden; de
```

#### Zip Codes
Formats:
```
zip <zipcode>[;iso3166-a2 country code]
<5-digit code>
```
A zip code with keyword but without a country setting OR a 5-digit zip code without keyword will automatically assume that the given zip code is a U.S. zip code

Examples:
```
zip 94043 --> Mountain View, CA, United States
zip 85609 --> Dragoon, AZ, United States
zip 85609; us --> Dragoon, AZ, United States
zip 85609; de --> Aschheim, Germany
94043 --> Mountain View, CA, United States
```

A 5-digit zip code with no iso-3166-a2 qualifier automatically sets the country setting to "US". 
Zip codes can be of 3..10 characters

#### numeric coordinates
Format: latitude/longitude (can be positive or negative)

Examples:
```
51.8458575/8.2997425
37.773972/-122.431297
-33.447487/-70.673676
```
Whereas possible, the program will try to turn these coordinates into a human readable address

#### Maidenhead / Grid locator
Formats:
```
grid <4-or 6-character grid locator>
mh <4-or 6-character grid locator>
```

Examples:
```
grid jo41du
mh jo41
```

Note: When a maidenhead locator is specified, the program will not try to translate this information to a human readable address







# The fine print
APRS is a registered trademark Bob Bruninga, WB4APR


