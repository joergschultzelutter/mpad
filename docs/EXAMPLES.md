# MPAD example requests and responses

This is a simple collection of sample queries along with their associated responses.

## Weather forecasts

External service dependencies:

- [Openweathermap](www.openweathermap.org) for wx reporting
- [Openstreetmap](www.openstreetmap.org) for coordinate transformation (e.g. City/country or zipcode to lat/lon)
- [aprs.fi](www.aprs.fi) for APRS call sign coordinates

| What do we want | Command string User > MPAD | Response example MPAD > User |
| --------------- | -------------------------- | ---------------------------- |
| localised Wx report for the city of Holzminden, Germany | ```Holzminden;de tomorrow lang de``` | ```16-Jan-21 Holzminden;DE Bedeckt morn:-3c day:-1c eve:-2c nite:-2c``` |
| | | ```sunrise/set 08:21/16:42UTC clouds:89% uvi:0.5 hPa:1026 hum:92%``` |
| | | ```dewpt:-5c wndspd:2m/s wnddeg:252``` |
| WX report for monday for the user's own current position | ```monday``` | ```18-Jan-21 Hoexter;DE rain and snow morn:-1c day:1c eve:2c nite:0c``` |
| | | ```sunrise/set 08:25/16:48UTC rain:1mm snow:2mm clouds:100% uvi:0.3``` |
| | | ```hPa:1017 hum:98% dewpt:1c wndspd:2m/s wnddeg:223``` |
| WX report for monday for another user's position | ```wa1gov-10 monday``` | ```20-Jan-21 Taunton,MA,02718;US overcast clouds morn:-1c day:1c``` |
| | | ```eve:0c nite:-4c sunrise/set 13:06/22:43UTC clouds:100% uvi:0.9```|
| | |```hPa:1010 hum:84% dewpt:-4c wndspd:1m/s wnddeg:280```|
| Wx report for zipcode 94043 |```94043``` | ```17-Jan-21 Mountain View,94043;US clear sky morn:13c day:22c eve:16c```|
| country code is added implicitly for a 5-digit zip - see keyword spec |```zip 94043``` returns same results| ```nite:14c sunrise/set 16:20/02:16UTC clouds:1% uvi:2.6 hPa:1019```|
| | |```hum:27% dewpt:2c wndspd:2m/s wnddeg:353```|
| WX report for zipcode 37603 in Germany |```zip 37603;de``` | ```19-Jan-21 Holzminden,37603;DE moderate rain morn:3c day:4c eve:8c```|
| | |```nite:5c sunrise/set 08:18/16:46UTC rain:13mm clouds:100% uvi:0.3```|
| | |```hPa:1006 hum:90% dewpt:3c wndspd:7m/s wnddeg:217```|
| WX report for Grid JO41du |```grid jo41du``` | ```17-Jan-21 jo41du rain and snow morn:-1c day:0c eve:1c nite:2c```|
| |```mh jo41du``` or ```jo41du``` returns same results | ```sunrise/set 08:25/16:48UTC rain:1mm snow:2mm clouds:100% uvi:0.3```|
| | |```hPa:1018 hum:97% dewpt:-1c wndspd:2m/s wnddeg:153```|
| Wx report for numeric latitude and longitude|```50.1211/8.7938``` | ```19-Jan-21 Offenbach am Main,63075;DE moderate rain morn:2c day:3c```|
| | |```eve:5c nite:3c sunrise/set 08:14/16:56UTC rain:5mm clouds:100%```|
| | |```uvi:0.1 hPa:1014 hum:79% dewpt:0c wndspd:8m/s wnddeg:217```|

## Repeater

External service dependencies:

- [aprs.fi](www.aprs.fi) for APRS call sign coordinates
- [repeatermap.de](www.repeatermap.de) for the repeater database

| What do we want | Command string User > MPAD | Response example MPAD > User |
| --------------- | -------------------------- | ---------------------------- |
| Nearest repeater with C4FM capability | ```repeater c4fm``` | ```Nearest repeater Hoexter 8 km 225 deg SW Rx 430.4125 Tx 439.8125``` |
| | | ```Multimode-Digital-Relais (C4FM und DMR), DMR-ID: 262484 C4FM 70cm``` |
| | | ```JO41QS``` |
| Nearest repeater on 70cm band | ```repeater 70cm``` | ```Nearest repeater Hoexter 8 km 225 deg SW Rx 430.4125 Tx 439.8125``` |
| | | ```Multimode-Digital-Relais (C4FM und DMR), DMR-ID: 262484 C4FM 70cm``` |
| | | ```JO41QS``` |
| Nearest repeater with C4FM capability and on 70cm band | ```repeater c4fm 70cm``` | ```Nearest repeater Hoexter 8 km 225 deg SW Rx 430.4125 Tx 439.8125``` |
| (order of both band and mode are interchangable) | | ```Multimode-Digital-Relais (C4FM und DMR), DMR-ID: 262484 C4FM 70cm``` |
| | | ```JO41QS``` |
| Nearest repeater (disregarding band and mode) | ```repeater``` | ```Nearest repeater Alfeld 18 km 62 deg ENE Rx 145.1125 Tx 145.7125``` |
| | | ```C4FM 2m JO41VX``` |

## Where Is / Where Am I

External service dependencies:

- [Openstreetmap](www.openstreetmap.org) for coordinate transformation (e.g. City/country or zipcode to lat/lon)
- [aprs.fi](www.aprs.fi) for APRS call sign coordinates

| What do we want | Command string User > MPAD | Response example MPAD > User |
| --------------- | -------------------------- | ---------------------------- |
| My own position data | ```whereami``` | ```Pos for DF1JSL-1 Grid JO41su94 DMS N51.51'13.2, E09.34'37.8 Alt 237m``` |
| | | ```UTM 32U 539752 5744921 MGRS 32UNC3975244921 LatLon 51.85367/9.57717``` |
| | | ```Schorborn, 37627, DE Alte Muehle``` |
| DF1JSL-8's position | ``` whereis df1jsl-8 ```| ```Pos DF1JSL-8 Grid JO41st76 DMS N51.49'0.0/E09.33'57.0 Dst 85 km``` |
| | | ```Brg 272deg W Alt 366m UTM 32U 539003 5740799 MGRS 32UNC3900340799``` |
| | | ```LatLon 51.81667/9.56583 Merxhausen, 37627, DE Neuhaeuser Strasse```|
| | |```Last heard 2021-01-23 17:32:42``` |

## METAR data

External service dependencies:

- [Aviation Weather](www.aviationweather.gov) for coordinate transformation (e.g. City/country or zipcode to lat/lon) and  METAR report data
- [aprs.fi](www.aprs.fi) for APRS call sign coordinates

METAR reports always return the latest wx data to the user. So METAR data cannot be requested for a specific day (corresponding keywords are ignored).


| What do we want | Command string User > MPAD | Response example MPAD > User |
| --------------- | -------------------------- | ---------------------------- |
| METAR data of a METAR-enabled airport, related to the user's position | ```metar``` | |
| METAR data of a METAR-enabled airport, related to another user's position | ```metar wa1gov-10``` | ```KTAN 171752Z AUTO 25013G27KT 10SM BKN055 07/M05 A2945 RMK AO2 PK``` |
| | | ```WND 22027/1747 SLP971 T00721050 10083 20022 56007``` |
| METAR data for ICAO code EDDF | ```icao eddf``` | ```EDDF 171750Z 22004KT 5000 BR BKN004 OVC011 00/M01 Q1022 R25C/290095``` |
| | | ```R25L/290095 R18/290095 TEMPO SCT004``` |
| METAR data for IATA code FRA | ```iata fra``` | ```EDDF 171750Z 22004KT 5000 BR BKN004 OVC011 00/M01 Q1022 R25C/290095``` |
| | | ```R25L/290095 R18/290095 TEMPO SCT004``` |

## CWOP data

External service dependencies:

- [aprs.fi](www.aprs.fi) for APRS call sign coordinates
- [findu.com](www.findu.com) for the CWOP data

METAR reports always return the latest wx data to the user. So METAR data cannot be requested for a specific day (corresponding keywords are ignored).

| What do we want | Command string User > MPAD | Response example MPAD > User |
| --------------- | -------------------------- | ---------------------------- |
| CWOP report, related to the user's position | ```cwop``` | ```CWOP AT166 17-Jan-21 0C Spd 0.0km/h Gust 1.6km/h Hum 94%``` |
| | | ```Pres 1017.9mb Rain(cm) 1h=0.03, 24h=0.10, mn=0.10``` |
| CWOP report, related to another user's position | ```cwop wa1gov-10``` | ```CWOP FW8220 17-Jan-21 6C 332deg Spd 8.0km/h Gust 32.2km/h Hum 52%``` |
| | | ```Pres 997.4mb Rain(cm) 1h=0.0, 24h=0.0, mn=0.0``` |
| CWOP report for a specific CWOP station ID | ```cwop dl6mm-4``` | ```CWOP DL6MM-4 17-Jan-21 0C 0deg Spd 0.0km/h Gust 0.0km/h Hum 91%``` |
| | | ```Pres 1018.1mb Rain(cm) 1h=0.0, 24h=0.0, mn=0.0``` |

## Sunrise/Sunset and Moonset/Moonrise

External service dependencies:

- [aprs.fi](www.aprs.fi) for APRS call sign coordinates

The very first usage of this command set will trigger a download of the ```de421.bsp``` ephemeris data file which will take a few seconds to complete. Once that download has been completed, all future attempts to calculate these celestial attempts will use that previously downloaded data file.

| What do we want | Command string User > MPAD | Response example MPAD > User |
| --------------- | -------------------------- | ---------------------------- |
| Sunrise/set and moonset/rise, relative to the user's position | ```riseset``` | ```RiseSet DF1JSL-4 17-Jan GMT sun_rs 07:25-15:49 mn_sr 20:47-09:55``` |
| Sunrise/set and moonset/rise, relative to another user's position | ```riseset wa1gov-10``` | ```RiseSet WA1GOV-10 17-Jan GMT sun_rs 12:08-21:40 mn_sr 01:26-15:03``` |
| Sunrise/set and moonset/rise, relative to another user's position and a specific day| ```riseset wa1gov-10 friday``` | ```RiseSet WA1GOV-10 22-Jan GMT sun_rs 12:04-21:46 mn_sr 06:31-17:00``` |

## OpenStreetMap Category 'Near' search

External service dependencies:

- [Openstreetmap](www.openstreetmap.org) for coordinate transformation (e.g. City/country or zipcode to lat/lon)
- [aprs.fi](www.aprs.fi) for APRS call sign coordinates

| What do we want | Command string User > MPAD | Response example MPAD > User |
| --------------- | -------------------------- | ---------------------------- |
| Nearest Supermarket to my location | ```osm supermarket``` | ```Nahkauf Eversteiner Straße 17 Lobach Dst 6 km Brg 332 deg NNW``` |
| Top3 of the nearest supermarkets to my location | ```osm supermarket top3``` | ```#1 Nahkauf Eversteiner Straße 17 Lobach Dst 6 km Brg 332 deg NNW #2``` |
| | | ```REWE Bevern Schloss 15 Bevern Dst 7 km Brg 313 deg NW #3 Aldi``` |
| | | ```Deenser Straße 26 Stadtoldendorf Dst 8 km Brg 26 deg NNE``` |
| Nearest police to my location (non-keyword search) | ```police``` | ```Polizei Stadtoldendorf Amtsstraße 4 Stadtoldendorf Dst 8 km``` |
| | | ```Brg 29 deg NNE``` |

## Send message to DAPNET user

External service dependencies:

- [DAPNET API](https://hampager.de/)

| What do we want | Command string User > MPAD | Response example MPAD > User |
| --------------- | -------------------------- | ---------------------------- |
| Send message ```Hello World``` to user ```DF1JSL``` | ```dapnet df1jsl Hello World``` | ```Successfully sent DAPNET message to DF1JSL``` |
