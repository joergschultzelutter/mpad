# Action Keyword Commands

Based on the sender's call sign, MPAD automatically provides its content in the 'correct format'. By default, MPAD uses the metric system. MPAD will evaluate the sender's call sign. If a call sign from Liberia, Myanmar and the U.S. has been received, MPAD will automatically switch to the imperial system, thus providing the user wx temperature reports in Fahrenheit, speed in mph, distances in miles and so on. You can override this behavior with specific keywords (can be found at the end of this document) 
## WX data inquiries

- One or multiple spaces between the respective separators are permitted
- ALL Commands and keywords are case __insensitive__
- For most of the cases, ```wx``` inquiries can be specified without any specific keyword; just specify the address. Unless any other keyword has been specified, ```wx``` __is always assumed as default keyword__.

Action Keyword can be combined with [date](DATE_KEYWORDS.md) / [daytime](DAYTIME_KEYWORDS.md) keyword parameters: __YES__

### City, State and/or Country

#### Formats

- ```<city>, <state>; <country>```
- ```<city>, <state>```
- ```<city>; <country>```

Country = iso3166-a2 country (de, us, fr, uk, ...)
#### Example requests

- ```Los Angeles, CA``` will try to return the Wx data for ```Los Angeles, CA, United States``` (Country code is not specified --> will automatically be set to "US")
- ```Mountain View, CA; US``` will try to return the Wx data for ```Mountain View, CA, United States```
- ```Holzminden; de``` will try to return the Wx data for ```Holzminden, Germany```

#### Example response

(applicable to all wx request types)

A wx response consists of 1..n lines, The actual content as well as the message lenght is dependent on how much data is actually available. Here is an example for a wx report in metric format:

```10-Jan-21 San Francisco,CA overcast clouds morn:10c day:13c eve:12c```

```nite:11c sunrise/set 16:24/02:09UTC clouds:90% uvi:1.9 hPa:1026```

```hum:57% dewpt:4c wndspd:2m/s wnddeg:52```

Glossary:

- ```morn``` - morning temperature
- ```day``` - daytime temperature
- ```eve``` - evening temperature
- ```nite``` - nighttime temperature
- ```sunrise/set``` sunrise and sunset in UTC time zone format
- ```clouds```
- ```uvi``` - UV index
- ```hPa``` - air pressure
- ```hum``` - humidity
- ```dewpt``` - dew point
- ```wndspd``` - wind speed
- ```wnddeg``` - wind degrees
  
### Zip Codes

#### Formats

- ```zip <zipcode>[;iso3166-a2 country code]```
- ```<5-digit code>```

A zip code __with__ keyword but __without__ a country setting OR a 5-digit zip code __without__ keyword will automatically assume that the given zip code is a U.S. zip code. 

#### Example requests

- ```zip 94043``` returns the wx information for ```Mountain View, CA, United States```
- ```zip 85609``` returns the wx information for ```Dragoon, AZ, United States```
- ```zip 85609; us``` returns the wx information for ```Dragoon, AZ, United States```
- ```zip 85609; de``` returns the wx information for ```Aschheim, Germany```
- ```94043``` returns the  wx information for ```Mountain View, CA, United States```

A 5-digit zip code __without__ iso-3166-a2 qualifier automatically sets the country setting to "US". 
Zip codes can be of 3..10 characters

### Numeric Coordinates

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

#### Example response



```jo41du overcast clouds morn:-0c day:1c eve:1c nite:-0c```

```sunrise/set 08:31/16:36UTC clouds:90% uvi:0.5 hPa:1024 hum:97%```

```dewpt:0c wndspd:2m/s wnddeg:291```


Note: When a maidenhead locator is specified, the program will _not_ try to translate this information to a human readable address, meaning that WX information will reference to the given grid data and not to a human-readable address (city, street and so on)

## METAR Data for airport locations

You have three options:

- specify a specific ICAO code
- specify a specific IATA code
- specify the METAR keyword, which instructs the program to look for the nearest airport. That 'nearest' airport position can either be based on the user's own call sign or alternatively on a different user's call sign.

If the given airport or the nearest one has been found but does __not__ support METAR data, the program will try to provide you with a standard WX report for the airport's coordinates instead. If the airport is capable of providing METAR data but the METAR report cannot be retrieved, an error message is returned to the user.

Action Keyword can be combined with [date](DATE_KEYWORDS.md) / [daytime](DAYTIME_KEYWORDS.md) keyword parameters: __NO__. If WX data is returned, 'today'/'full' settings will be applied.

### ICAO METAR / wx inquiries

Get a METAR report for a specific ICAO code. If the ICAO code is valid but the airport does not provide METAR data, a default wx report is returned instead.

#### Formats

- ```icao <4-character ICAO code>```
- ```<4-character ICAO code>```

#### Example requests

```icao eddf```

```eddf```

#### Example response

(applicable to all METAR options)

```EDDF 090120Z 36005KT 9999 FEW040 00/M01 Q1019 R25L/29//95```

```R25C/29//95 R25R/////// R18/29//95 NOSIG```



Specifying an ICAO code without keyword may or may not be successful as it is processed at the end of the parser's process chain.

### IATA METAR / wx inquiries

Get a METAR report for a specific IATA code by retrieving its associated ICAO code (and then performing an ICAO metar inquiry). If the IATA code is valid but the airport does not provide METAR data, a default wx report is returned instead. If the airport is capable of providing METAR data but the METAR report cannot be retrieved, an error message is returned to the user.

#### Formats

- ```iata <3-character IATA code>```
- ```<3-character IATA code>```

#### Example requests

```iata sea```

```sea```

Specifying an IATA code without keyword may or may not be successful as it is processed at the end of the parser's process chain.

### METAR keyword

Get a METAR report for the nearest airport in relation to the user's own call sign or a different call sign

#### Formats

- ```metar <callsign>[-ssid]```
- ```metar```

If no call sign is specified, then the user's own call sign (the one that he has send us the message with) is used

#### Example requests

```metar ko4jvr-9```

```metar lb7ji```

```metar ```

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

Action Keyword can be combined with [date](DATE_KEYWORDS.md) / [daytime](DAYTIME_KEYWORDS.md) keyword parameters: __NO__

#### Formats

- ```whereami``` returns my last known coordinates
- ```whereis <callsign>[-ssid]``` returns the position information for this user

#### Example requests

- ```whereami```
- ```whereis df1jsl-1```

#### Example response

Request: ```whereis wa1gov-10``` in metric format

Result:

```Pos WA1GOV-10 Grid:FN41lu95 DMS N41.51'17, W71.00'24 Dst 5826 km```

```Brg 50deg NE UTM:19T 333431 4635605 MGRS:19TCG3343135605```

```LatLon:41.85483/-71.00667 Taunton, 02718, US Seekell Street 329```

Glossary:

- ```Grid``` - Maidenhead locator
- ```DMS``` - Coordinates in degresses/minutes/seconds
- ```Dst``` - Distance to target in km (or miles)
- ```Brg``` - Bearing
- ```UTM``` - UTM coordinates
- ```MGRS``` - MGRS coordinates
- ```LatLon``` - coordinates in numerical format
- street / zip code / country / city, if available
- ```alt``` - altitude in meters or feet, if available. 

### Sunrise/Sunset and Moonset/Moonrise

Returns the sunrise/sunset and moonset/moonrise info of the sender's position or a specific call sign. Note: values are calculated for the given day. In case the moonSET value overlaps from the previous date, then this is not taken into consideration.

Action Keyword can be combined with [date](DATE_KEYWORDS.md) / [daytime](DAYTIME_KEYWORDS.md) keyword parameters: __YES__

#### Formats

- ```riseset``` returns the values based on the sender's position
- ```riseset <callsign>[-ssid]``` returns the values based on a different call sign's position

#### Example requests

```riseset```

```riseset df1jsl-1 wednesday```

```riseset df1jsl-1```

#### Example response

```RiseSet DF1JSL-4 09-Jan GMT sun_rs 07:31-15:36 mn_sr 12:20-03:19```

- ```sun_rs``` - time settings for sunrise and sunset in GMT
- ```mn_sr``` - time settings for moonset and moonrise in GMT


### CWOP (Customer Weather's Observer Program)

Returns the latest CWOP Wx report of the nearest CWOP station (related to the sender's call sign or a different call sign) OR a specific CWOP station ID.

Action Keyword can be combined with [date](DATE_KEYWORDS.md) / [daytime](DAYTIME_KEYWORDS.md) keyword parameters: __NO__

#### Formats

- ```cwop``` returns the nearest CWOP report, based on the user's position
- ```cwop <callsign>[-ssid]``` returns the nearest CWOP report, based on the given call sign's position
- ```cwop <station_id>``` returns the weather report for the given CWOP station ID

#### Example requests

```cwop```

```cwop df1jsl-1```

```cwop at166```

#### Example response

```CWOP AT166 09-Jan-21 1C Spd 0.0km/h Gust 1.6km/h Hum 95%```

```Pres 1021.6mb Rain(cm) 1h=0.0, 24h=0.05, mn=0.05```

### Satellite passes

Retrieves the next pass of the given satellite ID for the user's position. Satellites can be specified by their satellite names as defined in the respective [amateur radio satellite tle file](http://www.celestrak.com/NORAD/elements/amateur.txt). The following rules apply:

- If a satellite name contains spaces, then these spaces will be replaced by dashes. As an example, "SAUDISAT 1C" will internally be identified by "SAUDISAT-1C"

- For convenience reasons, the ISS can be selected by requesting the satellite pass data for either __ISS__ or __ZARYA__.

- It is assumed that satellite visibility is not important to you. Therefore, potential results contain values where the respective satellite may or may not be visible from the user's position.

- if a date / daytime setting is specified, the program will try to honor that setting.

- Only the data for the next statellite pass is returned.

EXPERIMENTAL - STILL IN DEVELOPMENT

Action Keyword can be combined with [date](DATE_KEYWORDS.md) / [daytime](DAYTIME_KEYWORDS.md) keyword parameters: __YES__

#### Formats

- ```satpass <satellite_name>```

#### Example requests

- ```satpass iss```
- ```satpass zarya```
- ```satpass saudisat-1c```

### Repeater data

Retrieves the nearest repeater, based on the user's position. In addition, 'band' and 'mode' filters can be specified.

Action Keyword can be combined with [date](DATE_KEYWORDS.md) / [daytime](DAYTIME_KEYWORDS.md) keyword parameters: __NO__

#### Formats

- ```repeater [band] [mode]```

The positions for both parameters __band__ and __mode__ are position-interchangeable, meaning that ```repeater [band] [mode]``` and ```repeater [mode] [band]``` are both valid.

```Band``` parameter needs to be specified with '```m```' or '```cm```' unit of measure, e.g. ```70cm```, ```2m```, ```80m```
```Mode``` parameter can be one of the following: ```fm```, ```dstar```, ```d-star```, ```dmr```, ```c4fm```, ```tetra```, ```atv```. ```d-star``` and ```dstar``` are identical; the two options just exist because of convenience issues.

#### Example requests

- ```repeater``` returns the nearest repeater, regardless of its capabilities
- ```repeater c4fm``` returns the nearest c4fm repeater without checking the band requirements
- ```repeater 70cm``` returns the nearest 70cm repeater without checking the mode requirements
- ```repeater c4fm 70cm``` returns the nearest c4fm repeater that runs on the 70cm band
- ```repeater 70cm c4fm``` same command as in the previous example

#### Example response

```Nearest repeater Bad Iburg / Dorenberg 40 km 335 deg NNW```

```Rx 430.9375 Tx 438.5375 WIRES-X,Startreflektor DL-Nordwest C4FM```

```70cm JO42AE```



### General help

Returns general program help to the user.

Action Keyword can be combined with [date](DATE_KEYWORDS.md) / [daytime](DAYTIME_KEYWORDS.md) keyword parameters: __NO__

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

If you don't want to rely on the automatic mode, you can always override this automated setting by specifying one of the following keywords:

#### Formats

- ```mtr``` or ```metric```
- ```imp``` or ```imperial```

#### Example requests

```metric```

```imperial```

To illustrate how this works, have a look at these two examples:

Request: ```san francisco, ca; us``` (issued by my German call sign). The result is returned in metric format:

```09-Jan-21 San Francisco,CA few clouds morn:9c day:12c eve:11c```

```nite:10c sunrise/set 16:25/02:08UTC clouds:16% uvi:2.2 hPa:1025```

```hum:68% dewpt:6c wndspd:1m/s wnddeg:50```

Now let's request the same wx report - but this time, we want it to be delivered in imperial format (this is what an American user would see as default format): 

```09-Jan-21 San Francisco,CA few clouds morn:48f day:53f eve:52f```

```nite:50f sunrise/set 16:25/02:08UTC clouds:16% uvi:2.2 hPa:1025```

```hum:68% dewpt:43f wndspd:2mph wnddeg:50```

MPAD does not perform an imperial-to-metric calculation (or vice versa) but requests the desired format as part of its REST requests to e.g. Openweathermap and other services. Apart from rounding these values in order to limit the message length, all data is displayed 'as is'.

### Language

Allows you to specify a language in a (somewhat) ISO639-1 format. Default language is 'en'. 

Action Keyword can be combined with [date](DATE_KEYWORDS.md) / [daytime](DAYTIME_KEYWORDS.md) keyword parameters: __YES__

Currently, this keyword is __only__ used for WX reports from Openweathermap. In addition, it only provides a localised __ASCII__ version of the wx free text, e.g. en=```snow```, de=```Schnee```, pl=```Snieg``` so don't expect to receive e.g. a wx report APRS message with the cyrillic alphabet. I might use the language option for other purposes in the future.

#### Formats

- ```lang [iso639-1 code]```
- ```lng [iso639-1 code]```

#### Example requests

- ```lang de```
- ```Erding;de lng pl``` returns a wx report for the city of Erding in Germany where the wx report's free text part will be in Polish.

#### Supported languages

- ```af``` Afrikaans
- ```al``` Albanian
- ```ar``` Arabic
- ```az``` Azerbaijani
- ```bg``` Bulgarian
- ```ca``` Catalan
- ```cz``` Czech
- ```da``` Danish
- ```de``` German
- ```el``` Greek
- ```en``` English (__default__)
- ```eu``` Basque
- ```fa``` Persian (Farsi)
- ```fi``` Finnish
- ```fr``` French
- ```gl``` Galician
- ```he``` Hebrew
- ```hi``` Hindi
- ```hr``` Croatian
- ```hu``` Hungarian
- ```id``` Indonesian
- ```it``` Italian
- ```ja``` Japanese
- ```kr``` Korean
- ```la``` Latvian
- ```lt``` Lithuanian
- ```mk``` Macedonian
- ```no``` Norwegian
- ```nl``` Dutch
- ```pl``` Polish
- ```pt``` Portuguese
- ```ro``` Romanian
- ```ru``` Russian
- ```sv```, ```se``` Swedish
- ```sk``` Slovak
- ```sl``` Slovenian
- ```sp```, ```es``` Spanish
- ```sr``` Serbian
- ```th``` Thai
- ```tr``` Turkish
- ```ua```, ```uk``` Ukrainian
- ```vi``` Vietnamese
- ```cn``` Chinese Simplified
- ```tw``` Chinese Traditional
- ```zu``` Zulu
