# mpad - Usage and Command Syntax

Rupe of thumb: The program's default is __always__ a wx report for the given address/coordinates. This assumption is valid as long as the user has not specified a keyword that tells the program to do something different.


## WX data inquiries

- One or multiple spaces between the respective separators are permitted
- Commands and keywords are case insensitive
- For most of the cases, wx inquiries can be specified without any specific keyword; just specify the address. Unless any other keyword has been specified, wx is always assumed as default.

### City, State and/or Country

Formats:

```
<city>, <state>; <country>
<city>, <state>
<city>; <country>
```

Country = iso3166-a2 country (de, us, fr, uk, ...)

Examples:

```
Los Angeles, CA
Mountain View, CA; US
Holzminden; de
```

### Zip Codes

Formats:
```
zip <zipcode>[;iso3166-a2 country code]
<5-digit code>
```
A zip code __with__ keyword but __without__ a country setting OR a 5-digit zip code __without__ keyword will automatically assume that the given zip code is a U.S. zip code. 

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

### numeric coordinates
Format: latitude/longitude (can be positive or negative)

Examples:
```
51.8458575/8.2997425
37.773972/-122.431297
-33.447487/-70.673676
```
Whereas possible, the program will try to turn these coordinates into a human readable address

### Maidenhead / Grid locator
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
Note: When a maidenhead locator is specified, the program will _not_ try to translate this information to a human readable address

### Call sign

Formats:
```
wx <call sign>[-ssid]
wx
<call sign>[-ssid]
```

## Airport data WX inquiries

You have three options:

- specify a specific ICAO code
- specify a specific IATA code
- specify the METAR keyword, which instructs the program to look for the nearest airport. That position can either be based on the user's own call sign or alternatively on a different user's call sign.

If the given airport or the nearest one has been found but does __not__ support METAR data, the program will try to provide you with a standard WX report for the airport's coordinates instead.

### ICAO wx inquiries

Formats:
```
icao <4-character ICAO code>
<4-character ICAO code>
```

Examples:
```
icao eddf
eddf
```

Hint: the non-keyword approach may or may not be successful as it is processed at the end of the parser's process chain.

### IATA wx inquiries

Formats:
```
iata <3-character IATA code>
<3-character IATA code>
```

Examples:
```
iata fra
fra
```
If the IATA keyword is used, it will always return (and use) the respective ICAO code.

Hint: the non-keyword approach may or may not be successful as it is processed at the end of the parser's process chain.

### METAR data

Formats:
```
metar <callsign>[-ssid]
metar
```
If no call sign is specified, then the user's own call sign (the one that he has send us the message with) is used

Examples:
```
metar ko4jvr-9
metar lb7ji
metar 
```

Based on the user's lat/lon, the program will then try to find the nearest airport for you. If that airport supports METAR data, the program is going to return METAR data to the user. Otherwise, it will try to pull a standard wx report for the airport's coordinates.

