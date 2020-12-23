# mpad - Usage and Command Syntax
## WX data inquiries

- One or multiple spaces between the respective separators are permitted
- Commands and keywords are case insensitive

### City, State and/or Country
Formats: 
```
<city>, <state>; <country>
<city>, <state>
<city>; <country>
```

Country = iso3166-a2 country

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

Note: When a maidenhead locator is specified, the program will not try to translate this information to a human readable address







