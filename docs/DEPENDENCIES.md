# Third Party Dependencies

## Python Library Dependencies

The following Python packages need to be installed (see also [requirements.txt](../requirements.txt):

- [activesoup](https://github.com/jelford/activesoup) required: version 0.3.0 or greater
- [apscheduler](https://github.com/agronholm/apscheduler)
- [aprslib](https://github.com/rossengeorgiev/aprs-python)
- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/)
- [expiringdict](https://pypi.org/project/expiringdict/)
- [geopy](https://github.com/geopy/geopy)
- [iso3166](https://github.com/deactivated/python-iso3166)
- [maidenhead](https://github.com/space-physics/maidenhead)
- [pymgrs](https://github.com/aydink/pymgrs) Note: this is __not__ a pip package; download the mgrs.py file and save it in the src directory
- [requests](https://github.com/psf/requests)
- [skyfield](https://github.com/skyfielders/python-skyfield)
- [timezonefinder](https://github.com/MrMinimal64/timezonefinder)
- [unidecode](https://github.com/avian2/unidecode)
- [us](https://github.com/unitedstates/python-us)
- [utm](https://github.com/Turbo87/utm)
- [xmltodict](https://github.com/martinblech/xmltodict)

If you install MPAD and its components on a Raspberry Pi, the skyfield package requires you to install ```apt-get install libatlas-base-dev``` as a separate dependency.

## API Dependencies

- [aprs.fi](https://aprs.fi/page/api) - thank you Hessu!
- [aprs-is](http://www.aprs-is.net/Default.aspx) - thank you Steve Loveall!
- [findu.com](https://www.findu.com) - thank you Steve Dimse!
- [openweathermap.org](https://www.openweathermap.org)

Both aprs.fi and openweathermap.org require an API access key which needs to be added to the program's configuration file - see [installation instructions](INSTALLATION.md)

## Additional external data dependencies

- [aviationweather.gov](https://www.aviationweather.gov)
- [celestrak.com](https://www.celestrak.com)
- [habhub.org](habhub.org)
- [hearham.com](https://www.hearham.com)
- [JE9PEL's satellite frequency data](http://www.ne.jp/asahi/hamradio/je9pel/satslist.htm)
- [openstreetmap.org](https://www.openstreetmap.org)
- [repeatermap.de](https://www.repeatermap.de)

## Programming & knowledge resources

- [aprs101](http://www.aprs.org/doc/APRS101.PDF)
- [wxbot](https://sites.google.com/site/ki6wjp/wxbot)
