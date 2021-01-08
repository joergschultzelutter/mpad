# Action Keyword Commands

Based on the sender's call sign, MPAD automatically provides its content in the 'correct format'. By default, MPAD uses the metric system. MPAD will evaluate the sender's call sign. If a call sign from Liberia, Myanmar and the U.S. has been received, MPAD will automatically switch to the imperial system, thus providing the user wx temperature reports in Fahrenheit, speed in mph, distances in miles and so on. You can override this behavior with specific keywords (can be found at the end of this document) 
## WX data inquiries

- One or multiple spaces between the respective separators are permitted
- ALL Commands and keywords are case __insensitive__
- For most of the cases, ```wx``` inquiries can be specified without any specific keyword; just specify the address. Unless any other keyword has been specified, ```wx``` __is always assumed as default keyword__.

Action Keyword can be combined with [date](date_keywords.md) / [daytime](daytime_keywords.md) keyword parameters: __YES__

### City, State and/or Country

#### Formats

- ```<city>, <state>; <country>```
- ```<city>, <state>```
- ```<city>; <country>```

Country = iso3166-a2 country (de, us, fr, uk, ...)
#### Example requests

- ```Los Angeles, CA```
- ```Mountain View, CA; US```
- ```Holzminden; de```

### Zip Codes

#### Formats

- ```zip <zipcode>[;iso3166-a2 country code]```
- ```<5-digit code>```

A zip code __with__ keyword but __without__ a country setting OR a 5-digit zip code __without__ keyword will automatically assume that the given zip code is a U.S. zip code. 

#### Example requests

- ```zip 94043``` returns the wx information for Mountain View, CA, United States
- ```zip 85609``` returns the wx information for Dragoon, AZ, United States
- ```zip 85609; us``` returns the wx information for Dragoon, AZ, United States
- ```zip 85609; de``` returns the wx information for Aschheim, Germany
- ```94043``` returns the  wx information for Mountain View, CA, United States

A 5-digit zip code __without__ iso-3166-a2 qualifier automatically sets the country setting to "US". 
Zip codes can be of 3..10 characters

### numeric coordinates

Format: latitude/longitude (can be positive or negative)

#### Example requests

- ```51.8458575/8.2997425```
- ```37.773972/-122.431297```
- ```-33.447487/-70.673676```

Whereas possible, the program will try to turn these coordinates into a human readable address

### Maidenhead / Grid locator

#### Formats

- ```grid <4-or 6-character grid locator>```
- ```mh <4-or 6-character grid locator>```

#### Example requests

- ```grid jo41du```
- ```mh jo41```

Note: When a maidenhead locator is specified, the program will _not_ try to translate this information to a human readable address

## METAR Data for airport locations

You have three options:

- specify a specific ICAO code
- specify a specific IATA code
- specify the METAR keyword, which instructs the program to look for the nearest airport. That 'nearest' airport position can either be based on the user's own call sign or alternatively on a different user's call sign.

If the given airport or the nearest one has been found but does __not__ support METAR data, the program will try to provide you with a standard WX report for the airport's coordinates instead. If the airport is capable of providing METAR data but the METAR report cannot be retrieved, an error message is returned to the user.

Action Keyword can be combined with [date](date_keywords.md) / [daytime](daytime_keywords.md) keyword parameters: __NO__. If WX data is returned, 'today'/'full' settings will be applied.

### ICAO METAR / wx inquiries

Get a METAR report for a specific ICAO code. If the ICAO code is valid but the airport does not provide METAR data, a default wx report is returned instead.

#### Formats

- ```icao <4-character ICAO code>```
- ```<4-character ICAO code>```

#### Example requests

- ```icao eddf```
- ```eddf```

Specifying an ICAO code without keyword may or may not be successful as it is processed at the end of the parser's process chain.

### IATA METAR / wx inquiries

Get a METAR report for a specific IATA code by retrieving its associated ICAO code (and then performing an ICAO metar inquiry). If the IATA code is valid but the airport does not provide METAR data, a default wx report is returned instead. If the airport is capable of providing METAR data but the METAR report cannot be retrieved, an error message is returned to the user.

#### Formats

- ```iata <3-character IATA code>```
- ```<3-character IATA code>```

#### Example requests

- ```iata sea```
- ```sea```

Specifying an IATA code without keyword may or may not be successful as it is processed at the end of the parser's process chain.

### METAR keyword

Get a METAR report for the nearest airport in relation to the user's own call sign or a different call sign

#### Formats

- ```metar <callsign>[-ssid]```
- ```metar```

If no call sign is specified, then the user's own call sign (the one that he has send us the message with) is used

#### Example requests

- ```metar ko4jvr-9```
- ```metar lb7ji```
- ```metar ```

Based on the user's lat/lon, the program will then try to find the nearest airport for you. If that airport supports METAR data, the program is going to return METAR data to the user. Otherwise, it will try to pull a standard wx report for the airport's coordinates. If the airport is capable of providing METAR data but the METAR report cannot be retrieved, an error message is returned to the user.

### WhereIs

Returns the geocoordinates/address info of the sender's position or a specific call sign. Respose data includes:

- Maidenhead locator
- MGRS coordinates
- DMS coordinates
- UTM coordinates
- Human-readable address (whereas available)
- Distance, direction and bearing to the call sign (if requested position differs from user's position)
- Altitude information whereas present

Action Keyword can be combined with [date](date_keywords.md) / [daytime](daytime_keywords.md) keyword parameters: __NO__

#### Formats

- ```whereami``` returns my last known coordinates
- ```whereis <callsign>[-ssid]``` returns the position information for this user

#### Example requests

- ```whereami```
- ```whereis df1jsl-1```

### Sunrise/Sunset and Moonrise/Moonset

Returns the sunrise/sunset and moonrise/moonset info of the sender's position or a specific call sign. Note: values are calculated for the given day. In case the moonSET value overlaps from the previous date, then this is not taken into consideration.

Action Keyword can be combined with [date](date_keywords.md) / [daytime](daytime_keywords.md) keyword parameters: __YES__

#### Formats

- ```riseset``` returns the values based on the sender's position
- ```riseset <callsign>[-ssid]``` returns the values based on a different call sign's position

#### Example requests

- ```riseset```
- ```riseset df1jsl-1```

### CWOP (Customer Weather's Observer Program)

Returns the nearest CWOP station's weather report (related to the sender's call sign or a different call sign) OR a specific CWOP ID's weather report to the user.

Action Keyword can be combined with [date](date_keywords.md) / [daytime](daytime_keywords.md) keyword parameters: __NO__

#### Formats

- ```cwop``` returns the nearest CWOP report, based on the user's position
- ```cwop <callsign>[-ssid]``` returns the nearest CWOP report, based on the given call sign's position
- ```cwop <station_id>``` returns the weather report for the given CWOP station ID

#### Example requests

- ```cwop```
- ```cwop df1jsl-1```
- ```cwop at166```

### Satellite passes

Retrieves the next pass of the given satellite ID for the user's position. Satellites can be specified by their satellite names as defined in the respective [amateur radio satellite tle file](http://www.celestrak.com/NORAD/elements/amateur.txt). The following rules apply:

- If a satellite name contains spaces, then these spaces will be replaced by dashes. As an example, "SAUDISAT 1C" will internally be identified by "SAUDISAT-1C"

- For convenience reasons, the ISS can be selected by requesting the satellite pass data for either __ISS__ or __ZARYA__.

- It is assumed that satellite visibility is not important to you. Therefore, potential results contain values where the respective satellite may or may not be visible from the user's position.

- if a date / daytime setting is specified, the program will try to honor that setting.

- Only the data for the next statellite pass is returned.

EXPERIMENTAL - STILL IN DEVELOPMENT

Action Keyword can be combined with [date](date_keywords.md) / [daytime](daytime_keywords.md) keyword parameters: __YES__

#### Formats

- ```satpass <satellite_name>```

#### Example requests

- ```satpass iss```
- ```satpass zarya```
- ```satpass saudisat-1c```

### Repeater data

Retrieves the nearest repeater, based on the user's position. In addition, 'band' and 'mode' filters can be specified.

Action Keyword can be combined with [date](date_keywords.md) / [daytime](daytime_keywords.md) keyword parameters: __NO__

#### Formats

- ```repeater [band] [mode]```

The positions for both parameters __band__ and __mode__ are position-interchangeable

```Band``` parameter needs to be specified with '```m```' or '```cm```' unit of measure, e.g. ```70cm```, ```2m```, ```80m```
```Mode``` parameter can be one of the following: ```fm```, ```dstar```, ```d-star```, ```dmr```, ```c4fm```, ```tetra```, ```atv```. ```d-star``` and ```dstar``` are identical; the two options just exist because of convenience issues.

#### Example requests

- ```repeater``` returns the nearest repeater, regardless of its capabilities
- ```repeater c4fm``` returns the nearest c4fm repeater without checking the band requirements
- ```repeater 70cm``` returns the nearest 70cm repeater without checking the mode requirements
- ```repeater c4fm 70cm``` returns the nearest c4fm repeater that runs on the 70cm band
- ```repeater 70cm c4fm``` same command as in the previous example

### General help

Returns general program help to the user.

Action Keyword can be combined with [date](date_keywords.md) / [daytime](daytime_keywords.md) keyword parameters: __NO__

#### Formats

- ```info```
- ```help```

#### Example requests

- ```info```
- ```help```

### Switching between the metric and imperial system

By default, the program will automatically switch from the metric system (default) to the imperial system if the __sender's__ call sign is from Liberia, Myanmar or the United States (per Wikipedia, these are the only three countries which still use the imperial system over the metric system).

- metric system (__default__): temperatures in degrees Celsius, speed in km/h, rain levels in cm etc.
- imperial system: temperatures in degress Fahrenheit, speed in mph, rain levels in inch etc.

Action Keyword can be combined with [date](date_keywords.md) / [daytime](daytime_keywords.md) keyword parameters: __YES__. The automated process is part of the program core and even overriding the setting by one of the imperial/metric keywords can be done at any time. Dependent on the information that you have requested, the program may or may not honor the information.

If you don't want to rely on the automatic mode, you can override the automated setting by specifying the following keywords:

#### Formats

- ```mtr``` or ```metric```
- ```imp``` or ```imperial```

#### Example requests

- ```metric```
- ```imperial```
