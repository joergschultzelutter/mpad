# Date settings

MPAD is able to understand the following keywords:

- ```today``` (Note: if not specified, this is the program default)

- ```tomorrow```

- ```monday``` or ```mon```

- ```tuesday``` or ```tue```

- ```wednesday``` or ```wed```

- ```thursday``` or ```thu```

- ```friday``` or ```fri```

- ```saturday``` or ```sat```

- ```sunday``` or ```sun```

- ```tonight```,```tonite``` --> results in date ```today``` and daytime ```night``` value

- ```1d``` ... ```7d``` results in 1...7 days in the future.

Additionally, you can specify an 'hour' keyword in order to receive hourly wx reports (other [action keywords](ACTION_KEYWORDS.md) may ignore these values). ```1h``` up until ```47h``` are permitted.

If you request the same weekday that is today, then the program assumes that you refer to that day in the next week.

Whereas noted for the respective [action keyword](ACTION_KEYWORDS.md), these date setting keywords (and also the [daytime](DAYTIME_KEYWORDS.md) setting keywords) can be combined with the action keywords. Examples:

```
San Francisco, CA tomorrow full --> returns a full wx report for location 'San Francisco' and date setting 'tomorrow'
riseset thursday --> returns sunrise/sunset and moonrise / moonset values for Thursday.
San Diego, CA 46h --> returns a report for location 'San Diego' for the wx in 46h 
Deensen;de 5d --> returns a report for location 'Deensen' in Germany for the wx in 5 days 
```
