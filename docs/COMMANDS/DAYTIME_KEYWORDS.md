# Daytime settings

MPAD is able to understand the following keywords:

- ```full```. Returns all data for the given day (__program default__). Note that ```full``` can refer to time frames or the amount of data that is returned by the program (dependent on the [action keyword](ACTION_KEYWORDS.md))

- Morning (Keywords: ```morn```, ```morning```)

- Daytime (Keywords: ```day```, ```daytime```, ```noon```)

- Evening (Keywords: ```eve```, ```evening```)

- Night (Keywords: ```nite```, ```night```, ```tonite```, ```tonight```). 
- 
```tonite``` and ```tonight``` keywords will set the ```date``` keyword to ```today``` unless the user has already specified a different day.

MPAD 0.60 or later:
- WX reports: all references are in the user's local time zone (based on the coordinates associated with the user's call sign or the given reference such e.g. a city name)
    - Night: 00:00 / 12AM local time
    - Morning: 06:00 / 6AM local time
    - Daytime: 12:00 / 12PM local time
    - Evening: 10:00 / 6PM local time
    - Note that this is also the order in which e.g. wx data is pulled. A day always starts with the "Night" and ends with the "Evening" values.
- Everything else: unless noted differently, all other time references are in UTC

Whereas noted for the respective [action keyword](ACTION_KEYWORDS.md), these daytime setting keywords (and also the [date](DATE_KEYWORDS.md) setting keywords) can be combined with the action keywords. Examples:

```
San Francisco, CA tomorrow full --> returns a full wx report for location 'San Francisco' and date setting 'tomorrow'
satpass iss friday morning --> returns the first pass of the ISS on Friday morning
riseset thursday --> returns sunrise/sunset and moonrise / moonset values for Thursday.
```

If an [action keyword](ACTION_KEYWORDS.md) does not support daytime information (e.g. ```repeater```, ```riseset``` etc.), the daytime keyword information will be ignored.
