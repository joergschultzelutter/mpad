# Third Party Dependencies

## Python Library Dependencies

All dependencies are included in [requirements.txt](../requirements.txt). Install via ```pip install -r requirements.txt```

If you install MPAD and its components on a Raspberry Pi, the skyfield package requires you to install ```apt-get install libatlas-base-dev``` as a separate dependency.

Dependent on your OS' flavor, you may be required to install the following additional packages: ```apt-get install libgeos-dev libopenjp2-7```

## API Dependencies

- [aprs.fi](https://aprs.fi/page/api) - thank you Hessu!
- [aprs-is](http://www.aprs-is.net/Default.aspx) - thank you Steve Loveall!
- [findu.com](https://www.findu.com) - thank you Steve Dimse!
- [met.no](https://developer.yr.no/featured-products/forecast/) - thank you Meterologisk institutt!

aprs.fi requires an API access key which needs to be added to the program's configuration file - see [installation instructions](INSTALLATION.md)

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
