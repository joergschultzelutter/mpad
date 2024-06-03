# MPAD example requests and responses

This is a simple collection of sample queries along with their associated responses.

## Weather forecasts

External service dependencies:

- [Openweathermap](www.openweathermap.org) for wx reporting
- [Openstreetmap](www.openstreetmap.org) for coordinate transformation (e.g. City/country or zipcode to lat/lon)
- [aprs.fi](www.aprs.fi) for APRS call sign coordinates

| What do we want                                           | Command string User > MPAD                           | Response example MPAD > User                                              |
|-----------------------------------------------------------|------------------------------------------------------|---------------------------------------------------------------------------|
| WX report for monday for the user's own current position  | ```monday```                                         | ```18-Jan-21 Hoexter;DE HeavySnow Nite:0c Morn:-1c Day:1c```              |
|                                                           |                                                      | ```Eve:2c avghum:87% snow:20mm wind:3-6m/s NW-NNW cld:100% prs:1017hPa``` |
| WX report for monday for another user's position          | ```wa1gov-10 monday```                               | ```20-Jan-21 Taunton,MA,02718;US Cloudy Nite:-4c Morn:-1c Day:1c```       |
|                                                           |                                                      | ```Eve:0c cld:100% uvi:0.9 wind:3-6m/s NW-NNW hPa:1012```                 |
| Wx report for zipcode 94043, issued by a non/US call sign | ```94043```                                          | ```17-Jan-21 Mountain View,94043;US ClearSky Nite:14c Morn:13c Day:22c``` |
| U.S. country code is added implicitly for a 5-digit zip   | ```zip 94043``` returns same results                 | ```Eve:16c cld:1% uvi:2.6 wind:5-7m/s SW-N hPa:1019```                    |
| WX report for zipcode 37603 in Germany                    | ```zip 37603;de```                                   | ```19-Jan-21 Holzminden,37603;DE LightRain Nite:5c Morn:3c Day:4c```      |
|                                                           | same as ```37603;de```                               | ```Eve:8c rain:13mm cld:100% uvi:0.3 wind:5-7m/s SW-N hPa:1006```         |
| WX report for Grid JO41du                                 | ```grid jo41du```                                    | ```17-Jan-21 jo41du HeavySnow Nite:2c Morn:-1c Day:0c Eve:1c ```          |
|                                                           | ```mh jo41du``` or ```jo41du``` returns same results | ```snow:35mm cld:100% uvi:0.3 wind:3-6m/s NW-NNW hPa:1006```              |
| Wx report for numeric latitude and longitude              | ```50.1211/8.7938```                                 | ```19-Jan-21 Offenbach am Main,63075;DE ModerateRain Nite:3c Morn:2c```   |
|                                                           |                                                      | ```Day:3c Eve:5c rain:5mm cld:100% uvi:0.1 wind:3-6m/s NW-NNW hPa:1014``` |
| WX report in 47h for zipcode 37627 in Germany             | ```zip 37603;de 47h```                               | ```15-Feb-21 in 47h Stadtoldendorf,37627;DE Cloudy -2c```                 |
|                                                           |                                                      | ```cld:100% uvi:0.5 wind:3-6m/s NW-NNW hPa:1014```                        |
| WX report for Moab,UT using forced imperial format        | ```moab,ut;us imperial```                            | ```today Moab,UT ClearSky Morn:76F Day:85F Eve:90F avghum:13% uvi:9.1```  |
|                                                           |                                                      | ```wind:4-9mph SSE-NNW cld:25% hPa:1008-1015```                           |

## Repeater

External service dependencies:

- [aprs.fi](www.aprs.fi) for APRS call sign coordinates
- [repeatermap.de](www.repeatermap.de) and [hearham.com](www.hearham.com) for the repeater databases

| What do we want                                        | Command string User > MPAD | Response example MPAD > User                                            |
|--------------------------------------------------------|----------------------------|-------------------------------------------------------------------------|
| Nearest repeater with C4FM capability                  | ```repeater c4fm```        | ```Nearest repeater Hoexter 8 km 225 deg SW Rx 430.4125 Tx 439.8125```  |
|                                                        |                            | ```Multimode-Digital-Relais (C4FM und DMR), DMR-ID: 262484 C4FM 70cm``` |
|                                                        |                            | ```JO41QS```                                                            |
| Nearest repeater on 70cm band                          | ```repeater 70cm```        | ```Nearest repeater Hoexter 8 km 225 deg SW Rx 430.4125 Tx 439.8125```  |
|                                                        |                            | ```Multimode-Digital-Relais (C4FM und DMR), DMR-ID: 262484 C4FM 70cm``` |
|                                                        |                            | ```JO41QS```                                                            |
| Nearest repeater with C4FM capability and on 70cm band | ```repeater c4fm 70cm```   | ```Nearest repeater Hoexter 8 km 225 deg SW Rx 430.4125 Tx 439.8125```  |
| (order of both band and mode are interchangable)       |                            | ```Multimode-Digital-Relais (C4FM und DMR), DMR-ID: 262484 C4FM 70cm``` |
|                                                        |                            | ```JO41QS```                                                            |
| Nearest repeater (disregarding band and mode)          | ```repeater```             | ```Nearest repeater Alfeld 18 km 62 deg ENE Rx 145.1125 Tx 145.7125```  |
|                                                        |                            | ```C4FM 2m JO41VX```                                                    |

## Where Is / Where Am I

External service dependencies:

- [Openstreetmap](www.openstreetmap.org) for coordinate transformation (e.g. City/country or zipcode to lat/lon)
- [aprs.fi](www.aprs.fi) for APRS call sign coordinates

| What do we want      | Command string User > MPAD | Response example MPAD > User                                               |
|----------------------|----------------------------|----------------------------------------------------------------------------|
| My own position data | ```whereami```             | ```Pos for DF1JSL-1 Grid JO41su94 DMS N51.51'13.2, E09.34'37.8 Alt 237m``` |
|                      |                            | ```UTM 32U 539752 5744921 MGRS 32UNC3975244921 LatLon 51.85367/9.57717```  |
|                      |                            | ```Schorborn, 37627, DE Alte Muehle```                                     |
| DF1JSL-8's position  | ``` whereis df1jsl-8 ```   | ```Pos DF1JSL-8 Grid JO41st76 DMS N51.49'0.0/E09.33'57.0 Dst 85 km```      |
|                      |                            | ```Brg 272deg W Alt 366m UTM 32U 539003 5740799 MGRS 32UNC3900340799```    |
|                      |                            | ```LatLon 51.81667/9.56583 Merxhausen, 37627, DE Neuhaeuser Strasse```     |
|                      |                            | ```Last heard 2021-01-23 17:32:42```                                       |

## METAR / TAF data

External service dependencies:

- [Aviation Weather](www.aviationweather.gov) for coordinate transformation (airport code to lat/lon) and  METAR/TAF data
- [aprs.fi](www.aprs.fi) for APRS call sign coordinates

| What do we want                                                                 | Command string User > MPAD             | Response example MPAD > User                                               |
|---------------------------------------------------------------------------------|----------------------------------------|----------------------------------------------------------------------------|
| METAR data of a METAR-enabled airport, related to the user's position           | ```metar```                            | ```EDDF 171150Z 02008KT 340V050 5000 -SHSNRA FEW004 SCT011CB BKN019```     |
|                                                                                 |                                        | ```03/01 Q1023 NOSIG```                                                    |
| TAF data of a METAR-enabled airport, related to the user's position             | ```taf```                              | ```TAF EDDF 171100Z 1712/1818 02008KT 9999 BKN030 TEMPO 1712/1716```       |
|                                                                                 |                                        | ```SHRAGS BKN020TCU BECMG 1717/1720 FEW030 BECMG 1800/1802 02002KT ```     |
|                                                                                 |                                        | ```BECMG 1806/1809 30005KT TEMPO 1811/1818 SHRAGS BKN020TCU SCT030```      |
| METAR _and_ TAF data of a METAR-enabled airport, related to the user's position | ```metar full``` __or__ ```taf full``` | ```EDDF 171150Z 02008KT 340V050 5000 -SHSNRA FEW004 SCT011CB BKN019```     |
|                                                                                 |                                        | ```03/01 Q1023 NOSIG ## TAF EDDF 171100Z 1712/1818 02008KT 9999```         |
|                                                                                 |                                        | ```BKN030 TEMPO 1712/1716 SHRAGS BKN020TCU BECMG 1717/1720 FEW030```       |
|                                                                                 |                                        | ```BECMG 1800/1802 02002KT BECMG 1806/1809 30005KT TEMPO 1811/1818```      |
|                                                                                 |                                        | ```SHRAGS BKN020TCU SCT030```                                              |
| METAR data of a METAR-enabled airport, related to another user's position       | ```metar wa1gov-10```                  | similar output to 1st example; add ```full``` keyword for METAR & TAF data |
| METAR data for ICAO code EDDF                                                   | ```icao eddf``` or ```eddf```          | similar output to 1st example; add ```full``` keyword for METAR & TAF data |
| METAR data for IATA code FRA                                                    | ```iata fra``` or ```fra```            | similar output to 1st example; add ```full``` keyword for METAR & TAF data |

IATA codes are taken from [https://www.aviationweather.gov/docs/metar/stations.txt](https://www.aviationweather.gov/docs/metar/stations.txt). This file does not contain several international IATA codes. If your IATA code does not work, use an ICAO code.

In case you use either the ```metar``` or the ```taf``` keyword in combination with the ```full``` keyword, `For better legibility,```mpad``` will separate METAR and TAF data by a ## sequence - see example.

## CWOP data

External service dependencies:

- [aprs.fi](www.aprs.fi) for APRS call sign coordinates
- [findu.com](www.findu.com) for the CWOP data

CWOP reports always return the latest wx data to the user. Any date / time specifications specified by the user will be ignored.

| What do we want                                 | Command string User > MPAD | Response example MPAD > User                                            |
|-------------------------------------------------|----------------------------|-------------------------------------------------------------------------|
| CWOP report, related to the user's position     | ```cwop```                 | ```CWOP AT166 17-Jan-21 0C Spd 0.0km/h Gust 1.6km/h Hum 94%```          |
|                                                 |                            | ```Pres 1017.9mb Rain(cm) 1h=0.03, 24h=0.10, mn=0.10```                 |
| CWOP report, related to another user's position | ```cwop wa1gov-10```       | ```CWOP FW8220 17-Jan-21 6C 332deg Spd 8.0km/h Gust 32.2km/h Hum 52%``` |
|                                                 |                            | ```Pres 997.4mb Rain(cm) 1h=0.0, 24h=0.0, mn=0.0```                     |
| CWOP report for a specific CWOP station ID      | ```cwop dl6mm-4```         | ```CWOP DL6MM-4 17-Jan-21 0C 0deg Spd 0.0km/h Gust 0.0km/h Hum 91%```   |
|                                                 |                            | ```Pres 1018.1mb Rain(cm) 1h=0.0, 24h=0.0, mn=0.0```                    |

## Sunrise/Sunset and Moonset/Moonrise

External service dependencies:

- [aprs.fi](www.aprs.fi) for APRS call sign coordinates

The very first usage of this command set will trigger a download of the ```de421.bsp``` ephemeris data file which will take a few seconds to complete. Once that download has been completed, all future attempts to calculate these celestial attempts will use that previously downloaded data file.

| What do we want                                                                      | Command string User > MPAD     | Response example MPAD > User                                            |
|--------------------------------------------------------------------------------------|--------------------------------|-------------------------------------------------------------------------|
| Sunrise/set and moonset/rise, relative to the user's position                        | ```riseset```                  | ```RiseSet DF1JSL-4 17-Jan GMT sun_rs 07:25-15:49 mn_sr 20:47-09:55```  |
| Sunrise/set and moonset/rise, relative to another user's position                    | ```riseset wa1gov-10```        | ```RiseSet WA1GOV-10 17-Jan GMT sun_rs 12:08-21:40 mn_sr 01:26-15:03``` |
| Sunrise/set and moonset/rise, relative to another user's position and a specific day | ```riseset wa1gov-10 friday``` | ```RiseSet WA1GOV-10 22-Jan GMT sun_rs 12:04-21:46 mn_sr 06:31-17:00``` |

## OpenStreetMap Category 'Near' search

External service dependencies:

- [Openstreetmap](www.openstreetmap.org) for coordinate transformation (e.g. City/country or zipcode to lat/lon)
- [aprs.fi](www.aprs.fi) for APRS call sign coordinates

| What do we want                                    | Command string User > MPAD | Response example MPAD > User                                              |
|----------------------------------------------------|----------------------------|---------------------------------------------------------------------------|
| Nearest Supermarket to my location                 | ```osm supermarket```      | ```Nahkauf Eversteiner Straße 17 Lobach Dst 6 km Brg 332 deg NNW```       |
| Top3 of the nearest supermarkets to my location    | ```osm supermarket top3``` | ```#1 Nahkauf Eversteiner Straße 17 Lobach Dst 6 km Brg 332 deg NNW #2``` |
|                                                    |                            | ```REWE Bevern Schloss 15 Bevern Dst 7 km Brg 313 deg NW #3 Aldi```       |
|                                                    |                            | ```Deenser Straße 26 Stadtoldendorf Dst 8 km Brg 26 deg NNE```            |
| Nearest police to my location (non-keyword search) | ```police```               | ```Polizei Stadtoldendorf Amtsstraße 4 Stadtoldendorf Dst 8 km```         |
|                                                    |                            | ```Brg 29 deg NNE```                                                      |

Keyword-less variants may or may not work, so ```osm supermarket``` and ```supermarket``` should return the same values. However, ambiguous (shorter) search terms might get misinterpreted as earlier parser processes might mistake them for something else. Example: ```osm pub``` will give you the direction to the nearest pub whereas ```pub``` will return METAR data for an airport location in Pueblo, CO (whose IATA code is -as you might have guessed- PUB). 

## Send message to DAPNET user

External service dependencies:

- [DAPNET API](https://hampager.de/)

| What do we want                                                            | Command string User > MPAD                | Response example MPAD > User                                   |
|----------------------------------------------------------------------------|-------------------------------------------|----------------------------------------------------------------|
| Send message ```Hello World``` to user ```DF1JSL```                        | ```dapnet df1jsl Hello World```           | ```DAPNET message dispatch to 'DF1JSL' via 'all' successful``` |
| Send high priority message ```Emergency, need help``` to user ```DF1JSL``` | ```dapnethp df1jsl mergency, need help``` | ```DAPNET message dispatch to 'DF1JSL' via 'all' successful``` |

MPAD's response message indicates which transmitter group was used for sending the message to the user (previous example: "all")

## Fortune Teller

External service dependencies:

- Fortuna :-)

| What do we want                 | Command string User > MPAD                                      | Response example MPAD > User |
|---------------------------------|-----------------------------------------------------------------|------------------------------|
| Our fortune in English language | ```fortuneteller```, ```magic8ball```,```magic8``` or ```m8b``` | ```Outlook good```           |
| Our fortune in Russian language | ```fortuneteller lang ru```                                     | ```Знаки говорят — да```     |

In case you ever wonder about whether you should buy that new transceiver with the super expensive price tag: the answer is always ```Without a doubt```. ALWAYS.

The main purpose of this keyword is testing both UTF-8 and ```lang``` keyword tests. Apart from that, it's fun :-)
Note that outgoing UTF-8 content will be converted to plain ASCII content unless specified otherwise in the program's config file (see [installation instructions](INSTALLATION.md)).

## Satellite pass data

External service dependencies:

- [Celestrak](https://www.celestrak.com/)

| What do we want                   | Command string User > MPAD | Response example MPAD > User                                              |
|-----------------------------------|----------------------------|---------------------------------------------------------------------------|
| Get next ISS pass                 | ```satpass iss```          | ```ISS pass for DF1JSL-8 UTC Rise 10-Mar 23:09 Culm 23:12 Set 23:15```    |
|                                   |                            | ```Alt 10 deg Az 154 deg Dst 677km Vis N```                               |
| Get next visible ISS pass         | ```vispass iss```          | ```ISS vis pass for DF1JSL-8 UTC Rise 11-Mar 03:59 Culm 04:02```          |
|                                   |                            | ```Set 04:05 Alt 10 deg Az 213 deg Dst 876km```                           |
| Get top2 of next visible ISS pass | ```vispass iss top2```     | ```ISS vis passes for DF1JSL-8 UTC #1 Rise 11-Mar 03:59 Culm 04:02```     |
|                                   |                            | ```Set 04:05 Alt 10 deg Az 213 deg Dst 876km #2 R 12-Mar 03:11 C 03:14``` |
|                                   |                            | ```S 03:17 Alt 10 Az 208 Dst 701```                                       |

If you request more than one result (via the ```top2```...```top5``` commands), MPAD will abbreviate the descriptive text for results 2..5 in order to save a few bytes per message. The format for messages 2..5 is the same as for the first message which comes with a full descriptive text.

Description:

- ```Rise``` / ```R```: Rise time, event start time
- ```Culm``` / ```C```: Culmination time, mid-time of the event
- ```Set``` / ```S```: Set time, event end time
- ```Alt```: Altitude in degrees at culmination time
- ```Az```: Azimuth in degrees at culmination time
- ```Dst```: Distance in km or miles at culmination time
- ```Vis```: Visibility Y/N. Only included if your query is based on ```satpass```.

## Satellite frequency data

External service dependencies:

- [JE9PEL's satellite data](http://www.ne.jp/asahi/hamradio/je9pel/satslist.htm)
- [Celestrak](https://www.celestrak.com/)

| What do we want                     | Command string User > MPAD | Response example MPAD > User                                             |
|-------------------------------------|----------------------------|--------------------------------------------------------------------------|
| Get Es'Hail-2 satellite frequencies | ```satfreq es'hail-2```    | ```'ES'HAIL-2' Freq: #1 Uplink 2400.050-2400.300```                      |
|                                     |                            | ```Downlink 10489.550-10489.800 Mode Linear  transponder #2```           |
|                                     |                            | ```Up 2401.500-2409.500 Dn 10491.000-10499.000 Md Digital transponder``` |

Note that the requested satellite in question MUST exist in [Celestrak's Amateur Radio Satellite](http://www.celestrak.com/NORAD/elements/amateur.txt) list. Satellites which do not exist in the Celestrak data but in JE9PEL's data will not be taken into consideration.

If the requested satellite has more than one uplink/downlink frequency tupel, MPAD will abbreviate the descriptive text for results 2..n in order to save a few bytes per message. The format for messages 2..n is the same as for the first message which comes with a full descriptive text.

Description:

- ```Uplink``` / ```Up```: Satellite uplink frequency
- ```Downlink``` / ```Dn```: Satellite Downlink frequency
- ```Beacon``` / ```Bcn```: Beacon frequency
- ```Mode``` / ```Md```: Mode, e.g. SSTV

## Email position reports

External service dependencies:

- [aprs.fi](www.aprs.fi) for APRS call sign coordinates
- [Openstreetmap](www.openstreetmap.org) for coordinate transformation (e.g. lat/lon to City/country or zipcode)

Have MPAD send an email with your APRS position data to any user on the Internet.

| What do we want                                                                 | Command string User > MPAD             | Response example MPAD > User                                     |
|---------------------------------------------------------------------------------|----------------------------------------|------------------------------------------------------------------|
| Send a position report to user test123@gmail.com                                | ```posmsg test123@gmail.com```         | ```The requested position report was emailed to its recipient``` |
| Send a position report to user test123@gmail.com and enforce language 'Russian' | ```posmsg test123@gmail.com lang ru``` | ```The requested position report was emailed to its recipient``` |

Default language is English - you can specify a different language via ```language``` keyword. MPAD always sends this parameter to OpenStreetmap, thus allowing you to receive e.g. Russian addresses in cyrillic characters.

Note that specifying your own message content (as part of the outgoing mail) is not implemented - I sacrificed this option in favor of longer email addresses.

## Radiosonde landing predictions

External service dependencies:

- [aprs.fi](www.aprs.fi) for APRS call sign coordinates
- [Habhub](habhub.org) for the radiosonde landing prediction

Based on the probe's coordinates on APRS.fi, calculate the probe's landing coordinates and return them to the user

| What do we want                                    | Command string User > MPAD | Response example MPAD > User                                           |
|----------------------------------------------------|----------------------------|------------------------------------------------------------------------|
| Get the radiosonde's predicted landing coordinates | ```sonde s3421116```       | ```Landing Pred. 'S3421116' Lat/Lon 47.7853/10.6331 02-Apr 15:45UTC``` |
|                                                    |                            | ```Dst 481 km Brg 159deg SSE Grid JN57hs58 Addr: Baerenleitenweg,```   |
|                                                    |                            | ```Marktoberdorf, Landkreis Ostallgaeu, Bavaria, 87616, Germany```     |
