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

- ```tonight```,```tonite```, ```night``` or ```nite``` --> results in a ```today``` value

If you request the same weekday that is today, then the program assumes that you refer to that day in the next week.

Whereas noted for the respective [action keyword](action_commands.md), these date setting keywords (and also the [daytime](daytime_keywords.md) setting keywords) can be combined with the action keywords. Examples:

```
San Francisco, CA tomorrow full --> returns a full wx report for location 'San Francisco' and date setting 'tomorrow'
satpass iss friday morning --> returns the first pass of the ISS on Friday morning
riseset thursday --> returns sunrise/sunset and moonrise / moonset values for Thursday.
```
