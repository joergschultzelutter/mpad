# Daytime settings

MPAD is able to understand the following keywords:

- ```full```. Returns all data for the given day (__program default__). Note that ```full``` can refer to time frames or the amount of data that is returned by the program (dependent on the [action keyword](ACTION_KEYWORDS.md))

- Morning (Keywords: ```morn```, ```morning```)

- Daytime (Keywords: ```day```, ```daytime```, ```noon```)

- Evening (Keywords: ```eve```, ```evening```)

- Night (Keywords: ```nite```, ```night```, ```tonite```, ```tonight```). 
- 
```tonite``` and ```tonight``` keywords will set the ```date``` keyword to ```today``` unless the user has already specified a different day.

All references are to UTC time zone settings.

Whereas noted for the respective [action keyword](ACTION_KEYWORDS.md), these daytime setting keywords (and also the [date](DATE_KEYWORDS.md) setting keywords) can be combined with the action keywords. Examples:

```
San Francisco, CA tomorrow full --> returns a full wx report for location 'San Francisco' and date setting 'tomorrow'
satpass iss friday morning --> returns the first pass of the ISS on Friday morning
riseset thursday --> returns sunrise/sunset and moonrise / moonset values for Thursday.
```

If an [action keyword](ACTION_KEYWORDS.md) does not support daytime information (e.g. ```repeater```, ```riseset``` etc.), the daytime keyword information will be ignored.
