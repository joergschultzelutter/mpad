# Date settings

MPAD is able to understand the following keywords:

- __today__ (Note: if not specified, this is the program default)

- __tomorrow__

- __monday__ or __mon__

- __tuesday__ or __tue__

- __wednesday__ or __wed__

- __thursday__ or __thu__

- __friday__ or __fri__

- __saturday__ or __sat__

- __sunday__ or __sun__

- __tonight__,__tonite__, __night__ or __nite__ --> results in a __today__ value

If you request the same weekday that is today, then the program assumes that you refer to that day in the next week.

Whereas noted for the respective [action keyword](01_actions.md), these date setting keywords (and also the [daytime](03_daytime_settings.md) setting keywords) can be combined with the action keywords. Examples:

```
San Francisco, CA tomorrow --> returns a wx report for location _San Francisco_ and date setting _tomorrow_
satpass iss fri --> returns the first pass of the ISS on Friday
riseset thursday --> returns sunrise/sunset and moonrise / moonset values for Thursday.
```
