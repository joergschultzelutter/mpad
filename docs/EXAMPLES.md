# Example requests

This is a mere collection of example requests along with their associated responses.

## Weather forecasts

| What do we want | Command string User > MPAD | Response example MPAD > User |
| --------------- | -------------------------- | ---------------------------- |
| localised Wx report for the city of Holzminden, Germany | ```Holzminden;de tomorrow lang de``` | ```16-Jan-21 Holzminden;DE Bedeckt morn:-3c day:-1c eve:-2c nite:-2c``` |
| | | ```sunrise/set 08:21/16:42UTC clouds:89% uvi:0.5 hPa:1026 hum:92%``` |
| | | ```dewpt:-5c wndspd:2m/s wnddeg:252``` |
| WX report for monday for the user's own current position | ```monday``` | ```18-Jan-21 DF1JSL-1 rain and snow morn:-1c day:1c eve:2c nite:0c``` |
| | | ```sunrise/set 08:25/16:48UTC rain:1mm snow:2mm clouds:100% uvi:0.3``` |
| | | ```hPa:1017 hum:98% dewpt:1c wndspd:2m/s wnddeg:223``` |

## Repeater

| What do we want | Command string User > MPAD | Response example MPAD > User |
| --------------- | -------------------------- | ---------------------------- |
| Nearest repeater with C4FM capability | ```repeater c4fm``` | ```Nearest repeater Hoexter 8 km 225 deg SW Rx 430.4125 Tx 439.8125``` |
| | | ```Multimode-Digital-Relais (C4FM und DMR), DMR-ID: 262484 C4FM 70cm``` |
| | | ```JO41QS``` |
| Nearest repeater with C4FM capability and on 70cm band | ```repeater c4fm 70cm``` | ```Nearest repeater Hoexter 8 km 225 deg SW Rx 430.4125 Tx 439.8125``` |
| (order of both band and mode are interchangable) | | ```Multimode-Digital-Relais (C4FM und DMR), DMR-ID: 262484 C4FM 70cm``` |
| | | ```JO41QS``` |
| Nearest repeater (disregarding band and mode) | ```repeater``` | ```Nearest repeater Alfeld 18 km 62 deg ENE Rx 145.1125 Tx 145.7125``` |
| | | ```C4FM 2m JO41VX``` |

## Where Is / Where Am I

| What do we want | Command string User > MPAD | Response example MPAD > User |
| --------------- | -------------------------- | ---------------------------- |
| My own position data | ```whereami``` | ```Pos for DF1JSL-1 Grid:JO41su94 DMS N51.51'13, E09.34'38 Alt 237m``` |
| | | ```UTM:32U 539752 5744921 MGRS:32UNC3975244921 LatLon:51.85367/9.57717``` |
| | | ```Schorborn, 37627, DE Alte Muehle``` |
| WA1GOV-10's position | ``` whereis wa1gov-10 ```| ```Pos WA1GOV-10 Grid:FN41lu95 DMS N41.51'17, W71.00'24 Dst 5862 km``` |
| | | ```Brg 50deg NE UTM:19T 333431 4635605 MGRS:19TCG3343135605``` |
| | | ```LatLon:41.85483/-71.00667 Taunton, 02718, US Seekell Street 329``` |

## METAR data

METAR wx reports always return the latest wx data to the user, meaning that you cannot request METAR data for a specific day (such keywords will be ignored)

| What do we want | Command string User > MPAD | Response example MPAD > User |
| --------------- | -------------------------- | ---------------------------- |
| METAR data of a METAR-capable airport, relative to the user's position | ```metar``` | |
| METAR data of a METAR-capable airport, relative to another user's position | ```metar wa1gov-10``` | ```KTAN 171752Z AUTO 25013G27KT 10SM BKN055 07/M05 A2945 RMK AO2 PK``` |
| | | ```WND 22027/1747 SLP971 T00721050 10083 20022 56007``` |
| METAR data for ICAO code EDDF | ```icao eddf``` | ```EDDF 171750Z 22004KT 5000 BR BKN004 OVC011 00/M01 Q1022 R25C/290095``` |
| | | ```R25L/290095 R18/290095 TEMPO SCT004``` |
| METAR data for IATA code FRA | ```iata fra``` | ```EDDF 171750Z 22004KT 5000 BR BKN004 OVC011 00/M01 Q1022 R25C/290095``` |
| | | ```R25L/290095 R18/290095 TEMPO SCT004``` |

## CWOP data

CWOP reports always return the latest wx data to the user, meaning that you cannot request CWOP data for a specific day (such keywords will be ignored)

| What do we want | Command string User > MPAD | Response example MPAD > User |
| --------------- | -------------------------- | ---------------------------- |
| CWOP report, relative to the user's position | ```cwop``` | ```CWOP AT166 17-Jan-21 0C Spd 0.0km/h Gust 1.6km/h Hum 94%``` |
| | | ```Pres 1017.9mb Rain(cm) 1h=0.03, 24h=0.10, mn=0.10``` |
| CWOP report, relative to another user's position | ```cwop wa1gov-10``` | ```CWOP FW8220 17-Jan-21 6C 332deg Spd 8.0km/h Gust 32.2km/h Hum 52%``` |
| | | ```Pres 997.4mb Rain(cm) 1h=0.0, 24h=0.0, mn=0.0``` |
| CWOP report for a specific station | ```cwop dl6mm-4``` | ```CWOP DL6MM-4 17-Jan-21 0C 0deg Spd 0.0km/h Gust 0.0km/h Hum 91%``` |
| | | ```Pres 1018.1mb Rain(cm) 1h=0.0, 24h=0.0, mn=0.0``` |

## Sunrise/Sunset and Moonset/Moonrise

| What do we want | Command string User > MPAD | Response example MPAD > User |
| --------------- | -------------------------- | ---------------------------- |
| Sunrise/set and moonset/rise, relative to the user's position | ```riseset``` | ```RiseSet DF1JSL-4 17-Jan GMT sun_rs 07:25-15:49 mn_sr 20:47-09:55``` |
| Sunrise/set and moonset/rise, relative to another user's position | ```riseset wa1gov-10``` | ```RiseSet WA1GOV-10 17-Jan GMT sun_rs 12:08-21:40 mn_sr 01:26-15:03``` |
| Sunrise/set and moonset/rise, relative to another user's position and a specific day| ```riseset wa1gov-10 friday``` | ```RiseSet WA1GOV-10 22-Jan GMT sun_rs 12:04-21:46 mn_sr 06:31-17:00``` |
